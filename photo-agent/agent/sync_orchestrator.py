"""
同步流程编排模块

协调扫描、图像处理、索引上传、图片上传等流程。
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import __version__
from .api_client import ApiClient
from .config import Config
from .cos_uploader import CosUploader
from .database import Database, PhotoRecord
from .exif_reader import read_exif_safe
from .heartbeat import HeartbeatReporter
from .image_processor import generate_preview, generate_thumb
from .metrics import MetricsCollector
from .scanner import generate_local_photo_id, scan_directory

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """同步编排器"""
    
    def __init__(self, config: Config, db: Database):
        """
        初始化同步编排器
        
        Args:
            config: 配置
            db: 数据库
        """
        self.config = config
        self.db = db
        
        # 初始化组件
        self.api_client = ApiClient(
            server_url=config.server_url,
            agent_token=config.agent_token,
            agent_id=config.agent_id,
        )
        self.cos_uploader = CosUploader()
        self.heartbeat = HeartbeatReporter(
            api_client=self.api_client,
            db=db,
            interval_seconds=30,
        )
        self.metrics = MetricsCollector(db=db)
        
        # 并发控制
        self._thumb_semaphore = asyncio.Semaphore(config.thumb_upload_concurrency)
        self._preview_semaphore = asyncio.Semaphore(config.preview_upload_concurrency)
        
        # 状态控制
        self._running = False
        self._stop_event = asyncio.Event()
        self._active_tasks: set[asyncio.Task] = set()
    
    def stop(self):
        """停止同步"""
        logger.info("收到停止信号")
        self._running = False
        self._stop_event.set()
    
    async def wait_for_completion(self):
        """等待所有活跃任务完成"""
        if self._active_tasks:
            logger.info(f"等待 {len(self._active_tasks)} 个活跃任务完成...")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        logger.info("所有任务已完成")
    
    async def run(self):
        """运行同步流程"""
        logger.info(f"Photo Agent v{__version__} 启动")
        logger.info(f"Agent ID: {self.config.agent_id}")
        logger.info(f"照片根目录: {self.config.photo_root}")
        
        self._running = True
        
        # 启动心跳
        await self.heartbeat.start()
        
        try:
            # 启动时全量扫描
            await self._run_full_scan()
            
            # 增量扫描循环
            while self._running:
                # 等待扫描间隔或停止信号
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.config.scan_interval_minutes * 60
                    )
                    # 如果 stop_event 被设置，退出循环
                    break
                except asyncio.TimeoutError:
                    # 超时说明到了扫描时间
                    pass
                
                if not self._running:
                    break
                
                # 增量扫描
                await self._run_incremental_scan()
        
        except Exception as e:
            logger.error(f"同步流程异常: {e}", exc_info=True)
        
        finally:
            # 停止心跳
            await self.heartbeat.stop()
            
            # 关闭客户端
            await self.api_client.close()
            await self.cos_uploader.close()
            
            # 保存统计
            self.metrics.log_stats()
            
            logger.info("Photo Agent 已停止")
    
    async def _run_full_scan(self):
        """运行全量扫描"""
        logger.info("开始全量扫描...")
        self.heartbeat.set_status("scanning")
        self.metrics.start_sync_timer()
        
        try:
            # 扫描目录
            photos = scan_directory(self.config.photo_root)
            logger.info(f"扫描到 {len(photos)} 个图片文件")
            
            # 获取已存在的 local_photo_id
            existing_ids = self.db.get_all_local_photo_ids()
            
            # 处理每个照片
            new_count = 0
            for photo_info in photos:
                if not self._running:
                    break
                
                local_photo_id = generate_local_photo_id(
                    photo_info['relative_path'],
                    photo_info['file_size'],
                    photo_info['mtime']
                )
                
                # 检查是否已存在且未修改
                existing = self.db.get_photo_by_local_id(local_photo_id)
                if existing:
                    continue
                
                # 新照片，读取 EXIF 并保存
                await self._process_new_photo(photo_info, local_photo_id)
                new_count += 1
            
            logger.info(f"全量扫描完成，新增 {new_count} 张照片")
            self.heartbeat.set_last_scan_at()
            
            # 处理待同步照片
            await self._process_pending_photos()
            
        except Exception as e:
            logger.error(f"全量扫描失败: {e}", exc_info=True)
        
        finally:
            duration = self.metrics.stop_sync_timer()
            self.metrics.save_stats(duration)
            self.heartbeat.set_status("idle")
    
    async def _run_incremental_scan(self):
        """运行增量扫描"""
        logger.info("开始增量扫描...")
        self.heartbeat.set_status("scanning")
        self.metrics.start_sync_timer()
        
        try:
            # 扫描目录
            photos = scan_directory(self.config.photo_root)
            
            # 获取已存在的 local_photo_id
            existing_ids = self.db.get_all_local_photo_ids()
            
            # 查找新增照片
            new_count = 0
            for photo_info in photos:
                if not self._running:
                    break
                
                local_photo_id = generate_local_photo_id(
                    photo_info['relative_path'],
                    photo_info['file_size'],
                    photo_info['mtime']
                )
                
                # 检查是否已存在且未修改
                existing = self.db.get_photo_by_local_id(local_photo_id)
                if existing:
                    continue
                
                # 新照片
                await self._process_new_photo(photo_info, local_photo_id)
                new_count += 1
            
            logger.info(f"增量扫描完成，新增 {new_count} 张照片")
            self.heartbeat.set_last_scan_at()
            
            # 处理待同步照片
            await self._process_pending_photos()
            
        except Exception as e:
            logger.error(f"增量扫描失败: {e}", exc_info=True)
        
        finally:
            duration = self.metrics.stop_sync_timer()
            self.metrics.save_stats(duration)
            self.heartbeat.set_status("idle")
    
    async def _process_new_photo(self, photo_info: dict, local_photo_id: str):
        """
        处理新照片
        
        Args:
            photo_info: 照片信息
            local_photo_id: 本地照片 ID
        """
        try:
            # 读取 EXIF
            exif_data = read_exif_safe(photo_info['absolute_path'])
            
            # 生成 thumb 和 preview
            relative_path = photo_info['relative_path']
            thumb_relative = f".wandernote/thumbs/{relative_path}.webp"
            preview_relative = f".wandernote/previews/{relative_path}.webp"
            
            thumb_path = str(Path(self.config.photo_root) / thumb_relative)
            preview_path = str(Path(self.config.photo_root) / preview_relative)
            
            # 生成缩略图
            thumb_result = generate_thumb(
                photo_info['absolute_path'],
                thumb_path,
                self.config.thumb_long_edge
            )
            
            # 生成预览图
            preview_result = generate_preview(
                photo_info['absolute_path'],
                preview_path,
                self.config.preview_long_edge
            )
            
            # 创建照片记录
            photo = PhotoRecord(
                local_photo_id=local_photo_id,
                relative_path=relative_path,
                file_name=photo_info['file_name'],
                file_size=photo_info['file_size'],
                mtime=photo_info['mtime'],
                taken_at=exif_data.taken_at,
                lat=exif_data.lat,
                lng=exif_data.lng,
                width=exif_data.width,
                height=exif_data.height,
                thumb_path=thumb_relative if thumb_result else None,
                preview_path=preview_relative if preview_result else None,
                index_sync_status='pending',
                thumb_sync_status='pending' if thumb_result else 'failed',
                preview_sync_status='pending' if preview_result else 'failed',
            )
            
            # 保存到数据库
            self.db.upsert_photo(photo)
            
            logger.debug(f"处理新照片: {relative_path}")
        
        except Exception as e:
            logger.error(f"处理照片失败 {photo_info.get('relative_path', 'unknown')}: {e}")
    
    async def _process_pending_photos(self):
        """处理待同步照片"""
        logger.info("开始处理待同步照片...")
        self.heartbeat.set_status("uploading")
        
        try:
            # 分批处理
            while self._running:
                # 获取待同步照片
                pending_photos = self.db.get_pending_photos(limit=self.config.index_batch_size)
                
                if not pending_photos:
                    logger.info("没有待同步的照片")
                    break
                
                logger.info(f"处理 {len(pending_photos)} 张待同步照片")
                
                # 上传索引
                await self._upload_photo_indices(pending_photos)
                
                # 上传图片
                await self._upload_photo_assets(pending_photos)
                
                # 更新最后同步时间
                self.heartbeat.set_last_sync_at()
        
        except Exception as e:
            logger.error(f"处理待同步照片失败: {e}", exc_info=True)
        
        finally:
            self.heartbeat.set_status("idle")
    
    async def _upload_photo_indices(self, photos: list[PhotoRecord]):
        """
        上传照片索引
        
        Args:
            photos: 照片记录列表
        """
        # 构建上传数据
        upload_data = []
        for photo in photos:
            if photo.index_sync_status == 'synced':
                continue
            
            upload_data.append({
                "localPhotoId": photo.local_photo_id,
                "relativePath": photo.relative_path,
                "fileName": photo.file_name,
                "fileSize": photo.file_size,
                "contentHash": photo.content_hash,
                "mtime": datetime.fromtimestamp(photo.mtime, tz=timezone.utc).isoformat(),
                "takenAt": photo.taken_at,
                "lat": photo.lat,
                "lng": photo.lng,
                "width": photo.width,
                "height": photo.height,
                "hasGps": photo.lat is not None and photo.lng is not None,
            })
        
        if not upload_data:
            return
        
        # 批量上传
        result = await self.api_client.batch_upload_photos(upload_data)
        
        if not result:
            logger.error("批量上传照片索引失败")
            return
        
        # 处理响应
        results = result.get("results", [])
        for item in results:
            local_photo_id = item.get("localPhotoId")
            photo_id = item.get("photoId")
            
            if local_photo_id and photo_id:
                # 更新数据库
                self.db.update_photo_sync_status(
                    local_photo_id,
                    index_sync_status='synced',
                    server_photo_id=photo_id
                )
                
                # 如果需要上传图片，更新状态
                if item.get("needThumb"):
                    self.db.update_photo_sync_status(
                        local_photo_id,
                        thumb_sync_status='pending'
                    )
                if item.get("needPreview"):
                    self.db.update_photo_sync_status(
                        local_photo_id,
                        preview_sync_status='pending'
                    )
        
        logger.info(f"上传照片索引完成: {len(results)} 条")
    
    async def _upload_photo_assets(self, photos: list[PhotoRecord]):
        """
        上传照片资源（thumb/preview）
        
        Args:
            photos: 照片记录列表
        """
        # 筛选需要上传的照片
        need_thumb = [p for p in photos if p.thumb_sync_status == 'pending' and p.thumb_path and p.server_photo_id]
        need_preview = [p for p in photos if p.preview_sync_status == 'pending' and p.preview_path and p.server_photo_id]
        
        # 并发上传
        tasks = []
        
        for photo in need_thumb:
            task = asyncio.create_task(
                self._upload_single_asset(photo, 'thumb')
            )
            tasks.append(task)
        
        for photo in need_preview:
            task = asyncio.create_task(
                self._upload_single_asset(photo, 'preview')
            )
            tasks.append(task)
        
        if tasks:
            self.metrics.set_upload_queue_size(len(tasks))
            await asyncio.gather(*tasks, return_exceptions=True)
            self.metrics.set_upload_queue_size(0)
    
    async def _upload_single_asset(self, photo: PhotoRecord, asset_type: str):
        """
        上传单个资源
        
        Args:
            photo: 照片记录
            asset_type: 资源类型（thumb/preview）
        """
        # 获取信号量
        semaphore = self._thumb_semaphore if asset_type == 'thumb' else self._preview_semaphore
        
        async with semaphore:
            if not self._running:
                return
            
            try:
                # 获取资源路径
                if asset_type == 'thumb':
                    local_path = str(Path(self.config.photo_root) / photo.thumb_path)
                else:
                    local_path = str(Path(self.config.photo_root) / photo.preview_path)
                
                # 检查文件是否存在
                if not os.path.exists(local_path):
                    logger.warning(f"资源文件不存在: {local_path}")
                    return
                
                # 获取文件大小
                file_size = os.path.getsize(local_path)
                
                # 申请上传地址
                ticket = await self.api_client.get_upload_ticket(
                    photo_id=photo.server_photo_id,
                    asset_type=asset_type,
                    content_type="image/webp",
                    file_size=file_size,
                    width=photo.width or 0,
                    height=photo.height or 0,
                )
                
                if not ticket:
                    logger.error(f"申请上传地址失败: {photo.local_photo_id} {asset_type}")
                    self.metrics.record_upload_failure()
                    self.db.update_photo_sync_status(
                        photo.local_photo_id,
                        **{f"{asset_type}_sync_status": 'failed'},
                        last_error="申请上传地址失败"
                    )
                    return
                
                # 上传到 COS
                upload_url = ticket.get("uploadUrl")
                storage_key = ticket.get("storageKey")
                
                success = await self.cos_uploader.upload_with_retry(
                    upload_url=upload_url,
                    file_path=local_path,
                    content_type="image/webp",
                )
                
                if not success:
                    logger.error(f"上传到 COS 失败: {photo.local_photo_id} {asset_type}")
                    self.metrics.record_upload_failure()
                    self.db.update_photo_sync_status(
                        photo.local_photo_id,
                        **{f"{asset_type}_sync_status": 'failed'},
                        last_error="上传到 COS 失败"
                    )
                    return
                
                # 通知后端上传完成
                notify_success = await self.api_client.notify_upload_complete(
                    photo_id=photo.server_photo_id,
                    asset_type=asset_type,
                    storage_key=storage_key,
                    file_size=file_size,
                    width=photo.width or 0,
                    height=photo.height or 0,
                )
                
                if not notify_success:
                    logger.error(f"通知上传完成失败: {photo.local_photo_id} {asset_type}")
                    self.metrics.record_upload_failure()
                    self.db.update_photo_sync_status(
                        photo.local_photo_id,
                        **{f"{asset_type}_sync_status": 'failed'},
                        last_error="通知上传完成失败"
                    )
                    return
                
                # 上传成功
                self.metrics.record_upload_success()
                self.db.update_photo_sync_status(
                    photo.local_photo_id,
                    **{f"{asset_type}_sync_status": 'synced'}
                )
                
                logger.debug(f"上传成功: {photo.local_photo_id} {asset_type}")
            
            except Exception as e:
                logger.error(f"上传资源异常: {photo.local_photo_id} {asset_type} - {e}")
                self.metrics.record_upload_failure()
                self.db.update_photo_sync_status(
                    photo.local_photo_id,
                    **{f"{asset_type}_sync_status": 'failed'},
                    last_error=str(e)
                )

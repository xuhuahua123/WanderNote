"""
心跳上报模块

每 30 秒向后端上报 Agent 状态和同步统计。
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from . import __version__
from .api_client import ApiClient
from .database import Database

logger = logging.getLogger(__name__)


class HeartbeatReporter:
    """心跳上报器"""
    
    def __init__(
        self,
        api_client: ApiClient,
        db: Database,
        interval_seconds: int = 30
    ):
        """
        初始化心跳上报器
        
        Args:
            api_client: API 客户端
            db: 数据库
            interval_seconds: 心跳间隔（秒）
        """
        self.api_client = api_client
        self.db = db
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._status = "idle"
        self._last_scan_at: Optional[str] = None
        self._last_sync_at: Optional[str] = None
    
    def set_status(self, status: str):
        """
        设置 Agent 状态
        
        Args:
            status: 状态（idle/scanning/uploading）
        """
        self._status = status
    
    def set_last_scan_at(self, scan_time: Optional[str] = None):
        """
        设置最后扫描时间
        
        Args:
            scan_time: 扫描时间（ISO 格式），如果为 None 则使用当前时间
        """
        self._last_scan_at = scan_time or datetime.now().isoformat()
    
    def set_last_sync_at(self, sync_time: Optional[str] = None):
        """
        设置最后同步时间
        
        Args:
            sync_time: 同步时间（ISO 格式），如果为 None 则使用当前时间
        """
        self._last_sync_at = sync_time or datetime.now().isoformat()
    
    async def start(self):
        """启动心跳上报"""
        if self._running:
            logger.warning("心跳上报已在运行")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"心跳上报已启动，间隔 {self.interval_seconds} 秒")
    
    async def stop(self):
        """停止心跳上报"""
        self._running = False
        
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._task = None
        logger.info("心跳上报已停止")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                await self._send_heartbeat()
            except Exception as e:
                logger.error(f"心跳上报异常: {e}")
            
            # 等待下一次心跳
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
    
    async def _send_heartbeat(self):
        """发送心跳"""
        # 获取同步统计
        stats = self.db.get_sync_stats()
        
        # 构建心跳数据
        heartbeat_data = {
            "version": __version__,
            "status": self._status,
            "lastScanAt": self._last_scan_at,
            "lastSyncAt": self._last_sync_at,
            "photoCount": stats.photo_count,
            "gpsPhotoCount": stats.gps_photo_count,
            "thumbSyncedCount": stats.thumb_synced_count,
            "previewSyncedCount": stats.preview_synced_count,
            "failedCount": stats.failed_count,
        }
        
        # 发送心跳
        success = await self.api_client.heartbeat(heartbeat_data)
        
        if success:
            logger.debug("心跳上报成功")
        else:
            logger.warning("心跳上报失败")

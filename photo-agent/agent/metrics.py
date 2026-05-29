"""
轻量指标收集模块

本地记录并通过心跳上报的指标：
- photo_count: 照片总数
- gps_photo_count: 有 GPS 的照片数量
- thumb_synced_count: 已同步缩略图数量
- preview_synced_count: 已同步预览图数量
- failed_count: 失败数量
- upload_success_count: 上传成功次数
- upload_failed_count: 上传失败次数
- current_upload_queue_size: 当前上传队列大小
- last_sync_duration_seconds: 上次同步耗时
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from .database import Database, SyncStats

logger = logging.getLogger(__name__)


@dataclass
class MetricsCollector:
    """指标收集器"""
    
    db: Database
    
    # 计数器
    upload_success_count: int = 0
    upload_failed_count: int = 0
    current_upload_queue_size: int = 0
    
    # 时间跟踪
    _sync_start_time: Optional[float] = field(default=None, repr=False)
    
    def reset_upload_counters(self):
        """重置上传计数器"""
        self.upload_success_count = 0
        self.upload_failed_count = 0
        self.current_upload_queue_size = 0
    
    def start_sync_timer(self):
        """开始同步计时"""
        self._sync_start_time = time.time()
    
    def stop_sync_timer(self) -> float:
        """
        停止同步计时
        
        Returns:
            同步耗时（秒）
        """
        if self._sync_start_time is None:
            return 0.0
        
        duration = time.time() - self._sync_start_time
        self._sync_start_time = None
        return duration
    
    def record_upload_success(self):
        """记录上传成功"""
        self.upload_success_count += 1
    
    def record_upload_failure(self):
        """记录上传失败"""
        self.upload_failed_count += 1
    
    def set_upload_queue_size(self, size: int):
        """
        设置上传队列大小
        
        Args:
            size: 队列大小
        """
        self.current_upload_queue_size = size
    
    def save_stats(self, last_sync_duration: float = 0.0):
        """
        保存统计数据到数据库
        
        Args:
            last_sync_duration: 上次同步耗时（秒）
        """
        stats = self.db.get_sync_stats()
        
        stats.upload_success_count += self.upload_success_count
        stats.upload_failed_count += self.upload_failed_count
        stats.current_upload_queue_size = self.current_upload_queue_size
        stats.last_sync_duration_seconds = last_sync_duration
        
        self.db.update_sync_stats(stats)
        
        logger.debug(
            f"统计数据已保存: "
            f"上传成功={stats.upload_success_count}, "
            f"上传失败={stats.upload_failed_count}, "
            f"队列大小={stats.current_upload_queue_size}, "
            f"同步耗时={stats.last_sync_duration_seconds:.1f}s"
        )
    
    def get_stats_summary(self) -> dict:
        """
        获取统计摘要
        
        Returns:
            统计数据字典
        """
        stats = self.db.get_sync_stats()
        
        return {
            "photo_count": stats.photo_count,
            "gps_photo_count": stats.gps_photo_count,
            "thumb_synced_count": stats.thumb_synced_count,
            "preview_synced_count": stats.preview_synced_count,
            "failed_count": stats.failed_count,
            "upload_success_count": stats.upload_success_count,
            "upload_failed_count": stats.upload_failed_count,
            "current_upload_queue_size": stats.current_upload_queue_size,
            "last_sync_duration_seconds": stats.last_sync_duration_seconds,
        }
    
    def log_stats(self):
        """记录统计数据到日志"""
        stats = self.get_stats_summary()
        
        logger.info(
            f"同步统计: "
            f"照片总数={stats['photo_count']}, "
            f"GPS照片={stats['gps_photo_count']}, "
            f"缩略图已同步={stats['thumb_synced_count']}, "
            f"预览图已同步={stats['preview_synced_count']}, "
            f"失败={stats['failed_count']}, "
            f"上传成功={stats['upload_success_count']}, "
            f"上传失败={stats['upload_failed_count']}, "
            f"队列大小={stats['current_upload_queue_size']}, "
            f"同步耗时={stats['last_sync_duration_seconds']:.1f}s"
        )

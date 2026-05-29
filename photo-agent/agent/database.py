"""
SQLite 数据库操作模块

管理本地照片索引和同步状态。
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PhotoRecord:
    """照片记录"""
    id: Optional[int] = None
    local_photo_id: str = ""
    relative_path: str = ""
    file_name: str = ""
    file_size: int = 0
    mtime: float = 0.0
    content_hash: Optional[str] = None
    taken_at: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    thumb_path: Optional[str] = None
    preview_path: Optional[str] = None
    index_sync_status: str = "pending"
    thumb_sync_status: str = "pending"
    preview_sync_status: str = "pending"
    server_photo_id: Optional[str] = None
    last_error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class SyncStats:
    """同步统计"""
    id: Optional[int] = None
    photo_count: int = 0
    gps_photo_count: int = 0
    thumb_synced_count: int = 0
    preview_synced_count: int = 0
    failed_count: int = 0
    upload_success_count: int = 0
    upload_failed_count: int = 0
    current_upload_queue_size: int = 0
    last_sync_duration_seconds: float = 0.0
    updated_at: Optional[str] = None


class Database:
    """SQLite 数据库操作"""
    
    def __init__(self, db_path: str = "data/agent.sqlite3"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建 photos 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_photo_id TEXT NOT NULL UNIQUE,
                    relative_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    content_hash TEXT,
                    taken_at TEXT,
                    lat REAL,
                    lng REAL,
                    width INTEGER,
                    height INTEGER,
                    thumb_path TEXT,
                    preview_path TEXT,
                    index_sync_status TEXT DEFAULT 'pending',
                    thumb_sync_status TEXT DEFAULT 'pending',
                    preview_sync_status TEXT DEFAULT 'pending',
                    server_photo_id TEXT,
                    last_error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_photos_sync 
                ON photos(index_sync_status, thumb_sync_status, preview_sync_status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_photos_local_id 
                ON photos(local_photo_id)
            """)
            
            # 创建 sync_stats 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    photo_count INTEGER DEFAULT 0,
                    gps_photo_count INTEGER DEFAULT 0,
                    thumb_synced_count INTEGER DEFAULT 0,
                    preview_synced_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    upload_success_count INTEGER DEFAULT 0,
                    upload_failed_count INTEGER DEFAULT 0,
                    current_upload_queue_size INTEGER DEFAULT 0,
                    last_sync_duration_seconds REAL DEFAULT 0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_photo_by_local_id(self, local_photo_id: str) -> Optional[PhotoRecord]:
        """根据 local_photo_id 获取照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM photos WHERE local_photo_id = ?", (local_photo_id,))
            row = cursor.fetchone()
            if row:
                return PhotoRecord(**dict(row))
            return None
    
    def get_photo_by_path(self, relative_path: str) -> Optional[PhotoRecord]:
        """根据相对路径获取照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM photos WHERE relative_path = ?", (relative_path,))
            row = cursor.fetchone()
            if row:
                return PhotoRecord(**dict(row))
            return None
    
    def upsert_photo(self, photo: PhotoRecord) -> PhotoRecord:
        """插入或更新照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 在同一连接内检查是否已存在
            cursor.execute("SELECT * FROM photos WHERE local_photo_id = ?", (photo.local_photo_id,))
            row = cursor.fetchone()
            existing = PhotoRecord(**dict(row)) if row else None
            
            if existing:
                # 更新现有记录
                cursor.execute("""
                    UPDATE photos SET
                        relative_path = ?,
                        file_name = ?,
                        file_size = ?,
                        mtime = ?,
                        content_hash = ?,
                        taken_at = ?,
                        lat = ?,
                        lng = ?,
                        width = ?,
                        height = ?,
                        thumb_path = ?,
                        preview_path = ?,
                        index_sync_status = ?,
                        thumb_sync_status = ?,
                        preview_sync_status = ?,
                        server_photo_id = ?,
                        last_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE local_photo_id = ?
                """, (
                    photo.relative_path,
                    photo.file_name,
                    photo.file_size,
                    photo.mtime,
                    photo.content_hash,
                    photo.taken_at,
                    photo.lat,
                    photo.lng,
                    photo.width,
                    photo.height,
                    photo.thumb_path,
                    photo.preview_path,
                    photo.index_sync_status,
                    photo.thumb_sync_status,
                    photo.preview_sync_status,
                    photo.server_photo_id,
                    photo.last_error,
                    photo.local_photo_id,
                ))
                conn.commit()
                return self.get_photo_by_local_id(photo.local_photo_id)
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO photos (
                        local_photo_id, relative_path, file_name, file_size, mtime,
                        content_hash, taken_at, lat, lng, width, height,
                        thumb_path, preview_path,
                        index_sync_status, thumb_sync_status, preview_sync_status,
                        server_photo_id, last_error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    photo.local_photo_id,
                    photo.relative_path,
                    photo.file_name,
                    photo.file_size,
                    photo.mtime,
                    photo.content_hash,
                    photo.taken_at,
                    photo.lat,
                    photo.lng,
                    photo.width,
                    photo.height,
                    photo.thumb_path,
                    photo.preview_path,
                    photo.index_sync_status,
                    photo.thumb_sync_status,
                    photo.preview_sync_status,
                    photo.server_photo_id,
                    photo.last_error,
                ))
                conn.commit()
                return self.get_photo_by_local_id(photo.local_photo_id)
    
    def get_pending_photos(self, limit: int = 100) -> list[PhotoRecord]:
        """获取待同步的照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM photos 
                WHERE index_sync_status = 'pending' 
                   OR thumb_sync_status = 'pending' 
                   OR preview_sync_status = 'pending'
                ORDER BY id
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [PhotoRecord(**dict(row)) for row in rows]
    
    def get_failed_photos(self, limit: int = 100) -> list[PhotoRecord]:
        """获取同步失败的照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM photos 
                WHERE index_sync_status = 'failed' 
                   OR thumb_sync_status = 'failed' 
                   OR preview_sync_status = 'failed'
                ORDER BY id
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [PhotoRecord(**dict(row)) for row in rows]
    
    def update_photo_sync_status(
        self,
        local_photo_id: str,
        index_sync_status: Optional[str] = None,
        thumb_sync_status: Optional[str] = None,
        preview_sync_status: Optional[str] = None,
        server_photo_id: Optional[str] = None,
        last_error: Optional[str] = None,
    ):
        """更新照片同步状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if index_sync_status is not None:
                updates.append("index_sync_status = ?")
                params.append(index_sync_status)
            
            if thumb_sync_status is not None:
                updates.append("thumb_sync_status = ?")
                params.append(thumb_sync_status)
            
            if preview_sync_status is not None:
                updates.append("preview_sync_status = ?")
                params.append(preview_sync_status)
            
            if server_photo_id is not None:
                updates.append("server_photo_id = ?")
                params.append(server_photo_id)
            
            if last_error is not None:
                updates.append("last_error = ?")
                params.append(last_error)
            
            if not updates:
                return
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(local_photo_id)
            
            sql = f"UPDATE photos SET {', '.join(updates)} WHERE local_photo_id = ?"
            cursor.execute(sql, params)
            conn.commit()
    
    def get_sync_stats(self) -> SyncStats:
        """获取同步统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取照片统计
            cursor.execute("SELECT COUNT(*) as count FROM photos")
            photo_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM photos WHERE lat IS NOT NULL AND lng IS NOT NULL")
            gps_photo_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM photos WHERE thumb_sync_status = 'synced'")
            thumb_synced_count = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM photos WHERE preview_sync_status = 'synced'")
            preview_synced_count = cursor.fetchone()["count"]
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM photos 
                WHERE index_sync_status = 'failed' 
                   OR thumb_sync_status = 'failed' 
                   OR preview_sync_status = 'failed'
            """)
            failed_count = cursor.fetchone()["count"]
            
            # 获取上传统计
            cursor.execute("SELECT * FROM sync_stats ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                stats = SyncStats(**dict(row))
                stats.photo_count = photo_count
                stats.gps_photo_count = gps_photo_count
                stats.thumb_synced_count = thumb_synced_count
                stats.preview_synced_count = preview_synced_count
                stats.failed_count = failed_count
                return stats
            else:
                return SyncStats(
                    photo_count=photo_count,
                    gps_photo_count=gps_photo_count,
                    thumb_synced_count=thumb_synced_count,
                    preview_synced_count=preview_synced_count,
                    failed_count=failed_count,
                )
    
    def update_sync_stats(self, stats: SyncStats):
        """更新同步统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已有记录
            cursor.execute("SELECT id FROM sync_stats LIMIT 1")
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE sync_stats SET
                        photo_count = ?,
                        gps_photo_count = ?,
                        thumb_synced_count = ?,
                        preview_synced_count = ?,
                        failed_count = ?,
                        upload_success_count = ?,
                        upload_failed_count = ?,
                        current_upload_queue_size = ?,
                        last_sync_duration_seconds = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    stats.photo_count,
                    stats.gps_photo_count,
                    stats.thumb_synced_count,
                    stats.preview_synced_count,
                    stats.failed_count,
                    stats.upload_success_count,
                    stats.upload_failed_count,
                    stats.current_upload_queue_size,
                    stats.last_sync_duration_seconds,
                    existing["id"],
                ))
            else:
                cursor.execute("""
                    INSERT INTO sync_stats (
                        photo_count, gps_photo_count, thumb_synced_count, preview_synced_count,
                        failed_count, upload_success_count, upload_failed_count,
                        current_upload_queue_size, last_sync_duration_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats.photo_count,
                    stats.gps_photo_count,
                    stats.thumb_synced_count,
                    stats.preview_synced_count,
                    stats.failed_count,
                    stats.upload_success_count,
                    stats.upload_failed_count,
                    stats.current_upload_queue_size,
                    stats.last_sync_duration_seconds,
                ))
            
            conn.commit()
    
    def get_all_local_photo_ids(self) -> set[str]:
        """获取所有本地照片 ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT local_photo_id FROM photos")
            rows = cursor.fetchall()
            return {row["local_photo_id"] for row in rows}
    
    def delete_photo_by_local_id(self, local_photo_id: str):
        """删除照片记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM photos WHERE local_photo_id = ?", (local_photo_id,))
            conn.commit()

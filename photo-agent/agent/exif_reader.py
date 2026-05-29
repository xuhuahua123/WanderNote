"""
EXIF 数据提取模块

提取照片的拍摄时间、GPS 坐标和图片尺寸。
支持 JPG、PNG、HEIC 格式。
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import exifread
from PIL import Image

# 尝试导入 pillow-heif 以支持 HEIC
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

logger = logging.getLogger(__name__)


@dataclass
class ExifData:
    """EXIF 数据"""
    taken_at: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


def _convert_gps_coordinate(value, ref) -> Optional[float]:
    """
    转换 GPS 坐标为十进制度数
    
    Args:
        value: GPS 坐标值（度、分、秒）
        ref: 方向参考（N/S/E/W）
    
    Returns:
        十进制度数
    """
    try:
        # 提取度、分、秒
        degrees = float(value.values[0].num) / float(value.values[0].den)
        minutes = float(value.values[1].num) / float(value.values[1].den)
        seconds = float(value.values[2].num) / float(value.values[2].den)
        
        # 转换为十进制度
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        # 根据方向调整符号
        if ref in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    except (AttributeError, ZeroDivisionError, IndexError) as e:
        logger.debug(f"GPS 坐标转换失败: {e}")
        return None


def _parse_taken_at(date_str: str) -> Optional[str]:
    """
    解析拍摄时间字符串
    
    Args:
        date_str: EXIF 日期字符串（格式：YYYY:MM:DD HH:MM:SS）
    
    Returns:
        ISO 8601 格式日期字符串
    """
    try:
        # EXIF 日期格式：YYYY:MM:DD HH:MM:SS
        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return dt.isoformat()
    except ValueError as e:
        logger.debug(f"日期解析失败: {e}")
        return None


def read_exif(file_path: str) -> Optional[ExifData]:
    """
    读取照片 EXIF 数据
    
    Args:
        file_path: 照片文件路径
    
    Returns:
        ExifData 对象，如果读取失败返回 None
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return None
    
    try:
        # 使用 Pillow 获取图片尺寸
        with Image.open(file_path) as img:
            width, height = img.size
        
        # 使用 exifread 读取 EXIF 数据
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        # 提取拍摄时间
        taken_at = None
        for tag_name in ['EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime']:
            if tag_name in tags:
                taken_at = _parse_taken_at(str(tags[tag_name]))
                if taken_at:
                    break
        
        # 提取 GPS 坐标
        lat = None
        lng = None
        
        if 'GPS GPSLatitude' in tags and 'GPS GPSLatitudeRef' in tags:
            lat = _convert_gps_coordinate(
                tags['GPS GPSLatitude'],
                str(tags['GPS GPSLatitudeRef'])
            )
        
        if 'GPS GPSLongitude' in tags and 'GPS GPSLongitudeRef' in tags:
            lng = _convert_gps_coordinate(
                tags['GPS GPSLongitude'],
                str(tags['GPS GPSLongitudeRef'])
            )
        
        return ExifData(
            taken_at=taken_at,
            lat=lat,
            lng=lng,
            width=width,
            height=height,
        )
    
    except Exception as e:
        logger.warning(f"读取 EXIF 失败 {file_path}: {e}")
        # 尝试仅获取图片尺寸
        try:
            with Image.open(file_path) as img:
                width, height = img.size
            return ExifData(width=width, height=height)
        except Exception as e2:
            logger.error(f"读取图片尺寸失败 {file_path}: {e2}")
            return None


def read_exif_safe(file_path: str) -> ExifData:
    """
    安全读取 EXIF 数据，不会抛出异常
    
    Args:
        file_path: 照片文件路径
    
    Returns:
        ExifData 对象（可能部分字段为 None）
    """
    result = read_exif(file_path)
    if result is None:
        return ExifData()
    return result

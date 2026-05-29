"""
目录扫描模块

扫描照片目录，发现新增和修改的照片文件。
忽略 .wandernote 目录。
"""

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

# 支持的图片格式
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic'}

# 忽略的目录
IGNORED_DIRS = {'.wandernote', '.git', '.svn', '__pycache__', 'node_modules'}


@dataclass
class ScanResult:
    """扫描结果"""
    new_photos: list[str]      # 新发现的照片路径列表
    modified_photos: list[str]  # 修改过的照片路径列表
    deleted_photos: list[str]   # 已删除的照片路径列表
    total_scanned: int          # 扫描到的文件总数


def generate_local_photo_id(relative_path: str, file_size: int, mtime: float) -> str:
    """
    生成本地照片 ID
    
    使用 SHA256(relative_path + file_size + mtime) 生成唯一标识。
    relative_path 统一使用正斜杠 / 作为路径分隔符。
    
    Args:
        relative_path: 相对路径（使用正斜杠）
        file_size: 文件大小（字节）
        mtime: 文件修改时间戳
    
    Returns:
        SHA256 哈希字符串
    """
    # 确保 relative_path 使用正斜杠
    normalized_path = relative_path.replace('\\', '/')
    
    # 组合输入字符串
    input_str = f"{normalized_path}{file_size}{mtime}"
    
    # 计算 SHA256
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()


def _should_ignore_dir(dir_name: str) -> bool:
    """判断是否应该忽略目录"""
    return dir_name in IGNORED_DIRS or dir_name.startswith('.')


def _is_supported_file(file_path: Path) -> bool:
    """判断是否是支持的图片文件"""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def scan_directory(photo_root: str) -> list[dict]:
    """
    扫描目录，返回所有支持的图片文件信息
    
    Args:
        photo_root: 照片根目录
    
    Returns:
        文件信息列表，每个元素包含：
        - absolute_path: 绝对路径
        - relative_path: 相对路径（使用正斜杠）
        - file_name: 文件名
        - file_size: 文件大小
        - mtime: 修改时间
    """
    root = Path(photo_root)
    
    if not root.exists():
        logger.error(f"照片根目录不存在: {photo_root}")
        return []
    
    if not root.is_dir():
        logger.error(f"照片根目录不是目录: {photo_root}")
        return []
    
    photos = []
    
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            # 过滤忽略的目录（就地修改 dirnames 以阻止 os.walk 进入）
            dirnames[:] = [d for d in dirnames if not _should_ignore_dir(d)]
            
            for filename in filenames:
                file_path = Path(dirpath) / filename
                
                # 检查文件扩展名
                if not _is_supported_file(file_path):
                    continue
                
                try:
                    # 获取文件信息
                    stat = file_path.stat()
                    
                    # 计算相对路径
                    relative_path = file_path.relative_to(root)
                    # 统一使用正斜杠
                    relative_path_str = str(relative_path).replace('\\', '/')
                    
                    photos.append({
                        'absolute_path': str(file_path),
                        'relative_path': relative_path_str,
                        'file_name': filename,
                        'file_size': stat.st_size,
                        'mtime': stat.st_mtime,
                    })
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法读取文件信息 {file_path}: {e}")
                    continue
    
    except (OSError, PermissionError) as e:
        logger.error(f"扫描目录失败 {photo_root}: {e}")
    
    logger.info(f"扫描完成，发现 {len(photos)} 个图片文件")
    return photos


def find_new_and_modified_photos(
    photo_root: str,
    existing_local_ids: Set[str]
) -> ScanResult:
    """
    查找新增和修改的照片
    
    Args:
        photo_root: 照片根目录
        existing_local_ids: 已存在的 local_photo_id 集合
    
    Returns:
        ScanResult 对象
    """
    # 扫描目录
    all_photos = scan_directory(photo_root)
    
    new_photos = []
    modified_photos = []
    current_local_ids = set()
    
    for photo in all_photos:
        # 生成 local_photo_id
        local_photo_id = generate_local_photo_id(
            photo['relative_path'],
            photo['file_size'],
            photo['mtime']
        )
        
        current_local_ids.add(local_photo_id)
        
        # 判断是新增还是修改
        if local_photo_id not in existing_local_ids:
            # 检查是否是同一路径但不同版本（修改）
            # 这里简单地认为所有不在 existing_local_ids 中的都是新增
            # 实际的修改检测在 database 层通过 relative_path 判断
            new_photos.append(photo['absolute_path'])
    
    # 查找已删除的照片
    deleted_photos = []
    # 注意：这里需要从数据库获取已删除照片的路径
    # 实际实现在 sync_orchestrator 中处理
    
    return ScanResult(
        new_photos=new_photos,
        modified_photos=modified_photos,
        deleted_photos=deleted_photos,
        total_scanned=len(all_photos)
    )


def get_photo_info(photo_root: str, absolute_path: str) -> Optional[dict]:
    """
    获取单个照片的详细信息
    
    Args:
        photo_root: 照片根目录
        absolute_path: 照片绝对路径
    
    Returns:
        照片信息字典，如果失败返回 None
    """
    file_path = Path(absolute_path)
    root = Path(photo_root)
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {absolute_path}")
        return None
    
    try:
        stat = file_path.stat()
        relative_path = file_path.relative_to(root)
        relative_path_str = str(relative_path).replace('\\', '/')
        
        return {
            'absolute_path': str(file_path),
            'relative_path': relative_path_str,
            'file_name': file_path.name,
            'file_size': stat.st_size,
            'mtime': stat.st_mtime,
        }
    except (OSError, PermissionError) as e:
        logger.warning(f"无法读取文件信息 {absolute_path}: {e}")
        return None

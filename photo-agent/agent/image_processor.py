"""
图像处理模块

生成 thumb（长边 360px）和 preview（长边 1280px）的 WebP 图片。
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


def calculate_resize_dimensions(
    width: int,
    height: int,
    target_long_edge: int
) -> Tuple[int, int]:
    """
    计算缩放后的尺寸
    
    Args:
        width: 原图宽度
        height: 原图高度
        target_long_edge: 目标长边尺寸
    
    Returns:
        (new_width, new_height)
    """
    if width <= 0 or height <= 0:
        return width, height
    
    # 如果图片已经小于目标尺寸，不缩放
    if max(width, height) <= target_long_edge:
        return width, height
    
    # 计算缩放比例
    if width >= height:
        # 横向图片，宽度为长边
        scale = target_long_edge / width
    else:
        # 纵向图片，高度为长边
        scale = target_long_edge / height
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # 确保至少为 1 像素
    new_width = max(1, new_width)
    new_height = max(1, new_height)
    
    return new_width, new_height


def generate_thumb(
    source_path: str,
    output_path: str,
    long_edge: int = 360,
    quality: int = 85
) -> Optional[str]:
    """
    生成缩略图
    
    Args:
        source_path: 源文件路径
        output_path: 输出文件路径
        long_edge: 长边尺寸（默认 360px）
        quality: WebP 质量（默认 85）
    
    Returns:
        输出文件路径，如果失败返回 None
    """
    return _resize_and_save(source_path, output_path, long_edge, quality)


def generate_preview(
    source_path: str,
    output_path: str,
    long_edge: int = 1280,
    quality: int = 85
) -> Optional[str]:
    """
    生成预览图
    
    Args:
        source_path: 源文件路径
        output_path: 输出文件路径
        long_edge: 长边尺寸（默认 1280px）
        quality: WebP 质量（默认 85）
    
    Returns:
        输出文件路径，如果失败返回 None
    """
    return _resize_and_save(source_path, output_path, long_edge, quality)


def _resize_and_save(
    source_path: str,
    output_path: str,
    target_long_edge: int,
    quality: int = 85
) -> Optional[str]:
    """
    缩放并保存图片
    
    Args:
        source_path: 源文件路径
        output_path: 输出文件路径
        target_long_edge: 目标长边尺寸
        quality: WebP 质量
    
    Returns:
        输出文件路径，如果失败返回 None
    """
    source = Path(source_path)
    output = Path(output_path)
    
    if not source.exists():
        logger.error(f"源文件不存在: {source_path}")
        return None
    
    try:
        # 创建输出目录
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # 打开图片
        with Image.open(source_path) as img:
            # 转换为 RGB（如果是 RGBA 或其他模式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 获取原始尺寸
            width, height = img.size
            
            # 计算缩放尺寸
            new_width, new_height = calculate_resize_dimensions(
                width, height, target_long_edge
            )
            
            # 缩放图片
            if (new_width, new_height) != (width, height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存为 WebP
            img.save(output, 'WEBP', quality=quality)
            
            logger.debug(
                f"生成图片: {source_path} -> {output_path} "
                f"({width}x{height} -> {new_width}x{new_height})"
            )
            
            return str(output)
    
    except Exception as e:
        logger.error(f"生成图片失败 {source_path}: {e}")
        return None


def get_image_dimensions(file_path: str) -> Optional[Tuple[int, int]]:
    """
    获取图片尺寸
    
    Args:
        file_path: 图片文件路径
    
    Returns:
        (width, height) 或 None
    """
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception as e:
        logger.warning(f"获取图片尺寸失败 {file_path}: {e}")
        return None

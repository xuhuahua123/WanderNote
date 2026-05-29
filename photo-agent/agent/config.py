"""
配置加载模块

配置优先级：环境变量 > config.yaml > 默认值
环境变量映射：
  AGENT_TOKEN -> agent_token
  PHOTO_ROOT -> photo_root
  SERVER_URL -> server_url
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    """Agent 配置"""
    
    agent_id: str
    server_url: str
    agent_token: str
    photo_root: str
    scan_interval_minutes: int = 10
    thumb_long_edge: int = 360
    preview_long_edge: int = 1280
    index_batch_size: int = 100
    thumb_upload_concurrency: int = 3
    preview_upload_concurrency: int = 1
    log_level: str = "INFO"
    
    def validate(self) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        if not self.agent_id:
            errors.append("agent_id 不能为空")
        
        if not self.server_url:
            errors.append("server_url 不能为空")
        
        if not self.agent_token:
            errors.append("agent_token 不能为空（设置环境变量 AGENT_TOKEN 或在 config.yaml 中配置）")
        
        if not self.photo_root:
            errors.append("photo_root 不能为空")
        elif not Path(self.photo_root).exists():
            errors.append(f"photo_root 目录不存在: {self.photo_root}")
        
        if self.scan_interval_minutes < 1:
            errors.append("scan_interval_minutes 必须大于 0")
        
        if self.thumb_long_edge < 1:
            errors.append("thumb_long_edge 必须大于 0")
        
        if self.preview_long_edge < 1:
            errors.append("preview_long_edge 必须大于 0")
        
        if self.index_batch_size < 1:
            errors.append("index_batch_size 必须大于 0")
        
        if self.thumb_upload_concurrency < 1:
            errors.append("thumb_upload_concurrency 必须大于 0")
        
        if self.preview_upload_concurrency < 1:
            errors.append("preview_upload_concurrency 必须大于 0")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level 必须是 {valid_log_levels} 之一")
        
        return errors


def _get_config_path() -> Path:
    """获取配置文件路径"""
    # 优先查找当前目录
    config_path = Path("config.yaml")
    if config_path.exists():
        return config_path
    
    # 其次查找 agent 目录
    config_path = Path("agent/config.yaml")
    if config_path.exists():
        return config_path
    
    # 最后查找上级目录
    config_path = Path("../config.yaml")
    if config_path.exists():
        return config_path
    
    return Path("config.yaml")


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置
    
    Args:
        config_path: 配置文件路径，如果为 None 则自动查找
    
    Returns:
        Config 对象
    
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置验证失败
    """
    # 确定配置文件路径
    if config_path:
        path = Path(config_path)
    else:
        path = _get_config_path()
    
    # 读取 YAML 配置
    yaml_config = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
    else:
        print(f"警告: 配置文件不存在: {path}")
        print("将使用环境变量和默认值")
    
    # 环境变量覆盖
    agent_token = os.environ.get("AGENT_TOKEN", yaml_config.get("agent_token", ""))
    photo_root = os.environ.get("PHOTO_ROOT", yaml_config.get("photo_root", ""))
    server_url = os.environ.get("SERVER_URL", yaml_config.get("server_url", ""))
    agent_id = yaml_config.get("agent_id", "")
    
    # 创建配置对象
    config = Config(
        agent_id=agent_id,
        server_url=server_url,
        agent_token=agent_token,
        photo_root=photo_root,
        scan_interval_minutes=yaml_config.get("scan_interval_minutes", 10),
        thumb_long_edge=yaml_config.get("thumb_long_edge", 360),
        preview_long_edge=yaml_config.get("preview_long_edge", 1280),
        index_batch_size=yaml_config.get("index_batch_size", 100),
        thumb_upload_concurrency=yaml_config.get("thumb_upload_concurrency", 3),
        preview_upload_concurrency=yaml_config.get("preview_upload_concurrency", 1),
        log_level=yaml_config.get("log_level", "INFO"),
    )
    
    # 验证配置
    errors = config.validate()
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError("配置验证失败")
    
    return config


def load_config_or_exit(config_path: Optional[str] = None) -> Config:
    """
    加载配置，失败时退出程序
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        Config 对象
    """
    try:
        return load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}")
        sys.exit(1)

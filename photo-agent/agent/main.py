"""
Photo-Agent 入口点

负责：
- 命令行参数解析
- 日志配置
- 信号处理（优雅关闭）
- 启动同步流程
"""

import asyncio
import logging
import signal
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import __version__
from .config import load_config_or_exit
from .database import Database
from .sync_orchestrator import SyncOrchestrator


def setup_logging(log_level: str = "INFO", log_file: str = "logs/agent.log"):
    """
    配置日志
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)


def main():
    """主入口点"""
    print(f"WanderNote Photo Agent v{__version__}")
    print("=" * 50)
    
    # 加载配置
    config = load_config_or_exit()
    
    # 配置日志
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Agent ID: {config.agent_id}")
    logger.info(f"Server URL: {config.server_url}")
    logger.info(f"Photo Root: {config.photo_root}")
    logger.info(f"Scan Interval: {config.scan_interval_minutes} minutes")
    
    # 初始化数据库
    db = Database()
    logger.info("数据库初始化完成")
    
    # 创建同步编排器
    orchestrator = SyncOrchestrator(config, db)
    
    # 信号处理：设置停止事件，让 run() 循环自然退出
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，开始优雅关闭...")
        orchestrator.stop()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行同步流程（run() 内部会检查 _stop_event 并优雅退出）
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出")
    except Exception as e:
        logger.error(f"运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

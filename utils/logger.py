"""
日志配置模块
统一管理系统日志输出
"""

import sys
from loguru import logger
from .config import settings

def setup_logging():
    """配置日志系统"""
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 文件输出
    logger.add(
        settings.data_path / "logs" / "app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    # Agent专用日志
    logger.add(
        settings.data_path / "logs" / "agents.log",
        level="INFO", 
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[agent_name]} | {message}",
        filter=lambda record: "agent_name" in record["extra"],
        rotation="5 MB",
        retention="3 days"
    )
    
    # 质量评估日志
    logger.add(
        settings.data_path / "logs" / "quality.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: record["extra"].get("log_type") == "quality",
        retention="30 days"
    )

# 创建日志目录
(settings.data_path / "logs").mkdir(parents=True, exist_ok=True)

# 初始化日志系统
setup_logging()

# 为各个Agent创建专用logger
def get_agent_logger(agent_name: str):
    """获取Agent专用logger"""
    return logger.bind(agent_name=agent_name)

def get_quality_logger():
    """获取质量评估logger"""
    return logger.bind(log_type="quality")
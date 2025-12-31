"""
日志记录模块

提供统一的日志记录功能
"""

import os
import logging
from datetime import datetime
from pathlib import Path


class GomokuLogger:
    """
    五子棋游戏日志记录器
    
    将日志写入文件，不影响终端显示
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if GomokuLogger._initialized:
            return
        
        GomokuLogger._initialized = True
        
        # 创建日志目录
        log_dir = Path.home() / ".gomoku" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        log_file = log_dir / f"gomoku_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置日志
        self.logger = logging.getLogger("gomoku")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            # 文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)
    
    def exception(self, message: str):
        """记录异常信息（包含堆栈）"""
        self.logger.exception(message)


# 全局日志实例
logger = GomokuLogger()


def get_logger() -> GomokuLogger:
    """获取日志记录器实例"""
    return logger

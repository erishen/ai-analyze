"""
统一日志系统
支持分级日志、文件日志、控制台日志分离
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys


class LoggerConfig:
    """日志配置"""
    
    # 日志级别
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    # 日志格式
    CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    
    # 日志目录
    LOG_DIR = Path(__file__).parent.parent / "logs"
    
    # 日志文件
    LOG_FILE = LOG_DIR / "ai-analyze.log"
    ERROR_LOG_FILE = LOG_DIR / "ai-analyze.error.log"


class UnifiedLogger:
    """统一日志管理器"""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        LoggerConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 创建根日志记录器
        self.root_logger = logging.getLogger("ai-analyze")
        self.root_logger.setLevel(LoggerConfig.DEBUG)
        
        # 清除已有的处理器
        self.root_logger.handlers.clear()
        
        # 控制台处理器（INFO 及以上）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LoggerConfig.INFO)
        console_formatter = logging.Formatter(LoggerConfig.CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        self.root_logger.addHandler(console_handler)
        
        # 文件处理器（DEBUG 及以上）
        file_handler = logging.handlers.RotatingFileHandler(
            LoggerConfig.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(LoggerConfig.DEBUG)
        file_formatter = logging.Formatter(LoggerConfig.FILE_FORMAT)
        file_handler.setFormatter(file_formatter)
        self.root_logger.addHandler(file_handler)
        
        # 错误文件处理器（ERROR 及以上）
        error_handler = logging.handlers.RotatingFileHandler(
            LoggerConfig.ERROR_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(LoggerConfig.ERROR)
        error_formatter = logging.Formatter(LoggerConfig.FILE_FORMAT)
        error_handler.setFormatter(error_formatter)
        self.root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取或创建日志记录器"""
        if name not in self._loggers:
            logger = logging.getLogger(f"ai-analyze.{name}")
            logger.setLevel(LoggerConfig.DEBUG)
            self._loggers[name] = logger
        return self._loggers[name]
    
    def set_level(self, level: int):
        """设置日志级别"""
        self.root_logger.setLevel(level)
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
    
    def get_log_file(self) -> Path:
        """获取日志文件路径"""
        return LoggerConfig.LOG_FILE
    
    def get_error_log_file(self) -> Path:
        """获取错误日志文件路径"""
        return LoggerConfig.ERROR_LOG_FILE


# 全局日志管理器实例
_logger_manager = UnifiedLogger()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用模块名）
    
    Returns:
        logging.Logger: 日志记录器实例
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
        >>> logger.error("This is an error message")
    """
    return _logger_manager.get_logger(name)


def set_log_level(level: int):
    """设置全局日志级别
    
    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    
    Example:
        >>> set_log_level(logging.DEBUG)
    """
    _logger_manager.set_level(level)


def get_log_file() -> Path:
    """获取日志文件路径"""
    return _logger_manager.get_log_file()


def get_error_log_file() -> Path:
    """获取错误日志文件路径"""
    return _logger_manager.get_error_log_file()


# 便捷函数
def debug(msg: str, *args, **kwargs):
    """记录 DEBUG 级别日志"""
    _logger_manager.root_logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录 INFO 级别日志"""
    _logger_manager.root_logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录 WARNING 级别日志"""
    _logger_manager.root_logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录 ERROR 级别日志"""
    _logger_manager.root_logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录 CRITICAL 级别日志"""
    _logger_manager.root_logger.critical(msg, *args, **kwargs)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\n📄 日志文件: {get_log_file()}")
    print(f"📄 错误日志: {get_error_log_file()}")

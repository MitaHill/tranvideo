"""
统一日志输出格式工具模块

提供统一格式的日志输出：[模块名称][时间戳][日志信息]

作者：Claude Code  
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


class StandardizedLogger:
    """标准化日志器类"""
    
    def __init__(self, module_name: str, log_dir: str = 'log'):
        """
        初始化标准化日志器
        
        Args:
            module_name: 模块名称，用于日志前缀
            log_dir: 日志文件目录
        """
        self.module_name = module_name
        self.log_dir = log_dir
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(module_name)
        
        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器配置"""
        self.logger.setLevel(logging.DEBUG)
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt='[%(name)s][%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器 - 所有日志都写入all.log
        log_file = os.path.join(self.log_dir, 'all.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.encoding = 'utf-8'
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """输出DEBUG级别日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """输出INFO级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """输出WARNING级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """输出ERROR级别日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """输出CRITICAL级别日志"""
        self.logger.critical(message)


def get_logger(module_name: str, log_dir: str = 'log') -> StandardizedLogger:
    """
    获取标准化日志器实例
    
    Args:
        module_name: 模块名称
        log_dir: 日志目录
    
    Returns:
        StandardizedLogger: 标准化日志器实例
    """
    return StandardizedLogger(module_name, log_dir)


# 全局日志器缓存
_logger_cache = {}


def get_cached_logger(module_name: str, log_dir: str = 'log') -> StandardizedLogger:
    """
    获取缓存的标准化日志器实例（避免重复创建）
    
    Args:
        module_name: 模块名称
        log_dir: 日志目录
    
    Returns:
        StandardizedLogger: 标准化日志器实例
    """
    cache_key = f"{module_name}_{log_dir}"
    
    if cache_key not in _logger_cache:
        _logger_cache[cache_key] = StandardizedLogger(module_name, log_dir)
    
    return _logger_cache[cache_key]
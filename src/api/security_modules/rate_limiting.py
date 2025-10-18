"""
请求速率限制器模块
限制每个IP地址一分钟内最多50次请求，超过则返回429状态码
"""

import time
import threading
from collections import defaultdict, deque
from typing import Tuple, Dict, Optional
from flask import request


class RateLimitingManager:
    """请求速率限制管理器"""
    
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数，默认50
            window_seconds: 时间窗口大小（秒），默认60秒
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # 存储每个IP的请求时间戳
        self.request_timestamps: Dict[str, deque] = defaultdict(deque)
        
        # 线程锁，确保线程安全
        self._lock = threading.Lock()
        
        # 上次清理时间
        self._last_cleanup = time.time()
        
        # 清理间隔（5分钟清理一次过期数据）
        self._cleanup_interval = 300
    
    def get_client_ip(self) -> str:
        """
        获取客户端真实IP地址
        
        Returns:
            str: 客户端IP地址
        """
        # 优先从X-Forwarded-For获取真实IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'
        
        return client_ip
    
    def is_rate_limited(self, ip: Optional[str] = None) -> Tuple[bool, Dict[str, any]]:
        """
        检查IP是否被速率限制
        
        Args:
            ip: IP地址，如果为None则自动获取
            
        Returns:
            Tuple[bool, Dict]: (是否被限制, 限制信息)
        """
        if ip is None:
            ip = self.get_client_ip()
        
        current_time = time.time()
        
        with self._lock:
            # 定期清理过期数据
            self._periodic_cleanup(current_time)
            
            # 获取该IP的请求时间戳队列
            timestamps = self.request_timestamps[ip]
            
            # 清理窗口外的旧时间戳
            window_start = current_time - self.window_seconds
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()
            
            # 检查是否超过限制
            request_count = len(timestamps)
            is_limited = request_count >= self.max_requests
            
            # 如果没有被限制，记录当前请求
            if not is_limited:
                timestamps.append(current_time)
            
            # 计算重置时间（下一个时间窗口开始时间）
            reset_time = int(timestamps[0] + self.window_seconds) if timestamps else int(current_time + self.window_seconds)
            remaining_requests = max(0, self.max_requests - request_count - (0 if is_limited else 1))
            
            limit_info = {
                'limit': self.max_requests,
                'remaining': remaining_requests,
                'reset': reset_time,
                'window_seconds': self.window_seconds,
                'current_requests': request_count + (0 if is_limited else 1),
                'client_ip': ip
            }
            
            return is_limited, limit_info
    
    def _periodic_cleanup(self, current_time: float):
        """
        定期清理过期数据
        
        Args:
            current_time: 当前时间戳
        """
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired_data(current_time)
            self._last_cleanup = current_time
    
    def _cleanup_expired_data(self, current_time: float):
        """
        清理过期的请求记录
        
        Args:
            current_time: 当前时间戳
        """
        window_start = current_time - self.window_seconds
        expired_ips = []
        
        for ip, timestamps in self.request_timestamps.items():
            # 清理该IP的过期时间戳
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()
            
            # 如果该IP没有活跃请求，标记为待删除
            if not timestamps:
                expired_ips.append(ip)
        
        # 删除没有活跃请求的IP记录
        for ip in expired_ips:
            del self.request_timestamps[ip]
    
    def get_stats(self) -> Dict[str, any]:
        """
        获取速率限制器统计信息
        
        Returns:
            Dict: 统计信息
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        with self._lock:
            active_ips = 0
            total_requests = 0
            
            for ip, timestamps in self.request_timestamps.items():
                # 统计活跃IP（有窗口内请求的IP）
                active_requests = sum(1 for ts in timestamps if ts >= window_start)
                if active_requests > 0:
                    active_ips += 1
                    total_requests += active_requests
            
            return {
                'max_requests_per_window': self.max_requests,
                'window_seconds': self.window_seconds,
                'active_ips': active_ips,
                'total_tracked_ips': len(self.request_timestamps),
                'total_active_requests': total_requests,
                'last_cleanup': self._last_cleanup
            }
    
    def reset_ip_limit(self, ip: str) -> bool:
        """
        重置特定IP的限制（管理员功能）
        
        Args:
            ip: 要重置的IP地址
            
        Returns:
            bool: 是否成功重置
        """
        with self._lock:
            if ip in self.request_timestamps:
                del self.request_timestamps[ip]
                return True
            return False
    
    def get_ip_status(self, ip: Optional[str] = None) -> Dict[str, any]:
        """
        获取特定IP的状态信息
        
        Args:
            ip: IP地址，如果为None则自动获取
            
        Returns:
            Dict: IP状态信息
        """
        if ip is None:
            ip = self.get_client_ip()
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        with self._lock:
            timestamps = self.request_timestamps.get(ip, deque())
            
            # 计算窗口内的请求数
            active_requests = sum(1 for ts in timestamps if ts >= window_start)
            
            return {
                'ip': ip,
                'requests_in_window': active_requests,
                'limit': self.max_requests,
                'remaining': max(0, self.max_requests - active_requests),
                'window_seconds': self.window_seconds,
                'is_limited': active_requests >= self.max_requests
            }


# 全局速率限制器实例
rate_limiter = RateLimitingManager(max_requests=60, window_seconds=60)


def check_rate_limit(ip: Optional[str] = None) -> Tuple[bool, Dict[str, any]]:
    """
    检查速率限制（便捷函数）
    
    Args:
        ip: IP地址，如果为None则自动获取
        
    Returns:
        Tuple[bool, Dict]: (是否被限制, 限制信息)
    """
    return rate_limiter.is_rate_limited(ip)


def get_rate_limit_stats() -> Dict[str, any]:
    """
    获取速率限制统计信息（便捷函数）
    
    Returns:
        Dict: 统计信息
    """
    return rate_limiter.get_stats()


def reset_rate_limit(ip: str) -> bool:
    """
    重置IP速率限制（便捷函数）
    
    Args:
        ip: 要重置的IP地址
        
    Returns:
        bool: 是否成功重置
    """
    return rate_limiter.reset_ip_limit(ip)
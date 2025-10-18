"""
安全模块二级调用器
负责调用 src/api/security_modules/ 中的各个安全模块来完成安全检查工作
"""

from functools import wraps
from flask import request, jsonify
from typing import Tuple, Dict, Optional, Any

# 导入各个安全模块
from .security_modules.file_type_verification import verify_uploaded_file, get_uploaded_file_info
from .security_modules.rate_limiting import check_rate_limit, get_rate_limit_stats
from .security_modules.IP_banned import is_banned_ip, ban_ip_address, unban_ip_address, get_banned_ip_list, get_ban_stats


class SecurityManager:
    """安全管理器 - 二级调用器"""
    
    def __init__(self):
        """初始化安全管理器"""
        pass
    
    def get_client_ip(self) -> str:
        """
        获取客户端真实IP地址
        
        Returns:
            str: 客户端IP地址
        """
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'
        return client_ip
    
    def check_ip_security(self, ip: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        综合检查IP安全状态（黑名单 + 速率限制）
        
        Args:
            ip: IP地址，如果为None则自动获取
            
        Returns:
            Tuple[bool, Dict]: (是否被阻止, 阻止信息)
        """
        if ip is None:
            ip = self.get_client_ip()
        
        # 1. 检查IP黑名单
        is_banned, ban_info = is_banned_ip(ip)
        if is_banned:
            return True, {
                'type': 'ip_banned',
                'message': f'IP地址已被封禁',
                'details': ban_info,
                'client_ip': ip
            }
        
        # 2. 检查速率限制
        is_limited, limit_info = check_rate_limit(ip)
        if is_limited:
            return True, {
                'type': 'rate_limited',
                'message': f'请求过于频繁，剩余配额: {limit_info.get("remaining", 0)}',
                'details': limit_info,
                'client_ip': ip
            }
        
        return False, {}
    
    def validate_uploaded_file(self, file) -> Tuple[bool, str, Dict]:
        """
        验证上传的文件
        
        Args:
            file: Flask文件对象
            
        Returns:
            Tuple[bool, str, Dict]: (是否通过验证, 错误信息, 文件信息)
        """
        # 获取文件信息
        file_info = get_uploaded_file_info(file)
        
        # 验证文件
        is_valid, error_msg = verify_uploaded_file(file)
        
        return is_valid, error_msg, file_info
    
    def security_check_decorator(self, check_file: bool = False):
        """
        综合安全检查装饰器
        
        Args:
            check_file: 是否检查文件上传
            
        Returns:
            装饰器函数
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # IP安全检查
                is_blocked, block_info = self.check_ip_security()
                if is_blocked:
                    return jsonify({
                        "error": block_info['message'],
                        "type": block_info['type'],
                        "client_ip": block_info['client_ip']
                    }), 429
                
                # 文件上传检查
                if check_file and request.files:
                    for file_key in request.files:
                        file = request.files[file_key]
                        if file and file.filename:
                            is_valid, error_msg, file_info = self.validate_uploaded_file(file)
                            if not is_valid:
                                return jsonify({
                                    "error": error_msg,
                                    "type": "file_validation_failed",
                                    "file_info": file_info
                                }), 400
                
                return f(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_security_stats(self) -> Dict[str, Any]:
        """
        获取安全模块统计信息
        
        Returns:
            Dict: 各模块统计信息
        """
        try:
            return {
                'rate_limiting': get_rate_limit_stats(),
                'ip_bans': get_ban_stats(),
                'client_ip': self.get_client_ip(),
                'timestamp': __import__('time').time()
            }
        except Exception as e:
            return {
                'error': f'获取安全统计信息失败: {str(e)}'
            }


# 全局安全管理器实例
security_manager = SecurityManager()


def get_client_ip() -> str:
    """获取客户端IP（便捷函数）"""
    return security_manager.get_client_ip()


def security_check(check_file: bool = False):
    """
    安全检查装饰器（便捷函数）
    
    Args:
        check_file: 是否检查文件上传
        
    Returns:
        装饰器函数
    """
    return security_manager.security_check_decorator(check_file=check_file)


def validate_file_upload(file) -> Tuple[bool, str, Dict]:
    """
    验证文件上传（便捷函数）
    
    Args:
        file: Flask文件对象
        
    Returns:
        Tuple[bool, str, Dict]: (是否通过验证, 错误信息, 文件信息)
    """
    return security_manager.validate_uploaded_file(file)


def check_ip_access(ip: Optional[str] = None) -> Tuple[bool, Dict]:
    """
    检查IP访问权限（便捷函数）
    
    Args:
        ip: IP地址，如果为None则自动获取
        
    Returns:
        Tuple[bool, Dict]: (是否被阻止, 阻止信息)
    """
    return security_manager.check_ip_security(ip)


def get_all_security_stats() -> Dict[str, Any]:
    """
    获取所有安全统计信息（便捷函数）
    
    Returns:
        Dict: 安全统计信息
    """
    return security_manager.get_security_stats()


def ban_client_ip(duration_seconds: Optional[int] = None, reason: str = "") -> bool:
    """
    封禁当前客户端IP（便捷函数）
    
    Args:
        duration_seconds: 封禁时长（秒），None表示永久封禁
        reason: 封禁原因
        
    Returns:
        bool: 是否成功封禁
    """
    client_ip = get_client_ip()
    return ban_ip_address(client_ip, duration_seconds, reason)


# 兼容性：保留旧的RateLimiter类引用
class RateLimiter:
    """兼容性类 - 重定向到新的安全管理器"""
    
    def __init__(self):
        pass
    
    def get_client_ip(self):
        return get_client_ip()
    
    def rate_limit(self, max_attempts=5, window_seconds=60, block_seconds=5):
        """兼容性方法"""
        return security_check()
    
    def get_stats(self):
        """兼容性方法"""
        return get_all_security_stats().get('rate_limiting', {})
    
    def clear_expired(self):
        """兼容性方法 - 不再需要手动清理"""
        pass
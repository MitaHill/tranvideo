import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify


class RateLimiter:
    """IP速率限制器"""

    def __init__(self):
        self.attempts = defaultdict(deque)  # IP -> [timestamp1, timestamp2, ...]
        self.blocked = {}  # IP -> block_until_timestamp

    def get_client_ip(self):
        """获取客户端真实IP"""
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        return client_ip

    def is_blocked(self, ip):
        """检查IP是否被封禁"""
        if ip not in self.blocked:
            return False, 0

        current_time = time.time()
        if current_time < self.blocked[ip]:
            remaining = int(self.blocked[ip] - current_time)
            return True, remaining
        else:
            # 解除封禁
            del self.blocked[ip]
            self.attempts[ip].clear()
            return False, 0

    def add_attempt(self, ip, window_seconds):
        """添加请求记录并清理过期记录"""
        current_time = time.time()
        attempts = self.attempts[ip]

        # 清理过期记录
        while attempts and current_time - attempts[0] > window_seconds:
            attempts.popleft()

        # 添加当前请求
        attempts.append(current_time)
        return len(attempts)

    def block_ip(self, ip, block_seconds):
        """封禁IP"""
        self.blocked[ip] = time.time() + block_seconds

    def rate_limit(self, max_attempts=5, window_seconds=60, block_seconds=5):
        """速率限制装饰器"""

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                client_ip = self.get_client_ip()

                # 检查是否被封禁
                is_blocked, remaining = self.is_blocked(client_ip)
                if is_blocked:
                    return jsonify({
                        "error": f"IP被暂时封禁，剩余时间: {remaining}秒",
                        "client_ip": client_ip
                    }), 429

                # 检查请求频率
                attempt_count = self.add_attempt(client_ip, window_seconds)

                if attempt_count > max_attempts:
                    # 封禁IP
                    self.block_ip(client_ip, block_seconds)
                    return jsonify({
                        "error": f"请求过于频繁，IP已被封禁{block_seconds}秒",
                        "client_ip": client_ip
                    }), 429

                return f(*args, **kwargs)

            return wrapper

        return decorator

    def get_stats(self):
        """获取统计信息"""
        current_time = time.time()
        active_blocks = {
            ip: int(block_time - current_time)
            for ip, block_time in self.blocked.items()
            if block_time > current_time
        }

        return {
            "blocked_ips": len(active_blocks),
            "active_blocks": active_blocks,
            "tracked_ips": len(self.attempts)
        }

    def clear_expired(self):
        """清理过期数据"""
        current_time = time.time()

        # 清理过期封禁
        expired_blocks = [
            ip for ip, block_time in self.blocked.items()
            if block_time <= current_time
        ]
        for ip in expired_blocks:
            del self.blocked[ip]
            self.attempts[ip].clear()

        # 清理空的attempts记录
        empty_attempts = [
            ip for ip, attempts in self.attempts.items()
            if len(attempts) == 0
        ]
        for ip in empty_attempts:
            del self.attempts[ip]
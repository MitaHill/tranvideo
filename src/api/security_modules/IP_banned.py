"""
IP地址封禁模块
管理IP黑名单，支持临时和永久封禁，程序每3秒读取一次数据库
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import request


class IPBanManager:
    """IP封禁管理器"""
    
    def __init__(self, db_path: str = "db/IP_black.json", refresh_interval: int = 3):
        """
        初始化IP封禁管理器
        
        Args:
            db_path: 黑名单数据库文件路径
            refresh_interval: 数据库刷新间隔（秒），默认3秒
        """
        self.db_path = db_path
        self.refresh_interval = refresh_interval
        
        # 内存中的黑名单缓存
        self._blacklist_cache: Dict[str, Dict] = {}
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 上次刷新时间
        self._last_refresh = 0
        
        # 确保数据库文件存在
        self._ensure_db_exists()
        
        # 初始加载
        self._refresh_cache()
    
    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            initial_data = {
                "blacklist": {},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "description": "IP地址黑名单数据库"
                }
            }
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _load_database(self) -> Dict:
        """加载数据库"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 如果数据库损坏，重新创建
            self._ensure_db_exists()
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _save_database(self, data: Dict):
        """保存数据库"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _refresh_cache(self):
        """刷新内存缓存"""
        current_time = time.time()
        
        # 检查是否需要刷新
        if current_time - self._last_refresh < self.refresh_interval:
            return
        
        try:
            data = self._load_database()
            
            with self._lock:
                self._blacklist_cache = data.get("blacklist", {})
                self._last_refresh = current_time
                
                # 清理过期的封禁记录
                self._cleanup_expired_bans()
                
        except Exception as e:
            print(f"[ERROR] 刷新IP黑名单缓存失败: {e}")
    
    def _cleanup_expired_bans(self):
        """清理过期的封禁记录"""
        current_timestamp = time.time()
        expired_ips = []
        
        for ip, ban_info in self._blacklist_cache.items():
            unban_time = ban_info.get('unban_time')
            
            # 如果有解封时间且已过期，标记为删除
            if unban_time and current_timestamp >= unban_time:
                expired_ips.append(ip)
        
        # 从缓存中删除过期记录
        for ip in expired_ips:
            del self._blacklist_cache[ip]
        
        # 如果有过期记录，更新数据库
        if expired_ips:
            try:
                data = self._load_database()
                for ip in expired_ips:
                    if ip in data["blacklist"]:
                        del data["blacklist"][ip]
                self._save_database(data)
                print(f"[INFO] 清理了 {len(expired_ips)} 个过期的IP封禁记录")
            except Exception as e:
                print(f"[ERROR] 清理过期IP封禁记录失败: {e}")
    
    def get_client_ip(self) -> str:
        """获取客户端真实IP地址"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'
        return client_ip
    
    def is_ip_banned(self, ip: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        检查IP是否被封禁
        
        Args:
            ip: IP地址，如果为None则自动获取
            
        Returns:
            Tuple[bool, Dict]: (是否被封禁, 封禁信息)
        """
        if ip is None:
            ip = self.get_client_ip()
        
        # 刷新缓存
        self._refresh_cache()
        
        with self._lock:
            ban_info = self._blacklist_cache.get(ip)
            
            if not ban_info:
                return False, {}
            
            current_timestamp = time.time()
            unban_time = ban_info.get('unban_time')
            
            # 检查是否已过期
            if unban_time and current_timestamp >= unban_time:
                return False, {}
            
            # 计算剩余封禁时间
            remaining_seconds = 0
            if unban_time:
                remaining_seconds = max(0, int(unban_time - current_timestamp))
            
            return True, {
                'ip': ip,
                'banned_at': ban_info.get('banned_at'),
                'unban_time': unban_time,
                'remaining_seconds': remaining_seconds,
                'reason': ban_info.get('reason', ''),
                'is_permanent': unban_time is None
            }
    
    def ban_ip(self, ip: str, duration_seconds: Optional[int] = None, reason: str = "") -> bool:
        """
        封禁IP地址
        
        Args:
            ip: 要封禁的IP地址
            duration_seconds: 封禁时长（秒），None表示永久封禁
            reason: 封禁原因
            
        Returns:
            bool: 是否成功封禁
        """
        try:
            current_timestamp = time.time()
            unban_time = None
            
            if duration_seconds is not None:
                unban_time = current_timestamp + duration_seconds
            
            ban_record = {
                'ip': ip,
                'banned_at': current_timestamp,
                'banned_at_readable': datetime.now().isoformat(),
                'unban_time': unban_time,
                'unban_time_readable': datetime.fromtimestamp(unban_time).isoformat() if unban_time else None,
                'duration_seconds': duration_seconds,
                'reason': reason,
                'is_permanent': duration_seconds is None
            }
            
            # 更新数据库
            data = self._load_database()
            data["blacklist"][ip] = ban_record
            self._save_database(data)
            
            # 更新缓存
            with self._lock:
                self._blacklist_cache[ip] = ban_record
            
            duration_str = f"{duration_seconds}秒" if duration_seconds else "永久"
            print(f"[INFO] IP {ip} 已被封禁，时长: {duration_str}，原因: {reason}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 封禁IP {ip} 失败: {e}")
            return False
    
    def unban_ip(self, ip: str) -> bool:
        """
        解封IP地址
        
        Args:
            ip: 要解封的IP地址
            
        Returns:
            bool: 是否成功解封
        """
        try:
            # 更新数据库
            data = self._load_database()
            if ip not in data["blacklist"]:
                return False
            
            del data["blacklist"][ip]
            self._save_database(data)
            
            # 更新缓存
            with self._lock:
                if ip in self._blacklist_cache:
                    del self._blacklist_cache[ip]
            
            print(f"[INFO] IP {ip} 已被解封")
            return True
            
        except Exception as e:
            print(f"[ERROR] 解封IP {ip} 失败: {e}")
            return False
    
    def get_banned_ips(self) -> List[Dict]:
        """
        获取所有被封禁的IP列表
        
        Returns:
            List[Dict]: 封禁IP列表
        """
        self._refresh_cache()
        
        with self._lock:
            banned_list = []
            current_timestamp = time.time()
            
            for ip, ban_info in self._blacklist_cache.items():
                unban_time = ban_info.get('unban_time')
                
                # 跳过已过期的封禁
                if unban_time and current_timestamp >= unban_time:
                    continue
                
                # 计算剩余时间
                remaining_seconds = 0
                if unban_time:
                    remaining_seconds = max(0, int(unban_time - current_timestamp))
                
                banned_list.append({
                    'ip': ip,
                    'banned_at': ban_info.get('banned_at_readable', ''),
                    'unban_time': ban_info.get('unban_time_readable', ''),
                    'remaining_seconds': remaining_seconds,
                    'reason': ban_info.get('reason', ''),
                    'is_permanent': ban_info.get('is_permanent', False)
                })
            
            return banned_list
    
    def get_stats(self) -> Dict:
        """
        获取封禁统计信息
        
        Returns:
            Dict: 统计信息
        """
        self._refresh_cache()
        
        with self._lock:
            total_bans = len(self._blacklist_cache)
            permanent_bans = sum(1 for ban in self._blacklist_cache.values() if ban.get('is_permanent', False))
            temporary_bans = total_bans - permanent_bans
            
            return {
                'total_banned_ips': total_bans,
                'permanent_bans': permanent_bans,
                'temporary_bans': temporary_bans,
                'last_refresh': self._last_refresh,
                'refresh_interval': self.refresh_interval
            }


# 全局IP封禁管理器实例
ip_ban_manager = IPBanManager()


def is_banned_ip(ip: Optional[str] = None) -> Tuple[bool, Dict]:
    """
    检查IP是否被封禁（便捷函数）
    
    Args:
        ip: IP地址，如果为None则自动获取
        
    Returns:
        Tuple[bool, Dict]: (是否被封禁, 封禁信息)
    """
    return ip_ban_manager.is_ip_banned(ip)


def ban_ip_address(ip: str, duration_seconds: Optional[int] = None, reason: str = "") -> bool:
    """
    封禁IP地址（便捷函数）
    
    Args:
        ip: 要封禁的IP地址
        duration_seconds: 封禁时长（秒），None表示永久封禁
        reason: 封禁原因
        
    Returns:
        bool: 是否成功封禁
    """
    return ip_ban_manager.ban_ip(ip, duration_seconds, reason)


def unban_ip_address(ip: str) -> bool:
    """
    解封IP地址（便捷函数）
    
    Args:
        ip: 要解封的IP地址
        
    Returns:
        bool: 是否成功解封
    """
    return ip_ban_manager.unban_ip(ip)


def get_banned_ip_list() -> List[Dict]:
    """
    获取被封禁的IP列表（便捷函数）
    
    Returns:
        List[Dict]: 封禁IP列表
    """
    return ip_ban_manager.get_banned_ips()


def get_ban_stats() -> Dict:
    """
    获取封禁统计信息（便捷函数）
    
    Returns:
        Dict: 统计信息
    """
    return ip_ban_manager.get_stats()
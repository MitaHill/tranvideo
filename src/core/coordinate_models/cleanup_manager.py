"""
清理管理器
负责任务过期检测和数据库健康维护相关功能
"""

from datetime import datetime
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("清理管理器")


class CleanupManager:
    """清理管理器，负责过期任务检测和数据库健康维护"""
    
    def __init__(self, database_handler):
        self.db = database_handler
    
    def get_expired_tasks(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取过期的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        
        Returns:
            过期任务列表
        """
        with self.db._lock:
            data = self.db.load_data()
            expired_tasks = []
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for task_id, task in data["single_tasks"].items():
                # 检查已下载的任务是否过期（24小时后清理）
                if (task["status"] == "被下载过进入清理倒计时" and 
                    current_time - task["updated_at"] > max_age_seconds):
                    expired_tasks.append(task)
                # 注意: "已完成"状态的长期未下载任务由get_long_term_undownloaded_tasks专门处理
                # 这里不再处理"已完成"状态，避免与长期未下载清理逻辑冲突
            
            return expired_tasks
    
    def get_long_term_undownloaded_tasks(self, max_age_days: int = 3) -> List[Dict[str, Any]]:
        """
        获取长期未下载的已完成任务（连续3天未下载）
        
        Args:
            max_age_days: 最大未下载天数
        
        Returns:
            长期未下载的任务列表
        """
        with self.db._lock:
            data = self.db.load_data()
            undownloaded_tasks = []
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_days * 24 * 3600  # 3天转换为秒
            
            for task_id, task in data["single_tasks"].items():
                # 检查状态为"已完成"且超过指定天数未下载的任务
                if (task["status"] == "已完成" and 
                    current_time - task["updated_at"] > max_age_seconds):
                    undownloaded_tasks.append(task)
            
            return undownloaded_tasks
    
    def get_cleanable_database_tasks(self, cleanup_delay_seconds: int = 320) -> List[Dict[str, Any]]:
        """
        获取可从数据库清理的任务
        
        Args:
            cleanup_delay_seconds: 状态为'过期文件已经被清理'后的等待清理时间（秒）
        
        Returns:
            可清理的任务列表
        """
        with self.db._lock:
            data = self.db.load_data()
            cleanable_tasks = []
            current_time = datetime.now().timestamp()
            
            for task_id, task in data["single_tasks"].items():
                # 检查状态为'过期文件已经被清理'的任务
                if task["status"] == "过期文件已经被清理":
                    # 基于时间戳计算是否到了清理时间
                    time_since_marked = current_time - task["updated_at"]
                    if time_since_marked >= cleanup_delay_seconds:
                        cleanable_tasks.append(task)
            
            return cleanable_tasks
    
    def get_stale_database_records(self, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        获取陈旧的数据库记录（用于深度清理）
        
        Args:
            max_age_days: 最大保留天数
        
        Returns:
            陈旧记录列表
        """
        with self.db._lock:
            data = self.db.load_data()
            stale_records = []
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_days * 24 * 3600
            
            # 检查单个任务
            for task_id, task in data["single_tasks"].items():
                if current_time - task["created_at"] > max_age_seconds:
                    stale_records.append({
                        "type": "single_task",
                        "id": task_id,
                        "data": task
                    })
            
            # 检查批量任务
            for batch_id, batch_task in data["batch_tasks"].items():
                if current_time - batch_task["created_at"] > max_age_seconds:
                    stale_records.append({
                        "type": "batch_task",
                        "id": batch_id,
                        "data": batch_task
                    })
            
            return stale_records
    
    def get_orphaned_batch_tasks(self) -> List[Dict[str, Any]]:
        """
        获取孤立的批量任务（子任务都不存在）
        
        Returns:
            孤立的批量任务列表
        """
        data = self.db.load_data()
        orphaned_batches = []
        
        for batch_id, batch_task in data["batch_tasks"].items():
            has_valid_subtasks = False
            
            for task_id in batch_task["sub_tasks"]:
                if task_id in data["single_tasks"]:
                    has_valid_subtasks = True
                    break
            
            if not has_valid_subtasks:
                orphaned_batches.append(batch_task)
        
        return orphaned_batches
    
    def cleanup_orphaned_batch_tasks(self) -> int:
        """
        清理孤立的批量任务
        
        Returns:
            清理的批量任务数量
        """
        orphaned_batches = self.get_orphaned_batch_tasks()
        cleaned_count = 0
        
        with self.db._lock:
            data = self.db.load_data()
            
            for batch_task in orphaned_batches:
                batch_id = batch_task["batch_id"]
                if batch_id in data["batch_tasks"]:
                    del data["batch_tasks"][batch_id]
                    cleaned_count += 1
                    logger.info(f"清理孤立批量任务: {batch_id}")
            
            if cleaned_count > 0:
                self.db.save_data(data)
        
        return cleaned_count
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            数据库统计信息
        """
        data = self.db.load_data()
        
        # 统计任务状态
        status_stats = {}
        for task in data["single_tasks"].values():
            status = task["status"]
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 统计批量任务状态
        batch_status_stats = {}
        for batch_task in data["batch_tasks"].values():
            status = batch_task["status"]
            batch_status_stats[status] = batch_status_stats.get(status, 0) + 1
        
        # 计算数据库大小和年龄
        current_time = datetime.now().timestamp()
        metadata = data.get("metadata", {})
        db_age_days = (current_time - metadata.get("created_at", current_time)) / (24 * 3600)
        
        return {
            "database_version": metadata.get("version", "unknown"),
            "database_age_days": round(db_age_days, 1),
            "total_single_tasks": len(data["single_tasks"]),
            "total_batch_tasks": len(data["batch_tasks"]),
            "single_task_status_breakdown": status_stats,
            "batch_task_status_breakdown": batch_status_stats,
            "orphaned_batch_tasks": len(self.get_orphaned_batch_tasks()),
            "cleanable_tasks": len(self.get_cleanable_database_tasks()),
            "expired_tasks": len(self.get_expired_tasks())
        }
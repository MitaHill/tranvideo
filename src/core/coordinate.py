"""
任务状态协调模块 - 重构版
负责统一管理 tasks.json 数据库，作为各子模块的调用入口
将原有的单一文件拆分为多个专责模块，提高代码可维护性
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.logger import get_cached_logger

from .coordinate_models import DatabaseHandler, TaskManager, BatchManager, CleanupManager

logger = get_cached_logger("任务协调器")


class TaskCoordinator:
    """
    任务协调器 - 重构版
    作为统一的调用入口，将具体功能委托给专门的子模块处理
    """
    
    def __init__(self, db_path: str = "db/tasks.json"):
        """
        初始化任务协调器
        
        Args:
            db_path: 数据库文件路径
        """
        # 初始化各个专责模块
        self.database = DatabaseHandler(db_path)
        self.task_manager = TaskManager(self.database)
        self.batch_manager = BatchManager(self.database)
        self.cleanup_manager = CleanupManager(self.database)
        
    
    # =========================
    # 单个任务相关方法
    # =========================
    
    def create_single_task(self, task_id: str, video_path: str, video_name: str, 
                          video_duration: float, mode: str = "srt", 
                          invite_code: str = "", batch_id: Optional[str] = None) -> bool:
        """创建单个任务"""
        return self.task_manager.create_single_task(
            task_id, video_path, video_name, video_duration, mode, invite_code, batch_id
        )
    
    def update_task_status(self, task_id: str, status: str, progress: str = "", 
                          current_step: str = "", error = "UNCHANGED", 
                          resume_data: Dict[str, Any] = None) -> bool:
        """更新任务状态"""
        success = self.task_manager.update_task_status(
            task_id, status, progress, current_step, error, resume_data
        )
        
        # 如果任务属于批量任务，同时更新批量任务状态
        if success:
            task = self.get_task(task_id)
            if task and task.get("batch_id"):
                data = self.database.load_data()
                self.batch_manager.update_batch_task_status(data, task["batch_id"])
                self.database.save_data(data)
        
        return success
    
    def update_task_progress(self, task_id: str, progress_percentage: float) -> bool:
        """更新任务进度百分比"""
        return self.task_manager.update_task_progress(task_id, progress_percentage)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务信息"""
        return self.task_manager.get_task(task_id)
    
    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """获取所有未完成的任务"""
        return self.task_manager.get_incomplete_tasks()
    
    def mark_task_downloaded(self, task_id: str) -> bool:
        """标记任务已被下载"""
        return self.task_manager.mark_task_downloaded(task_id)
    
    def mark_task_expired(self, task_id: str) -> bool:
        """标记任务已过期并被清理"""
        return self.task_manager.mark_task_expired(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return self.task_manager.delete_task(task_id)
    
    def get_task_count_by_status(self) -> Dict[str, int]:
        """获取各状态任务数量统计"""
        return self.task_manager.get_task_count_by_status()
    
    # =========================
    # 批量任务相关方法
    # =========================
    
    def create_batch_task(self, batch_id: str, single_task_ids: List[str]) -> bool:
        """创建批量任务"""
        return self.batch_manager.create_batch_task(batch_id, single_task_ids)
    
    def get_batch_task(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批量任务信息"""
        return self.batch_manager.get_batch_task(batch_id)
    
    def get_batch_tasks_by_status(self, status: str = None) -> List[Dict[str, Any]]:
        """根据状态获取批量任务列表"""
        return self.batch_manager.get_batch_tasks_by_status(status)
    
    def delete_batch_task(self, batch_id: str) -> bool:
        """删除批量任务"""
        return self.batch_manager.delete_batch_task(batch_id)
    
    def get_batch_task_progress(self, batch_id: str) -> Dict[str, Any]:
        """获取批量任务的整体进度"""
        return self.batch_manager.get_batch_task_progress(batch_id)
    
    # =========================
    # 清理相关方法
    # =========================
    
    def get_expired_tasks(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """获取过期的任务"""
        return self.cleanup_manager.get_expired_tasks(max_age_hours)
    
    def get_long_term_undownloaded_tasks(self, max_age_days: int = 3) -> List[Dict[str, Any]]:
        """获取长期未下载的已完成任务"""
        return self.cleanup_manager.get_long_term_undownloaded_tasks(max_age_days)
    
    def get_cleanable_database_tasks(self, cleanup_delay_seconds: int = 320) -> List[Dict[str, Any]]:
        """获取可从数据库清理的任务"""
        return self.cleanup_manager.get_cleanable_database_tasks(cleanup_delay_seconds)
    
    def permanently_delete_task(self, task_id: str) -> bool:
        """永久删除任务记录（仅用于数据库健康维护）"""
        return self.task_manager.delete_task(task_id)
    
    def get_stale_database_records(self, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """获取陈旧的数据库记录"""
        return self.cleanup_manager.get_stale_database_records(max_age_days)
    
    def cleanup_orphaned_batch_tasks(self) -> int:
        """清理孤立的批量任务"""
        return self.cleanup_manager.cleanup_orphaned_batch_tasks()
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.cleanup_manager.get_database_statistics()
    
    # =========================
    # 数据库相关方法
    # =========================
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """获取所有任务信息"""
        return self.database.load_data()
    
    def stop(self):
        """停止协调器，清理资源"""
        self.database.stop_queue_processor()
    
    # =========================
    # 兼容性方法（保持向后兼容）
    # =========================
    
    def _load_data(self) -> Dict[str, Any]:
        """兼容性方法：加载数据"""
        return self.database.load_data()
    
    def _save_data(self, data: Dict[str, Any]):
        """兼容性方法：保存数据"""
        return self.database.save_data(data)
    
    @property
    def _lock(self):
        """兼容性属性：获取数据库锁"""
        return self.database._lock


# 全局任务协调器实例
task_coordinator = TaskCoordinator()
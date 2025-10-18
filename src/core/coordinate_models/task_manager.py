"""
任务管理器
负责单个任务的创建、更新、查询等操作
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("任务管理器")


class TaskManager:
    """任务管理器，负责单个任务的所有操作"""
    
    def __init__(self, database_handler):
        self.db = database_handler
    
    def create_single_task_direct(self, task_id: str, video_path: str, video_name: str, 
                                 video_duration: float, mode: str = "srt", 
                                 invite_code: str = "", batch_id: Optional[str] = None) -> bool:
        """直接创建单个任务（不通过队列）"""
        data = self.db._load_data_direct()
        
        if task_id in data["single_tasks"]:
            return False
        
        current_time = datetime.now().timestamp()
        data["single_tasks"][task_id] = {
            "task_id": task_id,
            "video_path": video_path,
            "video_name": video_name,
            "video_duration": video_duration,
            "mode": mode,
            "invite_code": invite_code,
            "batch_id": batch_id,
            "status": "队列中",
            "progress": "初始化...",
            "created_at": current_time,
            "updated_at": current_time,
            "resumable": True,
            "resume_data": {},
            "current_step": "pending",
            "error": None,
            "prog_bar": 0  # 进度条初始化为0%
        }
        
        self.db._save_data_direct(data)
        return True
    
    def create_single_task(self, task_id: str, video_path: str, video_name: str, 
                          video_duration: float, mode: str = "srt", 
                          invite_code: str = "", batch_id: Optional[str] = None) -> bool:
        """
        创建单个任务
        
        Args:
            task_id: 任务ID
            video_path: 视频路径
            video_name: 视频名称
            video_duration: 视频时长（秒）
            mode: 输出模式
            invite_code: 邀请码
            batch_id: 批量任务ID（如果属于批量任务）
        
        Returns:
            创建是否成功
        """
        return self.db._queue_operation(
            self.create_single_task_direct, task_id, video_path, video_name,
            video_duration, mode, invite_code, batch_id
        )
    
    def update_task_status_direct(self, task_id: str, status: str, progress: str = "", 
                                 current_step: str = "", error = "UNCHANGED", 
                                 resume_data: Dict[str, Any] = None) -> bool:
        """直接更新任务状态（不通过队列）"""
        data = self.db._load_data_direct()
        
        if task_id not in data["single_tasks"]:
            return False
        
        task = data["single_tasks"][task_id]
        task["status"] = status
        task["updated_at"] = datetime.now().timestamp()
        
        if progress:
            task["progress"] = progress
        if current_step:
            task["current_step"] = current_step
        if error != "UNCHANGED":
            task["error"] = error
        if resume_data is not None:
            task["resume_data"] = resume_data
        
        self.db._save_data_direct(data)
        return True
    
    def update_task_status(self, task_id: str, status: str, progress: str = "", 
                          current_step: str = "", error = "UNCHANGED", 
                          resume_data: Dict[str, Any] = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态（队列中、提取原文字幕、翻译原文字幕、已完成、过期文件已经被清理、被下载过进入清理倒计时）
            progress: 进度描述
            current_step: 当前步骤
            error: 错误信息
            resume_data: 恢复数据
        
        Returns:
            更新是否成功
        """
        return self.db._queue_operation(
            self.update_task_status_direct, task_id, status, progress,
            current_step, error, resume_data
        )
    
    def update_task_progress_direct(self, task_id: str, progress_percentage: float) -> bool:
        """直接更新任务进度百分比（不通过队列）"""
        data = self.db._load_data_direct()
        
        if task_id not in data["single_tasks"]:
            return False
        
        task = data["single_tasks"][task_id]
        
        # 初始化prog_bar字段（如果不存在）
        if "prog_bar" not in task:
            task["prog_bar"] = 0
        
        task["prog_bar"] = round(min(100, max(0, progress_percentage)), 1)
        task["updated_at"] = datetime.now().timestamp()
        
        self.db._save_data_direct(data)
        return True
    
    def update_task_progress(self, task_id: str, progress_percentage: float) -> bool:
        """
        更新任务进度百分比
        
        Args:
            task_id: 任务ID
            progress_percentage: 进度百分比 (0-100)
        
        Returns:
            更新是否成功
        """
        return self.db._queue_operation(self.update_task_progress_direct, task_id, progress_percentage)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务信息"""
        data = self.db.load_data()
        return data["single_tasks"].get(task_id)
    
    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """获取所有未完成的任务"""
        data = self.db.load_data()
        incomplete_tasks = []
        
        for task_id, task in data["single_tasks"].items():
            if task["status"] not in ["已完成", "过期文件已经被清理", "被下载过进入清理倒计时"]:
                incomplete_tasks.append(task)
        
        return incomplete_tasks
    
    def mark_task_downloaded(self, task_id: str) -> bool:
        """标记任务已被下载"""
        return self.update_task_status(
            task_id, 
            "被下载过进入清理倒计时",
            "等待清理..."
        )
    
    def mark_task_expired(self, task_id: str) -> bool:
        """标记任务已过期并被清理"""
        return self.update_task_status(
            task_id,
            "过期文件已经被清理",
            "文件已清理"
        )
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self.db._lock:
            data = self.db.load_data()
            
            if task_id not in data["single_tasks"]:
                return False
            
            task = data["single_tasks"][task_id]
            
            # 如果属于批量任务，也要更新批量任务
            if task["batch_id"]:
                batch_id = task["batch_id"]
                if batch_id in data["batch_tasks"]:
                    if task_id in data["batch_tasks"][batch_id]["sub_tasks"]:
                        del data["batch_tasks"][batch_id]["sub_tasks"][task_id]
                    # 如果批量任务没有子任务了，删除批量任务
                    if not data["batch_tasks"][batch_id]["sub_tasks"]:
                        del data["batch_tasks"][batch_id]
            
            del data["single_tasks"][task_id]
            self.db.save_data(data)
            return True
    
    def get_task_count_by_status(self) -> Dict[str, int]:
        """获取各状态任务数量统计"""
        with self.db._lock:
            data = self.db.load_data()
            status_count = {}
            
            for task in data["single_tasks"].values():
                status = task["status"]
                status_count[status] = status_count.get(status, 0) + 1
            
            return status_count
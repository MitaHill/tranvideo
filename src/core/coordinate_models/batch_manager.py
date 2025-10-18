"""
批量任务管理器
负责批量任务的创建、更新、查询等操作
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("批量任务管理器")


class BatchManager:
    """批量任务管理器，负责批量任务的所有操作"""
    
    def __init__(self, database_handler):
        self.db = database_handler
    
    def create_batch_task(self, batch_id: str, single_task_ids: List[str]) -> bool:
        """
        创建批量任务
        
        Args:
            batch_id: 批量任务ID
            single_task_ids: 包含的单个任务ID列表
        
        Returns:
            创建是否成功
        """
        with self.db._lock:
            data = self.db.load_data()
            
            if batch_id in data["batch_tasks"]:
                return False
            
            # 验证所有单个任务都存在
            for task_id in single_task_ids:
                if task_id not in data["single_tasks"]:
                    return False
            
            # 收集子任务信息
            sub_tasks = {}
            for task_id in single_task_ids:
                task = data["single_tasks"][task_id]
                sub_tasks[task_id] = {
                    "video_name": task["video_name"],
                    "video_duration": task["video_duration"],
                    "status": task["status"],
                    "created_at": task["created_at"]
                }
                # 更新单个任务的batch_id
                data["single_tasks"][task_id]["batch_id"] = batch_id
            
            current_time = datetime.now().timestamp()
            data["batch_tasks"][batch_id] = {
                "batch_id": batch_id,
                "sub_tasks": sub_tasks,
                "created_at": current_time,
                "updated_at": current_time,
                "status": "队列中"
            }
            
            self.db.save_data(data)
            return True
    
    def update_batch_task_status(self, data: Dict[str, Any], batch_id: str):
        """更新批量任务状态"""
        if batch_id not in data["batch_tasks"]:
            return
        
        batch_task = data["batch_tasks"][batch_id]
        all_completed = True
        any_failed = False
        
        for task_id in batch_task["sub_tasks"]:
            if task_id in data["single_tasks"]:
                single_task = data["single_tasks"][task_id]
                batch_task["sub_tasks"][task_id]["status"] = single_task["status"]
                
                if single_task["status"] not in ["已完成", "过期文件已经被清理", "被下载过进入清理倒计时"]:
                    all_completed = False
                if single_task["status"] == "failed":
                    any_failed = True
        
        if all_completed:
            batch_task["status"] = "已完成"
        elif any_failed:
            batch_task["status"] = "部分失败"
        else:
            batch_task["status"] = "处理中"
        
        batch_task["updated_at"] = datetime.now().timestamp()
    
    def get_batch_task(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批量任务信息"""
        data = self.db.load_data()
        return data["batch_tasks"].get(batch_id)
    
    def get_batch_tasks_by_status(self, status: str = None) -> List[Dict[str, Any]]:
        """根据状态获取批量任务列表"""
        data = self.db.load_data()
        batch_tasks = []
        
        for batch_id, batch_task in data["batch_tasks"].items():
            if status is None or batch_task["status"] == status:
                batch_tasks.append(batch_task)
        
        return batch_tasks
    
    def delete_batch_task(self, batch_id: str) -> bool:
        """删除批量任务（同时清理子任务的batch_id）"""
        with self.db._lock:
            data = self.db.load_data()
            
            if batch_id not in data["batch_tasks"]:
                return False
            
            batch_task = data["batch_tasks"][batch_id]
            
            # 清理子任务的batch_id引用
            for task_id in batch_task["sub_tasks"]:
                if task_id in data["single_tasks"]:
                    data["single_tasks"][task_id]["batch_id"] = None
            
            # 删除批量任务记录
            del data["batch_tasks"][batch_id]
            
            self.db.save_data(data)
            return True
    
    def get_batch_task_progress(self, batch_id: str) -> Dict[str, Any]:
        """获取批量任务的整体进度"""
        batch_task = self.get_batch_task(batch_id)
        if not batch_task:
            return {"error": "批量任务不存在"}
        
        data = self.db.load_data()
        total_tasks = len(batch_task["sub_tasks"])
        completed_tasks = 0
        failed_tasks = 0
        total_progress = 0.0
        
        for task_id in batch_task["sub_tasks"]:
            if task_id in data["single_tasks"]:
                task = data["single_tasks"][task_id]
                task_status = task["status"]
                
                if task_status in ["已完成", "过期文件已经被清理", "被下载过进入清理倒计时"]:
                    completed_tasks += 1
                    total_progress += 100
                elif task_status == "failed":
                    failed_tasks += 1
                else:
                    # 获取任务当前进度
                    task_progress = task.get("prog_bar", 0)
                    total_progress += task_progress
        
        average_progress = total_progress / total_tasks if total_tasks > 0 else 0
        
        return {
            "batch_id": batch_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "average_progress": round(average_progress, 1),
            "status": batch_task["status"]
        }
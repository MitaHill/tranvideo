"""
任务状态协调模块
负责管理 tasks.json 数据库，统一处理任务状态的读写操作
"""

import json
import os
import threading
import queue
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("任务协调器备份")

class TaskCoordinator:
    """任务协调器，负责统一管理tasks.json的所有操作"""
    
    def __init__(self, db_path: str = "db/tasks.json"):
        self.db_path = db_path
        self._lock = threading.Lock()
        
        # 队列机制：所有IO操作通过队列按时间戳排序执行
        self._operation_queue = queue.PriorityQueue()
        self._queue_thread = None
        self._queue_running = False
        self._queue_counter = 0  # 用于生成优先级
        
        self._ensure_db_exists()
        self._start_queue_processor()
    
    def _start_queue_processor(self):
        """启动队列处理线程"""
        if not self._queue_running:
            self._queue_running = True
            self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._queue_thread.start()
            logger.info("任务协调器队列处理线程已启动")
    
    def _process_queue(self):
        """队列处理线程函数"""
        while self._queue_running:
            try:
                # 从队列中获取操作（阻塞等待）
                priority, timestamp, operation_id, operation_func, args, kwargs, result_event = self._operation_queue.get(timeout=1)
                
                try:
                    # 执行操作
                    result = operation_func(*args, **kwargs)
                    
                    # 设置结果并通知等待的线程
                    result_event.result = result
                    result_event.success = True
                    result_event.set()
                    
                    logger.debug(f"队列操作完成: {operation_id}")
                    
                except Exception as e:
                    # 操作失败，设置错误信息
                    result_event.error = e
                    result_event.success = False
                    result_event.set()
                    
                    logger.error(f"队列操作失败 {operation_id}: {e}")
                
                finally:
                    self._operation_queue.task_done()
                    
            except queue.Empty:
                # 超时，继续循环
                continue
            except Exception as e:
                logger.error(f"队列处理器出错: {e}")
    
    def _queue_operation(self, operation_func, *args, **kwargs):
        """将操作加入队列并等待执行结果"""
        if not self._queue_running:
            # 如果队列未运行，直接执行
            return operation_func(*args, **kwargs)
        
        # 创建结果事件
        result_event = threading.Event()
        result_event.result = None
        result_event.success = False
        result_event.error = None
        
        # 生成操作ID和优先级
        self._queue_counter += 1
        operation_id = f"op_{self._queue_counter}"
        timestamp = datetime.now().timestamp()
        
        # 将操作加入队列（按时间戳排序）
        self._operation_queue.put((
            timestamp,  # 优先级（时间戳）
            timestamp,  # 排序辅助
            operation_id,
            operation_func,
            args,
            kwargs,
            result_event
        ))
        
        # 等待操作完成
        result_event.wait(timeout=30)  # 30秒超时
        
        if result_event.success:
            return result_event.result
        elif hasattr(result_event, 'error') and result_event.error:
            raise result_event.error
        else:
            raise TimeoutError(f"队列操作超时: {operation_id}")
    
    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            # 初始化时直接保存，避免循环依赖
            self._save_data_direct({
                "single_tasks": {},
                "batch_tasks": {},
                "metadata": {
                    "version": "2.0",
                    "created_at": datetime.now().timestamp()
                }
            })
    
    def _load_data_direct(self) -> Dict[str, Any]:
        """直接加载数据库数据（不通过队列）"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "single_tasks": {},
                "batch_tasks": {},
                "metadata": {
                    "version": "2.0",
                    "created_at": datetime.now().timestamp()
                }
            }
    
    def _load_data(self) -> Dict[str, Any]:
        """加载数据库数据（通过队列）"""
        return self._queue_operation(self._load_data_direct)
    
    def _save_data_direct(self, data: Dict[str, Any]):
        """直接保存数据到数据库（不通过队列）"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_data(self, data: Dict[str, Any]):
        """保存数据到数据库（通过队列）"""
        return self._queue_operation(self._save_data_direct, data)
    
    def _create_single_task_direct(self, task_id: str, video_path: str, video_name: str, 
                                  video_duration: float, mode: str = "srt", 
                                  invite_code: str = "", batch_id: Optional[str] = None) -> bool:
        """直接创建单个任务（不通过队列）"""
        data = self._load_data_direct()
        
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
        
        self._save_data_direct(data)
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
        return self._queue_operation(
            self._create_single_task_direct, task_id, video_path, video_name,
            video_duration, mode, invite_code, batch_id
        )
    
    def create_batch_task(self, batch_id: str, single_task_ids: List[str]) -> bool:
        """
        创建批量任务
        
        Args:
            batch_id: 批量任务ID
            single_task_ids: 包含的单个任务ID列表
        
        Returns:
            创建是否成功
        """
        with self._lock:
            data = self._load_data()
            
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
            
            self._save_data(data)
            return True
    
    def _update_task_status_direct(self, task_id: str, status: str, progress: str = "", 
                                  current_step: str = "", error = "UNCHANGED", 
                                  resume_data: Dict[str, Any] = None) -> bool:
        """直接更新任务状态（不通过队列）"""
        data = self._load_data_direct()
        
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
        
        # 更新批量任务状态
        if task["batch_id"]:
            self._update_batch_task_status(data, task["batch_id"])
        
        self._save_data_direct(data)
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
        return self._queue_operation(
            self._update_task_status_direct, task_id, status, progress,
            current_step, error, resume_data
        )
    
    def _update_task_progress_direct(self, task_id: str, progress_percentage: float) -> bool:
        """直接更新任务进度百分比（不通过队列）"""
        data = self._load_data_direct()
        
        if task_id not in data["single_tasks"]:
            return False
        
        task = data["single_tasks"][task_id]
        
        # 初始化prog_bar字段（如果不存在）
        if "prog_bar" not in task:
            task["prog_bar"] = 0
        
        task["prog_bar"] = round(min(100, max(0, progress_percentage)), 1)
        task["updated_at"] = datetime.now().timestamp()
        
        self._save_data_direct(data)
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
        return self._queue_operation(self._update_task_progress_direct, task_id, progress_percentage)
    
    def _update_batch_task_status(self, data: Dict[str, Any], batch_id: str):
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
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务信息"""
        data = self._load_data()
        return data["single_tasks"].get(task_id)
    
    def get_batch_task(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批量任务信息"""
        data = self._load_data()
        return data["batch_tasks"].get(batch_id)
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """获取所有任务信息"""
        return self._load_data()
    
    def get_incomplete_tasks(self) -> List[Dict[str, Any]]:
        """获取所有未完成的任务"""
        data = self._load_data()
        incomplete_tasks = []
        
        for task_id, task in data["single_tasks"].items():
            if task["status"] not in ["已完成", "过期文件已经被清理", "被下载过进入清理倒计时"]:
                incomplete_tasks.append(task)
        
        return incomplete_tasks
    
    def get_expired_tasks(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取过期的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        
        Returns:
            过期任务列表
        """
        with self._lock:
            data = self._load_data()
            expired_tasks = []
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for task_id, task in data["single_tasks"].items():
                # 检查已下载的任务是否过期
                if (task["status"] == "被下载过进入清理倒计时" and 
                    current_time - task["updated_at"] > max_age_seconds):
                    expired_tasks.append(task)
                # 检查已完成但长时间未下载的任务
                elif (task["status"] == "已完成" and 
                      current_time - task["updated_at"] > max_age_seconds * 2):
                    expired_tasks.append(task)
            
            return expired_tasks
    
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
        with self._lock:
            data = self._load_data()
            
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
            self._save_data(data)
            return True
    
    def get_task_count_by_status(self) -> Dict[str, int]:
        """获取各状态任务数量统计"""
        with self._lock:
            data = self._load_data()
            status_count = {}
            
            for task in data["single_tasks"].values():
                status = task["status"]
                status_count[status] = status_count.get(status, 0) + 1
            
            return status_count
    
    def get_cleanable_database_tasks(self, cleanup_delay_seconds: int = 320) -> List[Dict[str, Any]]:
        """
        获取可从数据库清理的任务
        
        Args:
            cleanup_delay_seconds: 状态为'过期文件已经被清理'后的等待清理时间（秒）
        
        Returns:
            可清理的任务列表
        """
        with self._lock:
            data = self._load_data()
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
    
    def permanently_delete_task(self, task_id: str) -> bool:
        """
        永久删除任务记录（仅用于数据库健康维护）
        
        Args:
            task_id: 任务ID
            
        Returns:
            删除是否成功
        """
        # 重用现有的delete_task方法，确保逻辑一致
        return self.delete_task(task_id)


# 全局任务协调器实例
task_coordinator = TaskCoordinator()
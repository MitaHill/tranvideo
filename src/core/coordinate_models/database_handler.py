"""
数据库处理器
负责所有数据库的底层操作，包括读写、队列管理等
"""

import json
import os
import threading
import queue
from datetime import datetime
from typing import Dict, Any
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.logger import get_cached_logger

logger = get_cached_logger("数据库处理器")


class DatabaseHandler:
    """数据库处理器，负责统一管理tasks.json的所有IO操作"""
    
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
                    
                    
                except Exception as e:
                    # 操作失败，设置错误信息
                    result_event.error = e
                    result_event.success = False
                    result_event.set()
                    
                    logger.error(f"数据库队列操作失败 {operation_id}: {e}")
                
                finally:
                    self._operation_queue.task_done()
                    
            except queue.Empty:
                # 超时，继续循环
                continue
            except Exception as e:
                logger.error(f"数据库队列处理器出错: {e}")
    
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
        operation_id = f"db_op_{self._queue_counter}"
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
            raise TimeoutError(f"数据库队列操作超时: {operation_id}")
    
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
    
    def load_data(self) -> Dict[str, Any]:
        """加载数据库数据（通过队列）"""
        return self._queue_operation(self._load_data_direct)
    
    def _save_data_direct(self, data: Dict[str, Any]):
        """直接保存数据到数据库（不通过队列）"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_data(self, data: Dict[str, Any]):
        """保存数据到数据库（通过队列）"""
        return self._queue_operation(self._save_data_direct, data)
    
    def stop_queue_processor(self):
        """停止队列处理器"""
        if self._queue_running:
            self._queue_running = False
            if self._queue_thread and self._queue_thread.is_alive():
                self._queue_thread.join(timeout=5)
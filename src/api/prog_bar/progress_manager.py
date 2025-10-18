"""
进度管理器
负责统一管理任务进度更新
"""

import threading
import time
from typing import Dict, Optional
from ...core.coordinate import task_coordinator
from ...utils.logger import get_cached_logger

logger = get_cached_logger("进度管理器")

class ProgressManager:
    """进度管理器"""
    
    def __init__(self):
        self.active_tasks = {}  # {task_id: progress_info}
        self.lock = threading.Lock()
        self.running = False
        self.update_thread = None
        
    def start_tracking(self, task_id: str):
        """开始跟踪任务进度"""
        with self.lock:
            if task_id not in self.active_tasks:
                self.active_tasks[task_id] = {
                    'whisper_progress': 0,
                    'translation_progress': 0,
                    'current_stage': 'pending',
                    'overall_progress': 0
                }
                logger.info(f"开始跟踪任务进度: {task_id[:8]}...")
    
    def stop_tracking(self, task_id: str):
        """停止跟踪任务进度"""
        with self.lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.info(f"停止跟踪任务进度: {task_id[:8]}...")
    
    def update_whisper_progress(self, task_id: str, progress: float):
        """更新Whisper进度 (0-100)"""
        with self.lock:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['whisper_progress'] = min(100, max(0, progress))
                self.active_tasks[task_id]['current_stage'] = 'extracting'
                self._calculate_overall_progress(task_id)
    
    def update_translation_progress(self, task_id: str, progress: float):
        """更新翻译进度 (0-100)"""
        with self.lock:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]['translation_progress'] = min(100, max(0, progress))
                self.active_tasks[task_id]['current_stage'] = 'translating'
                self._calculate_overall_progress(task_id)
    
    def _calculate_overall_progress(self, task_id: str):
        """计算总体进度"""
        if task_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[task_id]
        stage = task_info['current_stage']
        
        if stage == 'pending':
            overall = 0
        elif stage == 'extracting':
            # 提取阶段占50%
            overall = task_info['whisper_progress'] * 0.5
        elif stage == 'translating':
            # 提取完成(50%) + 翻译进度(50%)
            overall = 50 + task_info['translation_progress'] * 0.5
        elif stage == 'completed':
            overall = 100
        else:
            overall = 0
        
        task_info['overall_progress'] = round(overall, 1)
        
        # 同步到数据库
        try:
            task_coordinator.update_task_progress(task_id, overall)
        except Exception as e:
            logger.warning(f"更新任务进度到数据库失败: {e}")
    
    def set_stage_completed(self, task_id: str, stage: str):
        """标记某阶段完成"""
        with self.lock:
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                
                if stage == 'extracting':
                    task_info['whisper_progress'] = 100
                    task_info['current_stage'] = 'translating'
                elif stage == 'translating':
                    task_info['translation_progress'] = 100
                    task_info['current_stage'] = 'completed'
                
                self._calculate_overall_progress(task_id)
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """获取任务进度信息"""
        with self.lock:
            return self.active_tasks.get(task_id, None)
    
    def get_all_progress(self) -> Dict:
        """获取所有任务进度"""
        with self.lock:
            return self.active_tasks.copy()

# 全局进度管理器实例
progress_manager = ProgressManager()
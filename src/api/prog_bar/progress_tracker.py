"""
进度跟踪器
用于监控Whisper和翻译程序的实时进度
"""

import threading
import time
import re
import subprocess
import queue
import os
import io
from typing import Optional, Callable
from .progress_manager import progress_manager
from ...utils.logger import get_cached_logger

logger = get_cached_logger("进度跟踪器")

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self):
        self.active_trackers = {}  # {task_id: tracker_info}
        self.lock = threading.Lock()
        self.console_monitors = {}  # {task_id: console_monitor_info}
        
        # Whisper进度解析正则（匹配百分比和frames/s）
        self.whisper_patterns = [
            re.compile(r'(\d+)%\|[█▏▎▍▌▋▊▉\s]*\|\s*\d+/\d+\s*\[.*?\].*?frames/s'),
            re.compile(r'(\d+)%\|.*?frames/s'),
            re.compile(r'(\d+)%\|')
        ]
        
        # 翻译进度解析正则（匹配"翻译进度"和s/it）
        self.translation_patterns = [
            re.compile(r'翻译进度:\s*(\d+)%\|.*?\|\s*(\d+)/(\d+)\s*\[.*?\].*?s/it'),
            re.compile(r'翻译进度:\s*(\d+)%.*?s/it'),
            re.compile(r'翻译进度:\s*(\d+)%')
        ]
    
    def start_whisper_tracking(self, task_id: str, log_callback: Optional[Callable] = None):
        """开始跟踪Whisper进度"""
        with self.lock:
            if task_id not in self.active_trackers:
                self.active_trackers[task_id] = {
                    'whisper_thread': None,
                    'translation_thread': None,
                    'whisper_progress': 0,
                    'translation_progress': 0
                }
            
            # 启动进度管理器跟踪
            progress_manager.start_tracking(task_id)
            
            # 创建Whisper进度监控线程
            tracker_thread = threading.Thread(
                target=self._monitor_whisper_progress,
                args=(task_id, log_callback),
                daemon=True
            )
            tracker_thread.start()
            self.active_trackers[task_id]['whisper_thread'] = tracker_thread
            
            logger.info(f"开始跟踪Whisper进度: {task_id[:8]}...")
    
    def start_translation_tracking(self, task_id: str, log_callback: Optional[Callable] = None):
        """开始跟踪翻译进度"""
        with self.lock:
            if task_id in self.active_trackers:
                # 标记Whisper阶段完成
                progress_manager.set_stage_completed(task_id, 'extracting')
                
                # 创建翻译进度监控线程
                tracker_thread = threading.Thread(
                    target=self._monitor_translation_progress,
                    args=(task_id, log_callback),
                    daemon=True
                )
                tracker_thread.start()
                self.active_trackers[task_id]['translation_thread'] = tracker_thread
                
                logger.info(f"开始跟踪翻译进度: {task_id[:8]}...")
    
    def stop_tracking(self, task_id: str):
        """停止跟踪任务进度"""
        with self.lock:
            if task_id in self.active_trackers:
                # 标记任务完成
                progress_manager.set_stage_completed(task_id, 'translating')
                progress_manager.stop_tracking(task_id)
                
                # 清理跟踪器
                del self.active_trackers[task_id]
                logger.info(f"停止跟踪任务进度: {task_id[:8]}...")
    
    def _monitor_whisper_progress(self, task_id: str, log_callback: Optional[Callable] = None):
        """监控Whisper进度的线程函数"""
        try:
            logger.info(f"开始监控Whisper控制台输出: {task_id[:8]}...")
            
            # 监控控制台输出，解析进度信息
            while task_id in self.active_trackers:
                try:
                    # 检查是否有控制台监控器
                    if task_id in self.console_monitors and 'whisper_output' in self.console_monitors[task_id]:
                        output_queue = self.console_monitors[task_id]['whisper_output']
                        
                        # 尝试获取输出行（非阻塞）
                        try:
                            line = output_queue.get_nowait()
                            self._parse_whisper_progress(task_id, line)
                        except queue.Empty:
                            pass
                    
                    time.sleep(0.1)  # 减少CPU使用率
                    
                except Exception as e:
                    logger.warning(f"Whisper进度监控循环出错: {e}")
                    time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Whisper进度监控线程出错: {e}")
    
    def _monitor_translation_progress(self, task_id: str, log_callback: Optional[Callable] = None):
        """监控翻译进度的线程函数"""
        try:
            logger.info(f"开始监控翻译控制台输出: {task_id[:8]}...")
            
            # 监控控制台输出，解析翻译进度
            while task_id in self.active_trackers:
                try:
                    # 检查是否有控制台监控器
                    if task_id in self.console_monitors and 'translation_output' in self.console_monitors[task_id]:
                        output_queue = self.console_monitors[task_id]['translation_output']
                        
                        # 尝试获取输出行（非阻塞）
                        try:
                            line = output_queue.get_nowait()
                            self._parse_translation_progress(task_id, line)
                        except queue.Empty:
                            pass
                    
                    time.sleep(0.1)  # 减少CPU使用率
                    
                except Exception as e:
                    logger.warning(f"翻译进度监控循环出错: {e}")
                    time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"翻译进度监控线程出错: {e}")
    
    def _parse_whisper_progress(self, task_id: str, log_line: str):
        """解析Whisper进度输出行并实现旁路输出"""
        try:
            # 先将Whisper进度输出重新打印到控制台（旁路结构）
            if any(keyword in log_line for keyword in ['%|', 'frames/s']):
                print(f"\r{log_line}", end='', flush=True)  # \r实现进度条覆盖效果
            
            # 使用正则模式匹配Whisper进度
            for pattern in self.whisper_patterns:
                match = pattern.search(log_line)
                if match:
                    percentage = int(match.group(1))
                    
                    # 确保进度值合理
                    if 0 <= percentage <= 100:
                        # Whisper进度直接传递，progress_manager会自动计算总进度
                        progress_manager.update_whisper_progress(task_id, percentage)
                        logger.debug(f"解析Whisper进度: {task_id[:8]}... -> {percentage}%")
                        return
            
        except Exception as e:
            logger.warning(f"解析Whisper进度失败: {e}")
    
    def _parse_translation_progress(self, task_id: str, log_line: str):
        """解析翻译进度输出行并实现旁路输出"""
        try:
            # 先将翻译进度输出重新打印到控制台（旁路结构）
            if any(keyword in log_line for keyword in ['翻译进度', '%|', 's/it']):
                print(f"\r{log_line}", end='', flush=True)  # \r实现进度条覆盖效果
            
            # 使用正则模式匹配翻译进度
            for pattern in self.translation_patterns:
                match = pattern.search(log_line)
                if match:
                    percentage = int(match.group(1))
                    
                    # 确保进度值合理
                    if 0 <= percentage <= 100:
                        # 翻译进度直接传递，progress_manager会自动计算总进度
                        progress_manager.update_translation_progress(task_id, percentage)
                        logger.debug(f"解析翻译进度: {task_id[:8]}... -> {percentage}%")
                        return
            
        except Exception as e:
            logger.warning(f"解析翻译进度失败: {e}")
    
    def setup_console_monitor(self, task_id: str, whisper_process=None, translation_process=None):
        """设置控制台输出监控器"""
        with self.lock:
            if task_id not in self.console_monitors:
                self.console_monitors[task_id] = {}
            
            if whisper_process:
                # 创建Whisper输出队列
                whisper_queue = queue.Queue()
                self.console_monitors[task_id]['whisper_output'] = whisper_queue
                
                # 启动Whisper输出读取线程
                whisper_reader = threading.Thread(
                    target=self._read_process_output,
                    args=(whisper_process, whisper_queue, f"Whisper-{task_id[:8]}"),
                    daemon=True
                )
                whisper_reader.start()
                self.console_monitors[task_id]['whisper_reader'] = whisper_reader
            
            if translation_process:
                # 创建翻译输出队列
                translation_queue = queue.Queue()
                self.console_monitors[task_id]['translation_output'] = translation_queue
                
                # 启动翻译输出读取线程
                translation_reader = threading.Thread(
                    target=self._read_process_output,
                    args=(translation_process, translation_queue, f"Translation-{task_id[:8]}"),
                    daemon=True
                )
                translation_reader.start()
                self.console_monitors[task_id]['translation_reader'] = translation_reader
    
    def _read_process_output(self, process, output_queue, name):
        """读取进程输出的线程函数"""
        try:
            logger.info(f"开始读取{name}进程输出")
            
            # 读取进程输出
            for line in iter(process.stdout.readline, b''):
                try:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        output_queue.put(line_str)
                        logger.debug(f"{name}输出: {line_str}")
                except Exception as e:
                    logger.warning(f"处理{name}输出行失败: {e}")
            
            logger.info(f"{name}进程输出读取完成")
            
        except Exception as e:
            logger.error(f"读取{name}进程输出失败: {e}")
    
    def cleanup_console_monitor(self, task_id: str):
        """清理控制台监控器"""
        with self.lock:
            if task_id in self.console_monitors:
                logger.info(f"清理任务控制台监控器: {task_id[:8]}...")
                del self.console_monitors[task_id]
    
    def update_translation_progress_from_count(self, task_id: str, current: int, total: int):
        """从翻译计数更新进度"""
        try:
            if total > 0:
                percentage = (current / total) * 100
                progress_manager.update_translation_progress(task_id, percentage)
                logger.debug(f"翻译进度: {task_id[:8]}... -> {current}/{total} ({percentage:.1f}%)")
        except Exception as e:
            logger.warning(f"更新翻译进度失败: {e}")

# 全局进度跟踪器实例
progress_tracker = ProgressTracker()
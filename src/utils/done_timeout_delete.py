import os
import time
import threading
from datetime import datetime
from ..core.coordinate import task_coordinator

# 简单日志函数
def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")


class TimeoutCleaner:
    def __init__(self, cache_dirs, timeout_hours=24):
        self.cache_dirs = cache_dirs
        self.timeout_hours = timeout_hours
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        """启动清理线程"""
        if self.running:
            return

        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        print(f"[INFO] 文件清理线程已启动，超时: {self.timeout_hours}小时")

    def stop(self):
        """停止清理线程"""
        if not self.running:
            return

        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        print("[INFO] 文件清理线程已停止")

    def _cleanup_loop(self):
        """清理循环"""
        while not self.stop_event.wait(1):  # 每1秒检查一次
            try:
                self._check_and_clean()
            except Exception as e:
                print(f"[ERROR] 文件清理异常: {e}")

    def _check_and_clean(self):
        """检查并清理超时文件，优先通过任务协调器处理"""
        try:
            # 首先通过任务协调器检查过期任务
            self._clean_expired_tasks()
            
            # 检查并清理长期未下载的任务（3天）
            self._clean_long_term_undownloaded_tasks()
            
            # 然后清理孤立的文件（不在任务数据库中的文件）
            self._clean_orphaned_files()
            
            # 最后进行数据库健康维护
            self._maintain_database_health()
            
        except Exception as e:
            log_error(f"清理过程出现异常: {e}")
    
    def _clean_expired_tasks(self):
        """通过任务协调器清理过期任务"""
        try:
            # 获取过期任务列表
            expired_tasks = task_coordinator.get_expired_tasks(self.timeout_hours)
            
            if not expired_tasks:
                return
            
            log_info(f"发现 {len(expired_tasks)} 个过期任务需要清理")
            
            for task in expired_tasks:
                task_id = task['task_id']
                
                try:
                    # 标记任务为已清理状态
                    task_coordinator.mark_task_expired(task_id)
                    
                    # 清理任务相关文件
                    self._clean_task_files(task_id, task)
                    
                    log_info(f"任务 {task_id} 已清理完成")
                    
                except Exception as e:
                    log_error(f"清理任务 {task_id} 失败: {e}")
        
        except Exception as e:
            log_error(f"获取过期任务失败: {e}")
    
    def _clean_long_term_undownloaded_tasks(self):
        """
        清理长期未下载的任务（连续3天未下载）
        
        清理流程：
        1. 检测状态为"已完成"且超过3天未下载的任务
        2. 先标记任务状态为"过期文件已经被清理" 
        3. 删除所有相关文件
        4. 等待320秒后由数据库健康维护删除任务记录
        """
        try:
            # 获取长期未下载的任务列表
            undownloaded_tasks = task_coordinator.get_long_term_undownloaded_tasks(3)
            
            if not undownloaded_tasks:
                return
            
            log_info(f"发现 {len(undownloaded_tasks)} 个长期未下载任务需要清理")
            
            for task in undownloaded_tasks:
                task_id = task['task_id']
                
                try:
                    # 计算已完成多少天
                    current_time = datetime.now().timestamp()
                    days_since_completion = (current_time - task["updated_at"]) / (24 * 3600)
                    
                    log_info(f"清理长期未下载任务 {task_id}（已完成 {days_since_completion:.1f} 天未下载）")
                    
                    # 标记任务为已清理状态
                    task_coordinator.mark_task_expired(task_id)
                    
                    # 清理任务相关文件
                    self._clean_task_files(task_id, task)
                    
                    log_info(f"长期未下载任务 {task_id} 已清理完成")
                    
                except Exception as e:
                    log_error(f"清理长期未下载任务 {task_id} 失败: {e}")
        
        except Exception as e:
            log_error(f"获取长期未下载任务失败: {e}")
    
    def _clean_task_files(self, task_id: str, task: dict):
        """清理特定任务的文件和目录"""
        files_to_clean = []
        dirs_to_clean = []
        
        # 添加视频文件
        if 'video_path' in task and os.path.exists(task['video_path']):
            files_to_clean.append(task['video_path'])
        
        # 添加输出文件
        output_patterns = [
            f"cache/outputs/{task_id}_translated.srt",
            f"cache/outputs/{task_id}_final.mp4", 
            f"cache/outputs/{task_id}_output.mp4",
            f"cache/temp/{task_id}_raw.srt",
            f"cache/temp/{task_id}_original.srt",
            f"cache/temp/{task_id}_translated.srt"
        ]
        
        for pattern in output_patterns:
            if os.path.exists(pattern):
                files_to_clean.append(pattern)
        
        # 添加任务ID目录及其内所有文件
        task_temp_dir = f"cache/temp/{task_id}"
        if os.path.exists(task_temp_dir) and os.path.isdir(task_temp_dir):
            dirs_to_clean.append(task_temp_dir)
        
        # 删除文件
        for file_path in files_to_clean:
            try:
                os.remove(file_path)
                log_info(f"删除任务文件: {file_path}")
            except OSError as e:
                log_error(f"删除文件失败 {file_path}: {e}")
        
        # 删除目录（递归删除）
        for dir_path in dirs_to_clean:
            try:
                import shutil
                shutil.rmtree(dir_path)
                log_info(f"删除任务目录: {dir_path}")
            except OSError as e:
                log_error(f"删除目录失败 {dir_path}: {e}")
    
    def _clean_orphaned_files(self):
        """清理孤立的文件（原有逻辑的改进版）"""
        current_time = time.time()
        timeout_seconds = self.timeout_hours * 3600

        for dir_name, dir_path in self.cache_dirs.items():
            if not os.path.exists(dir_path):
                continue

            try:
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)

                    if not os.path.isfile(file_path):
                        continue

                    # 获取文件修改时间
                    file_mtime = os.path.getmtime(file_path)
                    time_diff = current_time - file_mtime

                    # 检查是否超时
                    if time_diff > timeout_seconds:
                        # 检查文件是否属于活跃任务
                        if not self._is_file_in_active_tasks(file_path):
                            try:
                                os.remove(file_path)
                                hours_old = time_diff / 3600
                                log_info(f"删除孤立超时文件: {file_path} (存在{hours_old:.1f}小时)")
                            except OSError as e:
                                log_error(f"删除孤立文件失败 {file_path}: {e}")

            except OSError as e:
                log_error(f"访问目录失败 {dir_path}: {e}")
    
    def _is_file_in_active_tasks(self, file_path: str) -> bool:
        """检查文件是否属于活跃任务"""
        try:
            all_tasks = task_coordinator.get_all_tasks()
            
            for task_id, task in all_tasks['single_tasks'].items():
                # 检查是否是任务的视频文件或输出文件
                if (task.get('video_path') == file_path or 
                    file_path.find(task_id) != -1):
                    # 如果任务状态不是已清理，则认为文件是活跃的
                    return task['status'] != '过期文件已经被清理'
            
            return False
        except Exception:
            # 出错时保守处理，认为文件是活跃的
            return True

    def _maintain_database_health(self):
        """数据库健康维护：清理状态为'过期文件已经被清理'且文件不存在的任务记录"""
        try:
            # 获取可从数据库清理的任务（等待320秒）
            cleanable_tasks = task_coordinator.get_cleanable_database_tasks(320)
            
            if not cleanable_tasks:
                return
            
            log_info(f"发现 {len(cleanable_tasks)} 个可从数据库清理的任务记录")
            
            for task in cleanable_tasks:
                task_id = task['task_id']
                
                try:
                    # 验证相关文件是否确实不存在
                    if self._verify_task_files_cleaned(task_id, task):
                        # 从数据库中永久删除任务记录
                        success = task_coordinator.permanently_delete_task(task_id)
                        
                        if success:
                            log_info(f"数据库健康维护: 已删除任务记录 {task_id}")
                        else:
                            log_warning(f"删除任务记录失败: {task_id}")
                    else:
                        log_warning(f"任务 {task_id} 仍有文件存在，跳过数据库清理")
                        
                except Exception as e:
                    log_error(f"数据库健康维护失败 {task_id}: {e}")
        
        except Exception as e:
            log_error(f"数据库健康维护过程异常: {e}")
    
    def _verify_task_files_cleaned(self, task_id: str, task: dict) -> bool:
        """验证任务相关的所有文件和目录都已被清理"""
        # 检查视频文件
        if 'video_path' in task and os.path.exists(task['video_path']):
            return False
        
        # 检查所有可能的输出文件
        file_patterns = [
            f"cache/outputs/{task_id}_translated.srt",
            f"cache/outputs/{task_id}_final.mp4",
            f"cache/outputs/{task_id}_output.mp4",
            f"cache/temp/{task_id}_raw.srt",
            f"cache/temp/{task_id}_original.srt",
            f"cache/temp/{task_id}_translated.srt"
        ]
        
        for pattern in file_patterns:
            if os.path.exists(pattern):
                return False
        
        # 检查任务ID目录
        task_temp_dir = f"cache/temp/{task_id}"
        if os.path.exists(task_temp_dir):
            return False
        
        # 检查批量任务相关文件（如果是批量任务的一部分）
        if task.get('batch_id'):
            batch_zip = f"cache/outputs/{task['batch_id']}_batch.zip"
            if os.path.exists(batch_zip):
                # 批量文件还存在，不清理数据库记录
                return False
        
        return True

    def set_timeout(self, hours):
        """设置超时时间"""
        self.timeout_hours = hours
        print(f"[INFO] 文件清理超时时间已设置为: {hours}小时")


def start_timeout_cleaner(cache_dirs, timeout_hours=24):
    """启动超时清理器"""
    cleaner = TimeoutCleaner(cache_dirs, timeout_hours)
    cleaner.start()
    return cleaner


def create_timeout_cleaner(cache_dirs, timeout_hours=24):
    """创建超时清理器实例"""
    return TimeoutCleaner(cache_dirs, timeout_hours)
"""
启动恢复模块
在程序启动时检查并恢复未完成的任务
"""

import os
import asyncio
import time
from typing import List, Dict, Any
from ..core.coordinate import task_coordinator

# 简单日志函数
def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")


class StartupTaskResumer:
    """启动时任务恢复器"""
    
    def __init__(self):
        self.startup_completed = False
        self.startup_time = None

    async def resume_incomplete_tasks(self):
        """恢复未完成的任务并将它们重新加入队列"""
        try:
            self.startup_time = time.time()
            log_info("=== 启动任务恢复开始 ===")
            log_info("正在检查未完成的任务...")
            
            incomplete_tasks = task_coordinator.get_incomplete_tasks()
            
            if not incomplete_tasks:
                log_info("没有发现未完成的任务")
                self.startup_completed = True
                return
            
            log_info(f"发现 {len(incomplete_tasks)} 个未完成的任务，开始恢复处理...")
            
            # 按任务创建时间排序
            incomplete_tasks.sort(key=lambda x: x['created_at'])
            
            # 恢复任务状态和数据
            recovery_count = 0
            for task in incomplete_tasks:
                if self._recover_single_task(task):
                    recovery_count += 1
            
            log_info(f"任务恢复完成！成功恢复 {recovery_count}/{len(incomplete_tasks)} 个任务")
            log_info("=== 启动任务恢复完成 ===")
            
            self.startup_completed = True
            
        except Exception as e:
            log_error(f"恢复未完成任务时出错: {str(e)}")
            self.startup_completed = True

    def _recover_single_task(self, task: Dict[str, Any]) -> bool:
        """恢复单个任务，基于数据库状态进行恢复 - 完全基于数据库状态，不检查文件"""
        task_id = task['task_id']
        status = task['status']
        video_path = task['video_path']
        mode = task.get('mode', 'srt')
        
        try:
            log_info(f"恢复任务 {task_id[:8]}...，当前数据库状态: {status}")
            
            # 检查原始视频文件
            if not os.path.exists(video_path):
                log_error(f"任务 {task_id[:8]}... 的视频文件不存在: {video_path}")
                task_coordinator.update_task_status(
                    task_id, 
                    "failed", 
                    "视频文件不存在", 
                    "failed", 
                    error="视频文件不存在"
                )
                return False
            
            # 定义工作文件路径（仅用于清理，不用于状态检测）
            raw_srt = f"cache/temp/{task_id}_raw.srt"
            translated_srt = f"cache/outputs/{task_id}_translated.srt"
            
            # 严格根据数据库状态清理不完整的文件，不修改任务状态
            if status == "提取原文字幕":
                # 在提取阶段中断，删除可能不完整的raw文件
                if os.path.exists(raw_srt):
                    log_info(f"  清理中断阶段的原文字幕文件: {raw_srt}")
                    try:
                        os.remove(raw_srt)
                    except:
                        pass
                log_info(f"  ✅ 任务将从提取原文字幕阶段继续（保持数据库状态: {status}）")
                
            elif status == "翻译原文字幕":
                # 在翻译阶段中断，删除可能不完整的翻译文件
                if os.path.exists(translated_srt):
                    log_info(f"  清理中断阶段的翻译字幕文件: {translated_srt}")
                    try:
                        os.remove(translated_srt)
                    except:
                        pass
                log_info(f"  ✅ 任务将从翻译原文字幕阶段继续（保持数据库状态: {status}）")
                
            elif status in ["队列中", "processing"]:
                log_info(f"  ✅ 任务将从头开始处理（保持数据库状态: {status}）")
            elif status == "已完成":
                log_info(f"  ✅ 任务已完成，无需恢复（保持数据库状态: {status}）")
                return True
            else:
                log_info(f"  ⚠️  未知状态，将从头处理（保持数据库状态: {status}）")
            
            # 绝对不修改任务状态！保持数据库中的状态，让处理函数根据状态正确恢复
            log_info(f"  ➡️  任务 {task_id[:8]}... 恢复完成，保持数据库状态: {status}，等待主处理循环调度")
            
            return True
            
        except Exception as e:
            log_error(f"恢复任务 {task_id[:8]}... 时出错: {str(e)}")
            return False
    
    
    def is_startup_completed(self) -> bool:
        """检查启动检查是否已完成"""
        return self.startup_completed
        
    def get_startup_time(self) -> float:
        """获取启动时间"""
        return self.startup_time or 0
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dir = "cache/temp"
            if os.path.exists(temp_dir):
                cleaned_count = 0
                for file in os.listdir(temp_dir):
                    if file.endswith(('.srt', '.tmp')):
                        file_path = os.path.join(temp_dir, file)
                        # 检查文件是否超过1小时没有修改
                        if os.path.getctime(file_path) < (time.time() - 3600):
                            os.remove(file_path)
                            cleaned_count += 1
                if cleaned_count > 0:
                    log_info(f"清理了 {cleaned_count} 个临时文件")
        except Exception as e:
            log_error(f"清理临时文件时出错: {str(e)}")


# 全局启动任务检查器实例
startup_resumer = StartupTaskResumer()
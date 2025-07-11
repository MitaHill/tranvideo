import os
import time
import threading
from datetime import datetime


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
        """检查并清理超时文件"""
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
                        try:
                            os.remove(file_path)
                            hours_old = time_diff / 3600
                            print(f"[INFO] 删除超时文件: {file_path} (存在{hours_old:.1f}小时)")
                        except OSError as e:
                            print(f"[ERROR] 删除文件失败 {file_path}: {e}")

            except OSError as e:
                print(f"[ERROR] 访问目录失败 {dir_path}: {e}")

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
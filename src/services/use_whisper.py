import requests
import subprocess
import sys
import os
import time
import threading
import signal
import psutil
from threading import Timer

# Whisper服务配置
WHISPER_SERVICE_URL = "http://127.0.0.1:5001"

# 全局变量
log_cleanup_timer = None
whisper_process = None


def cleanup_logs():
    """调用log-ctl.py清理日志"""
    try:
        subprocess.run([sys.executable, 'log-ctl.py', 'cleanup', 'log', '2'],
                       timeout=30, capture_output=True)
    except Exception as e:
        print(f"日志清理失败: {e}")


def schedule_log_cleanup():
    """定时调用日志清理"""
    global log_cleanup_timer
    cleanup_logs()
    log_cleanup_timer = Timer(30.0, schedule_log_cleanup)
    log_cleanup_timer.daemon = True
    log_cleanup_timer.start()


def check_whisper_service():
    """检查 Whisper 服务是否可用"""
    try:
        response = requests.get(f"{WHISPER_SERVICE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def call_whisper_service(video_path):
    """调用 Whisper 服务进行转录"""
    try:
        response = requests.post(
            f"{WHISPER_SERVICE_URL}/transcribe_video",
            json={"video_path": video_path},
            timeout=600  # 10分钟超时
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"Whisper 服务调用失败: {str(e)}")


def format_srt(segments):
    """格式化为SRT字幕"""

    def format_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()
        srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
    return srt_content


def kill_existing_whisper_processes():
    """杀死现有的 Whisper 进程"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('whisper_service.py' in arg for arg in cmdline):
                    print(f"[INFO] 终止现有 Whisper 进程: PID {proc.info['pid']}")
                    proc.terminate()
                    proc.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass
    except Exception as e:
        print(f"[WARNING] 清理现有进程时出错: {e}")


def start_whisper_service():
    """启动 Whisper 服务"""
    global whisper_process

    try:
        # 首先检查服务是否已经运行
        if check_whisper_service():
            print("[INFO] Whisper 服务已在运行")
            return True

        # 清理可能存在的僵尸进程
        kill_existing_whisper_processes()
        time.sleep(2)

        print("[INFO] 启动 Whisper 服务...")

        # 启动新的 Whisper 服务进程
        whisper_service_path = "src/services/whisper_service.py"
        if not os.path.exists(whisper_service_path):
            print(f"[ERROR] Whisper 服务文件不存在: {whisper_service_path}")
            return False

        whisper_process = subprocess.Popen(
            [sys.executable, whisper_service_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )

        print(f"[INFO] Whisper 服务进程已启动，PID: {whisper_process.pid}")

        # 等待服务启动
        for i in range(60):  # 增加等待时间到60秒
            if check_whisper_service():
                print("[INFO] Whisper 服务启动成功")
                # 启动日志清理
                schedule_log_cleanup()
                return True
            time.sleep(1)

        print("[ERROR] Whisper 服务启动超时")

        # 如果启动失败，尝试读取错误信息
        if whisper_process and whisper_process.poll() is not None:
            stdout, stderr = whisper_process.communicate(timeout=5)
            print(f"[ERROR] Whisper 服务启动失败:")
            print(f"STDOUT: {stdout.decode('utf-8')}")
            print(f"STDERR: {stderr.decode('utf-8')}")

        return False

    except Exception as e:
        print(f"[ERROR] 启动 Whisper 服务失败: {e}")
        return False


def stop_whisper_service():
    """停止 Whisper 服务"""
    global whisper_process

    try:
        # 先尝试优雅停止
        try:
            response = requests.post(f"{WHISPER_SERVICE_URL}/shutdown", timeout=10)
            if response.status_code == 200:
                print("[INFO] Whisper 服务已优雅停止")
                return True
        except:
            pass

        # 如果有进程句柄，直接终止
        if whisper_process and whisper_process.poll() is None:
            print(f"[INFO] 终止 Whisper 进程: PID {whisper_process.pid}")
            whisper_process.terminate()
            try:
                whisper_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                whisper_process.kill()
            whisper_process = None

        # 清理所有相关进程
        kill_existing_whisper_processes()

        print("[INFO] Whisper 服务已停止")
        return True

    except Exception as e:
        print(f"[ERROR] 停止 Whisper 服务时出错: {e}")
        return False


def get_whisper_status():
    """获取 Whisper 服务状态信息"""
    try:
        response = requests.get(f"{WHISPER_SERVICE_URL}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unavailable", "error": "Service not responding"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def restart_whisper_service():
    """重启 Whisper 服务"""
    print("[INFO] 重启 Whisper 服务...")
    stop_whisper_service()
    time.sleep(3)
    return start_whisper_service()


def stop_log_cleanup():
    """停止日志清理定时器"""
    global log_cleanup_timer
    if log_cleanup_timer:
        log_cleanup_timer.cancel()
        log_cleanup_timer = None
        print("[INFO] 日志清理定时器已停止")


class WhisperServiceManager:
    """Whisper服务管理器"""

    def __init__(self, service_url=None):
        self.service_url = service_url or WHISPER_SERVICE_URL
        self.log_timer = None

    def start_service(self):
        """启动服务"""
        return start_whisper_service()

    def stop_service(self):
        """停止服务"""
        return stop_whisper_service()

    def restart_service(self):
        """重启服务"""
        return restart_whisper_service()

    def check_health(self):
        """检查服务健康状态"""
        return check_whisper_service()

    def get_status(self):
        """获取服务状态"""
        return get_whisper_status()

    def transcribe(self, video_path):
        """转录视频"""
        return call_whisper_service(video_path)

    def start_log_cleanup(self):
        """启动日志清理"""
        schedule_log_cleanup()

    def stop_log_cleanup(self):
        """停止日志清理"""
        stop_log_cleanup()


# 创建默认实例
whisper_manager = WhisperServiceManager()


def cleanup_on_exit():
    """程序退出时的清理函数"""
    stop_log_cleanup()
    stop_whisper_service()


# 注册退出处理函数
import atexit

atexit.register(cleanup_on_exit)


# 处理信号
def signal_handler(signum, frame):
    print(f"\n[INFO] 收到信号 {signum}，正在清理...")
    cleanup_on_exit()
    sys.exit(0)


if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)
if hasattr(signal, 'SIGINT'):
    signal.signal(signal.SIGINT, signal_handler)

# 导出主要函数供其他模块使用
__all__ = [
    'check_whisper_service',
    'call_whisper_service',
    'format_srt',
    'start_whisper_service',
    'stop_whisper_service',
    'restart_whisper_service',
    'get_whisper_status',
    'schedule_log_cleanup',
    'stop_log_cleanup',
    'cleanup_logs',
    'WhisperServiceManager',
    'whisper_manager'
]
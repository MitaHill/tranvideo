import subprocess
import sys
import os
import time
import threading
import signal
from threading import Timer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.logger import get_cached_logger

# 导入直接调用模块
from .whisper_direct import get_whisper_manager, transcribe_video_direct, get_whisper_status

logger = get_cached_logger("Whisper服务管理")

# 全局变量
log_cleanup_timer = None


def cleanup_logs():
    """调用log-ctl.py清理日志"""
    try:
        subprocess.run([sys.executable, 'log-ctl.py', 'cleanup', 'log', '2'],
                       timeout=30, capture_output=True, text=True, encoding='utf-8', errors='replace')
    except Exception as e:
        logger.warning(f"日志清理失败: {e}")


def schedule_log_cleanup():
    """定时调用日志清理"""
    global log_cleanup_timer
    cleanup_logs()
    log_cleanup_timer = Timer(30.0, schedule_log_cleanup)
    log_cleanup_timer.daemon = True
    log_cleanup_timer.start()


def check_whisper_service():
    """检查 Whisper 服务是否可用（改为检查直接调用模块）"""
    try:
        # 对于新的直接调用系统，如果管理器初始化成功就认为可用
        # 不需要检查模型是否已加载，因为采用延迟加载
        manager = get_whisper_manager()
        return True  # 管理器存在即表示服务可用
    except Exception as e:
        logger.error(f"检查Whisper状态失败: {e}")
        return False


def call_whisper_service(video_path, progress_callback=None, task_id=None):
    """调用 Whisper 进行转录（改为直接调用）"""
    try:
        logger.info(f"开始直接转录视频: {video_path}")
        result = transcribe_video_direct(video_path, task_id, progress_callback)
        
        if result.get('success'):
            return result
        else:
            raise Exception(f"转录失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"Whisper 转录失败: {str(e)}")
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


def start_whisper_service():
    """初始化 Whisper 直接调用模块（启动时预加载和预热）"""
    try:
        logger.info("[INFO] 初始化 Whisper 直接调用模块...")

        # 步骤1: 如果是本地Ollama，先卸载Ollama模型释放显存
        try:
            from src.services.tran import load_config
            import requests

            config = load_config()
            translator_type = config.get('translator_type', 'ollama')
            ollama_url = config.get('ollama_api', '')
            ollama_model = config.get('ollama_model', '')

            # 检查是否为本地Ollama
            if translator_type == 'ollama' and ollama_url and ollama_model:
                is_local = any(host in ollama_url.lower() for host in ['127.0.0.1', 'localhost', '::1'])

                if is_local:
                    logger.info(f"[INFO] 检测到本地Ollama ({ollama_url})，启动前先卸载模型...")
                    try:
                        unload_url = f"{ollama_url}/api/generate"
                        payload = {"model": ollama_model, "keep_alive": 0}
                        response = requests.post(unload_url, json=payload, timeout=10)

                        if response.status_code == 200:
                            logger.info(f"[INFO] ✅ Ollama模型 {ollama_model} 已卸载，显存已释放")
                        else:
                            logger.warning(f"[WARN] Ollama卸载请求返回: {response.status_code}")
                    except Exception as e:
                        logger.warning(f"[WARN] 卸载Ollama模型失败(将继续启动): {e}")
                else:
                    logger.info(f"[INFO] 检测到远程Ollama ({ollama_url})，跳过卸载步骤")
        except Exception as e:
            logger.warning(f"[WARN] 检查Ollama配置失败(将继续启动): {e}")

        # 步骤2: 启用预加载模式，立即加载Whisper模型并预热
        manager = get_whisper_manager(preload=True)
        logger.info("[INFO] Whisper 模块已初始化并完成预热")

        # 步骤3: 启动日志清理
        schedule_log_cleanup()
        return True

    except Exception as e:
        logger.error(f"[ERROR] 初始化 Whisper 模块失败: {e}")
        return False


def stop_whisper_service():
    """停止 Whisper 模块（卸载模型）"""
    try:
        logger.info("[INFO] 停止 Whisper 模块...")
        manager = get_whisper_manager()
        manager.unload_model()
        logger.info("[INFO] Whisper 模块已停止")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] 停止 Whisper 模块时出错: {e}")
        return False


def restart_whisper_service():
    """重启 Whisper 模块"""
    logger.info("[INFO] 重启 Whisper 模块...")
    stop_whisper_service()
    time.sleep(1)
    return start_whisper_service()


def stop_log_cleanup():
    """停止日志清理定时器"""
    global log_cleanup_timer
    if log_cleanup_timer:
        log_cleanup_timer.cancel()
        log_cleanup_timer = None
        print("[INFO] 日志清理定时器已停止")


class WhisperServiceManager:
    """Whisper直接调用管理器"""

    def __init__(self):
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

    def transcribe(self, video_path, progress_callback=None):
        """转录视频"""
        return call_whisper_service(video_path, progress_callback)

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
    logger.info(f"\n[INFO] 收到信号 {signum}，正在清理...")
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
    'schedule_log_cleanup',
    'stop_log_cleanup',
    'cleanup_logs',
    'WhisperServiceManager',
    'whisper_manager'
]
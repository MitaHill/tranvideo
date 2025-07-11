from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import threading
import time
from src.api import create_api_routes
from src.utils.webui import create_webui_routes
from src.services.use_whisper import start_whisper_service, check_whisper_service
from src.core.task import process_video_background
from src.utils.done_timeout_delete import start_timeout_cleaner

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# 缓存目录
CACHE_DIRS = {'uploads': 'cache/uploads', 'temp': 'cache/temp', 'outputs': 'cache/outputs'}
[os.makedirs(d, exist_ok=True) for d in CACHE_DIRS.values()]


class AppState:
    def __init__(self):
        self.task_queue = []
        self.task_status = {}
        self.batch_tasks = {}
        self.processing_lock = threading.Lock()
        self.current_processing = None
        self.file_deletion_timers = {}
        self.file_download_info = {}
        self.cache_dirs = CACHE_DIRS
        self.shutdown_flag = threading.Event()
        self.timeout_cleaner = None


app_state = AppState()


def process_task_queue():
    """任务处理主循环"""
    while not app_state.shutdown_flag.is_set():
        task_id = None

        with app_state.processing_lock:
            if app_state.task_queue and not app_state.current_processing:
                task_id = app_state.task_queue.pop(0)
                app_state.current_processing = task_id

                # 更新队列位置
                for i, tid in enumerate(app_state.task_queue):
                    if tid in app_state.task_status:
                        app_state.task_status[tid]["queue_position"] = f"队列: {i + 1}"

        if task_id:
            task_info = app_state.task_status.get(task_id, {})
            try:
                process_video_background(task_id, task_info.get('video_path'),
                                         task_info.get('mode'), app_state)
            except Exception as e:
                app_state.task_status[task_id] = {"status": "failed", "error": str(e)}
            finally:
                with app_state.processing_lock:
                    app_state.current_processing = None
                    if 'batch_id' in task_info:
                        from src.core.batch import check_done
                        check_done(task_info['batch_id'], app_state)
        else:
            time.sleep(1)


def init_whisper():
    """初始化 Whisper 服务"""
    if not start_whisper_service():
        print("[WARNING] Whisper 服务启动失败")
        return

    for _ in range(30):
        if check_whisper_service():
            print("[INFO] Whisper 服务已就绪")
            return
        time.sleep(2)

    print("[WARNING] Whisper 服务启动超时")


if __name__ == "__main__":
    try:
        # 初始化服务
        init_whisper()
        threading.Thread(target=process_task_queue, daemon=True).start()

        # 启动文件清理器 (24小时超时)
        app_state.timeout_cleaner = start_timeout_cleaner(CACHE_DIRS, 24)

        # 创建路由
        create_api_routes(app, app_state, CACHE_DIRS)
        create_webui_routes(app)

        print("[INFO] 启动 Flask 服务器...")
        app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)

    except KeyboardInterrupt:
        print("\n[INFO] 收到中断信号")
    finally:
        app_state.shutdown_flag.set()
        if app_state.timeout_cleaner:
            app_state.timeout_cleaner.stop()
        for timer in app_state.file_deletion_timers.values():
            timer.cancel()
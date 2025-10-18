from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import threading
import time
import asyncio
from src.api import create_api_routes
from src.utils.webui import create_webui_routes
from src.services.use_whisper import start_whisper_service, check_whisper_service
from src.core.task import process_video_background
from src.utils.done_timeout_delete import start_timeout_cleaner
from src.services.enabled import startup_resumer

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
        # 添加限流器需要的属性
        self.ip_last_request = {}


app_state = AppState()


def process_task_queue():
    """任务处理主循环 - 完全基于数据库查询"""
    from src.core.coordinate import task_coordinator
    
    while not app_state.shutdown_flag.is_set():
        task_id = None

        # 从数据库获取下一个待处理任务
        try:
            all_tasks = task_coordinator.get_all_tasks()
            queued_tasks = []
            
            # 找到所有需要处理的任务（队列中 + 中断恢复的任务）
            for tid, task in all_tasks['single_tasks'].items():
                if task['status'] in ["队列中", "提取原文字幕", "翻译原文字幕"]:
                    queued_tasks.append((tid, task['created_at']))
            
            # 按创建时间排序，处理最早的任务
            if queued_tasks:
                queued_tasks.sort(key=lambda x: x[1])
                task_id = queued_tasks[0][0]
                
                # 不要在这里修改任务状态！
                # 让 process_video_background() 根据当前状态正确处理恢复逻辑
        
        except Exception as e:
            print(f"[ERROR] 获取队列任务失败: {e}")
            time.sleep(5)
            continue

        if task_id:
            # 从数据库获取任务信息
            db_task = task_coordinator.get_task(task_id)
            
            if db_task:
                task_info = {
                    'video_path': db_task['video_path'],
                    'mode': db_task['mode'],
                    'batch_id': db_task.get('batch_id')
                }
                
                try:
                    process_video_background(task_id, task_info.get('video_path'),
                                             task_info.get('mode'), app_state)
                except Exception as e:
                    # process_video_background内部已经处理了异常和状态更新
                    # 这里只记录日志，不重复更新状态
                    print(f"[ERROR] 任务 {task_id} 处理异常: {str(e)}")
                finally:
                    # 检查批量任务完成状态
                    if task_info.get('batch_id'):
                        from src.core.batch import check_done
                        check_done(task_info['batch_id'], app_state)
            else:
                print(f"[ERROR] 任务 {task_id} 在数据库中不存在")
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


def init_startup_recovery():
    """初始化高优先级启动恢复功能 - 纯数据库方式"""
    def run_recovery():
        try:
            print("[INFO] 高优先级任务恢复开始...")
            # 运行异步任务恢复（基于数据库）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(startup_resumer.resume_incomplete_tasks())
            loop.close()
            print("[INFO] 高优先级任务恢复完成")
        except Exception as e:
            print(f"[ERROR] 任务恢复过程出错: {e}")
            # 即使失败也要标记为完成，以便继续启动流程
            startup_resumer.startup_completed = True
    
    # 同步执行启动恢复，确保完成后再继续
    recovery_thread = threading.Thread(target=run_recovery, daemon=False)
    recovery_thread.start()
    
    print("[INFO] 等待高优先级启动恢复完成...")
    recovery_thread.join(timeout=60)  # 最多等待60秒
    
    if recovery_thread.is_alive():
        print("[WARNING] 启动恢复超时，继续启动流程")
    else:
        print("[INFO] 高优先级启动恢复线程完成")


if __name__ == "__main__":
    try:
        # 初始化服务
        init_whisper()
        
        # 初始化高优先级任务恢复功能
        print("[INFO] 高优先级启动任务恢复检查...")
        init_startup_recovery()
        
        # 启动任务处理队列
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
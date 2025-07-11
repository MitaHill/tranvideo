import os
import threading
import time

def schedule_del(filename, delay_minutes, timers, info, cache_dirs):
    """安排文件删除"""
    def delete_file():
        for d in cache_dirs.values():
            path = f"{d}/{filename}"
            if os.path.exists(path):
                try:
                    os.remove(path)
                    timers.pop(filename, None)
                    info.pop(filename, None)
                except:
                    pass

    if filename in timers:
        timers[filename].cancel()
    timer = threading.Timer(delay_minutes * 60, delete_file)
    timer.start()
    timers[filename] = timer

def handle_down(filename, info, timers, cache_dirs):
    """处理文件下载"""
    cur_time = time.time()
    if filename not in info:
        info[filename] = {"first_download": cur_time, "extended": False}
        schedule_del(filename, 30, timers, info, cache_dirs)
    else:
        file_info = info[filename]
        if (cur_time - file_info["first_download"]) / 60 <= 30 and not file_info["extended"]:
            file_info["extended"] = True
            schedule_del(filename, 15, timers, info, cache_dirs)

def clear_all(timers, info, cache_dirs):
    """清理所有缓存文件"""
    try:
        # 停止所有定时器
        for timer in timers.values():
            timer.cancel()
        timers.clear()
        info.clear()

        # 删除所有文件
        for dir_name in cache_dirs.values():
            if os.path.exists(dir_name):
                for filename in os.listdir(dir_name):
                    file_path = os.path.join(dir_name, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
        return True
    except Exception:
        return False

def save_temp(file, cache_dirs, prefix=""):
    """保存临时文件"""
    import uuid
    temp_name = f"{prefix}{uuid.uuid4()}_{file.filename}"
    temp_path = f"{cache_dirs['temp']}/{temp_name}"
    file.save(temp_path)
    return temp_path

def move_final(temp_path, cache_dirs, task_id, filename):
    """移动到最终位置"""
    final_path = f"{cache_dirs['uploads']}/{task_id}_{filename}"
    os.rename(temp_path, final_path)
    return final_path
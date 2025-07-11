import uuid
import os
import time
from src.core.invite import check_code, validate, deduct_time
from src.core.video import get_duration, process_srt, merge_video, clean_temp
from src.utils.filer import schedule_del, handle_down, clear_all, save_temp, move_final
from src.core.batch import check_done, create_batch, get_status as get_batch_status
from src.utils.taskq import add_task, get_status as get_queue_status, create_task_data
from src.services.use_whisper import check_whisper_service, call_whisper_service, format_srt


def validate_video_file(file):
    """验证视频文件"""
    if not file or not file.filename:
        return False, "文件名为空"

    allowed_exts = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.3gp'}
    ext = os.path.splitext(file.filename.lower())[1]

    if ext not in allowed_exts:
        return False, f"不支持的格式: {ext}"
    return True, "验证通过"


def process_video_background(task_id, video_path, mode, app_state):
    """后台处理视频"""
    try:
        app_state.task_status[task_id].update({"status": "processing", "progress": "初始化..."})

        if not os.path.exists(video_path):
            raise Exception(f"文件不存在: {video_path}")

        if not check_whisper_service():
            raise Exception("Whisper 服务不可用")

        # 提取原文字幕
        app_state.task_status[task_id]["progress"] = "提取原文字幕中..."
        whisper_result = call_whisper_service(video_path)

        if not whisper_result.get('success'):
            raise Exception(f"转录失败: {whisper_result.get('error', '未知错误')}")

        # 保存字幕文件
        cache_dirs = app_state.cache_dirs
        translated_srt = f"{cache_dirs['outputs']}/{task_id}_translated.srt"

        with open(translated_srt, 'w', encoding='utf-8') as f:
            f.write(format_srt(whisper_result['segments']))

        app_state.task_status[task_id]["progress"] = "翻译字幕中..."
        if not process_srt(translated_srt):
            raise Exception("字幕翻译失败")

        # 处理视频或字幕
        if mode == "video":
            app_state.task_status[task_id]["progress"] = "合成视频中..."
            output_video = f"{cache_dirs['outputs']}/{task_id}_final.mp4"
            if not merge_video(video_path, translated_srt, output_video):
                raise Exception("视频合成失败")
            result_file = f"{task_id}_final.mp4"
        else:
            result_file = f"{task_id}_translated.srt"

        clean_temp(video_path)

        # 更新任务状态
        app_state.task_status[task_id].update({
            "status": "completed",
            "filename": result_file,
            "mode": mode,
            "progress": "处理完成"
        })

        # 扣除时长
        task_info = app_state.task_status[task_id]
        if task_info.get("invite_code") and task_info.get("duration"):
            deduct_time(task_info["invite_code"], task_info["duration"])

    except Exception as e:
        app_state.task_status[task_id] = {
            "status": "failed",
            "error": str(e),
            "progress": f"处理失败: {str(e)}"
        }
        if video_path and os.path.exists(video_path):
            clean_temp(video_path)


def create_single_task(invite_code, file, mode, app_state, cache_dirs):
    """创建单个任务"""
    validation = validate(invite_code)
    if not validation["valid"]:
        return {"error": "邀请码无效或时长不足", "code": 403}

    is_valid, message = validate_video_file(file)
    if not is_valid:
        return {"error": message, "code": 400}

    try:
        temp_path = save_temp(file, cache_dirs)
        duration = get_duration(temp_path)

        if duration > validation["minutes"]:
            clean_temp(temp_path)
            return {
                "error": f"视频时长 {duration:.1f} 分钟超过可用时长 {validation['minutes']} 分钟",
                "code": 413
            }

        task_id = str(uuid.uuid4())
        video_path = move_final(temp_path, cache_dirs, task_id, file.filename)
        task_data = create_task_data(mode, video_path, invite_code, duration)
        final_task_id = add_task(task_data, app_state)

        return {
            "task_id": final_task_id,
            "status": "queued",
            "queue_position": app_state.task_status[final_task_id].get("queue_position", "队列: 1"),
            "duration": duration
        }

    except Exception as e:
        return {"error": f"处理文件时出错: {str(e)}", "code": 500}


def create_batch_tasks(invite_code, files, mode, app_state, cache_dirs):
    """创建批量任务"""
    validation = validate(invite_code)
    if not validation["valid"]:
        return {"error": "邀请码无效或时长不足", "code": 403}

    if not files:
        return {"error": "未选择文件", "code": 400}

    # 验证文件
    for file in files:
        if file.filename:
            is_valid, message = validate_video_file(file)
            if not is_valid:
                return {"error": message, "code": 400}

    temp_files = []
    total_duration = 0

    try:
        # 保存文件并计算时长
        for file in files:
            if file.filename:
                temp_path = save_temp(file, cache_dirs)
                temp_files.append((temp_path, file))
                total_duration += get_duration(temp_path)

        if total_duration > validation["minutes"]:
            for temp_path, _ in temp_files:
                clean_temp(temp_path)
            return {
                "error": f"视频总时长 {total_duration:.1f} 分钟超过可用时长 {validation['minutes']} 分钟",
                "code": 413
            }

        # 创建批量任务
        batch_id = str(uuid.uuid4())
        task_ids = []

        for temp_path, file in temp_files:
            task_id = str(uuid.uuid4())
            video_path = move_final(temp_path, cache_dirs, task_id, file.filename)
            task_data = create_task_data(mode, video_path, invite_code, 0,
                                         batch_id=batch_id, original_name=file.filename)
            task_ids.append(add_task(task_data, app_state))

        create_batch(batch_id, task_ids, mode, invite_code, app_state)

        return {
            "batch_id": batch_id,
            "file_count": len(task_ids),
            "status": "processing",
            "total_duration": total_duration
        }

    except Exception as e:
        for temp_path, _ in temp_files:
            clean_temp(temp_path)
        return {"error": f"处理文件时出错: {str(e)}", "code": 500}


def clear_all_cache(app_state, cache_dirs):
    """清理所有缓存文件"""
    with app_state.processing_lock:
        if app_state.task_queue or app_state.current_processing:
            return {"error": "系统忙碌，请在队列为空时重试", "code": 400}

    return {"message": "所有缓存文件已成功删除"} if clear_all(
        app_state.file_deletion_timers, app_state.file_download_info, cache_dirs
    ) else {"error": "删除缓存文件失败", "code": 500}


class TaskManager:
    """任务管理器"""

    def __init__(self, app_state, cache_dirs):
        self.app_state = app_state
        self.cache_dirs = cache_dirs

    def create_task(self, invite_code, file, mode):
        return create_single_task(invite_code, file, mode, self.app_state, self.cache_dirs)

    def create_batch(self, invite_code, files, mode):
        return create_batch_tasks(invite_code, files, mode, self.app_state, self.cache_dirs)

    def get_task_status(self, task_id):
        return self.app_state.task_status.get(task_id)

    def get_batch_status(self, batch_id):
        return get_batch_status(batch_id, self.app_state)

    def get_system_status(self):
        return get_queue_status(self.app_state)

    def clear_cache(self):
        return clear_all_cache(self.app_state, self.cache_dirs)


# 兼容性别名
check_invitation_code = check_code
get_video_duration = get_duration
schedule_file_deletion = schedule_del
handle_file_download = handle_down
check_batch_completion = check_done

__all__ = [
    'check_invitation_code', 'get_video_duration', 'schedule_file_deletion',
    'handle_file_download', 'check_batch_completion', 'process_video_background',
    'create_single_task', 'create_batch_tasks', 'clear_all_cache', 'TaskManager'
]
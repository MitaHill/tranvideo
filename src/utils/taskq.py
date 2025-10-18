import uuid
from ..core.coordinate import task_coordinator


def add_task(task_data, app_state):
    """添加任务到队列 - 完全基于数据库"""
    task_id = str(uuid.uuid4())

    # 使用coordinate.py创建任务在数据库中
    video_name = task_data.get("original_name", "unknown.mp4")
    video_duration_seconds = task_data.get("duration", 0) * 60  # 转换为秒
    
    success = task_coordinator.create_single_task(
        task_id=task_id,
        video_path=task_data.get("video_path", ""),
        video_name=video_name,
        video_duration=video_duration_seconds,
        mode=task_data.get("mode", "srt"),
        invite_code=task_data.get("invite_code", ""),
        batch_id=task_data.get("batch_id")
    )
    
    if not success:
        raise Exception(f"任务 {task_id} 数据库创建失败")
    
    # 任务状态和队列位置完全由数据库管理
    # 不再维护内存状态

    return task_id


def get_position(app_state):
    """获取队列位置"""
    if app_state.current_processing:
        return f"队列: {len(app_state.task_queue)}"
    else:
        return "队列: Now"


def update_positions(app_state):
    """更新所有任务的队列位置"""
    for i, tid in enumerate(app_state.task_queue):
        if tid in app_state.task_status:
            app_state.task_status[tid]["queue_position"] = f"队列: {i + 1}"


def get_status(app_state):
    """获取队列状态"""
    with app_state.processing_lock:
        return {
            "busy": app_state.current_processing is not None,
            "queue_length": len(app_state.task_queue),
            "current_task": app_state.current_processing
        }




def create_task_data(mode, video_path, invite_code, duration, **kwargs):
    """创建任务数据"""
    return {
        "mode": mode,
        "video_path": video_path,
        "invite_code": invite_code,
        "duration": duration,
        **kwargs
    }
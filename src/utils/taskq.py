import uuid


def add_task(task_data, app_state):
    """添加任务到队列"""
    task_id = str(uuid.uuid4())

    with app_state.processing_lock:
        app_state.task_queue.append(task_id)
        queue_pos = get_position(app_state)

    # 创建任务状态
    app_state.task_status[task_id] = {
        "status": "queued",
        "queue_position": queue_pos,
        **task_data
    }

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
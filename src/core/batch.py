import zipfile
import os
import time


def check_done(batch_id, app_state):
    """检查批量任务是否完成"""
    if batch_id not in app_state.batch_tasks:
        return False

    batch = app_state.batch_tasks[batch_id]
    all_done = all(
        app_state.task_status.get(tid, {}).get('status') in ['completed', 'failed']
        for tid in batch['task_ids']
    )

    if all_done:
        batch['status'] = 'completed'
        create_zip(batch_id, batch['task_ids'], app_state)
        return True
    return False


def create_zip(batch_id, task_ids, app_state):
    """创建批量下载zip文件"""
    cache_dirs = getattr(app_state, 'cache_dirs', {'outputs': 'cache/outputs'})
    zip_path = f"{cache_dirs['outputs']}/{batch_id}_batch.zip"

    with zipfile.ZipFile(zip_path, 'w') as zf:
        for tid in task_ids:
            task = app_state.task_status.get(tid, {})
            if task.get('status') == 'completed' and 'filename' in task:
                fpath = f"{cache_dirs['outputs']}/{task['filename']}"
                if os.path.exists(fpath):
                    zf.write(fpath, task['filename'])

    app_state.batch_tasks[batch_id]['download_file'] = f"{batch_id}_batch.zip"


def create_batch(batch_id, task_ids, mode, invite_code, app_state):
    """创建批量任务记录"""
    app_state.batch_tasks[batch_id] = {
        "status": "processing",
        "task_ids": task_ids,
        "mode": mode,
        "created": time.time(),
        "invite_code": invite_code
    }


def get_status(batch_id, app_state):
    """获取批量任务状态"""
    if batch_id not in app_state.batch_tasks:
        return None

    batch = app_state.batch_tasks[batch_id]
    tasks = {tid: app_state.task_status.get(tid, {}) for tid in batch['task_ids']}
    return {
        "batch_id": batch_id,
        "status": batch['status'],
        "task_ids": batch['task_ids'],
        "tasks": tasks,
        "download_file": batch.get('download_file')
    }
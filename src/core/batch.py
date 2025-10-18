import zipfile
import os
import time
from .coordinate import task_coordinator


def check_done(batch_id, app_state):
    """检查批量任务是否完成"""
    # 优先检查数据库中的批量任务
    db_batch = task_coordinator.get_batch_task(batch_id)
    if db_batch:
        # 检查所有子任务状态
        completed_tasks = []
        for tid in db_batch['sub_tasks']:
            task = task_coordinator.get_task(tid)
            if task and task.get('status') == '已完成':
                completed_tasks.append(tid)
        
        # 只有所有任务都完成时才创建压缩包
        if len(completed_tasks) == len(db_batch['sub_tasks']):
            # 创建zip文件
            create_zip(batch_id, completed_tasks, app_state)
            return True
        return False
    
    # 回退到内存检查
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
    """创建批量下载zip文件，按照新的文件组织规范"""
    cache_dirs = getattr(app_state, 'cache_dirs', {'outputs': 'cache/outputs'})
    
    # 获取批量任务信息
    db_batch = task_coordinator.get_batch_task(batch_id)
    if not db_batch:
        print(f"[ERROR] 批量任务不存在: {batch_id}")
        return
    
    batch_mode = None
    # 从第一个任务获取批量模式
    for tid in task_ids:
        db_task = task_coordinator.get_task(tid)
        if db_task:
            batch_mode = db_task.get('mode', 'srt')
            break
    
    if batch_mode == 'video':
        # 批量视频模式：打包所有视频文件
        zip_path = f"{cache_dirs['outputs']}/{batch_id}_video.zip"
        _create_batch_video_zip(batch_id, task_ids, zip_path, cache_dirs)
    else:
        # 批量SRT模式：打包所有任务目录
        zip_path = f"{cache_dirs['outputs']}/{batch_id}_batch_srt.zip"
        _create_batch_srt_zip(batch_id, task_ids, zip_path, cache_dirs)


def _create_batch_srt_zip(batch_id, task_ids, zip_path, cache_dirs):
    """创建批量SRT压缩包：每个任务一个目录，目录内包含三种字幕"""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for tid in task_ids:
            db_task = task_coordinator.get_task(tid)
            if db_task and db_task.get('status') == '已完成':
                video_name = db_task.get('video_name', 'video.mp4')
                video_name_without_ext = os.path.splitext(video_name)[0]
                
                # 任务临时目录
                task_temp_dir = f"{cache_dirs.get('temp', 'cache/temp')}/{tid}"
                
                if os.path.exists(task_temp_dir):
                    # 在压缩包中为每个任务创建目录：{video_name}_{task_id}
                    zip_task_dir = f"{video_name_without_ext}_{tid}"
                    
                    subtitle_files = [
                        ("chinese.srt", "中文字幕.srt"),
                        ("original.srt", "原文字幕.srt"),
                        ("bilingual.srt", "双语字幕.srt")
                    ]
                    
                    for source_file, zip_file in subtitle_files:
                        source_path = os.path.join(task_temp_dir, source_file)
                        if os.path.exists(source_path):
                            zip_file_path = f"{zip_task_dir}/{zip_file}"
                            zf.write(source_path, zip_file_path)
                            print(f"[INFO] 添加字幕文件到批量压缩包: {zip_file_path}")


def _create_batch_video_zip(batch_id, task_ids, zip_path, cache_dirs):
    """创建批量视频压缩包：打包所有视频文件"""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for tid in task_ids:
            db_task = task_coordinator.get_task(tid)
            if db_task and db_task.get('status') == '已完成':
                video_name = db_task.get('video_name', 'video.mp4')
                video_name_without_ext = os.path.splitext(video_name)[0]
                
                # 视频文件路径（按新命名规范）
                video_file = f"{cache_dirs.get('outputs', 'cache/outputs')}/{video_name_without_ext}_{tid}_video.mp4"
                
                if os.path.exists(video_file):
                    # 在压缩包中使用原始文件名加task_id的命名
                    zip_filename = f"{video_name_without_ext}_{tid}_video.mp4"
                    zf.write(video_file, zip_filename)
                    print(f"[INFO] 添加视频文件到批量压缩包: {zip_filename}")

    print(f"[INFO] 批量任务 {batch_id} 打包完成，保存到: {zip_path}")


def create_batch(batch_id, task_ids, mode, invite_code, app_state):
    """创建批量任务记录"""
    # 使用coordinate.py创建批量任务
    success = task_coordinator.create_batch_task(batch_id, task_ids)
    
    if success:
        # 保持内存状态兼容性
        app_state.batch_tasks[batch_id] = {
            "status": "processing",
            "task_ids": task_ids,
            "mode": mode,
            "created": time.time(),
            "invite_code": invite_code
        }
    else:
        # 如果数据库创建失败，仍创建内存记录
        app_state.batch_tasks[batch_id] = {
            "status": "processing",
            "task_ids": task_ids,
            "mode": mode,
            "created": time.time(),
            "invite_code": invite_code
        }


def get_status(batch_id, app_state):
    """获取批量任务状态"""
    # 优先从数据库获取批量任务状态
    db_batch = task_coordinator.get_batch_task(batch_id)
    if db_batch:
        # 获取所有子任务的详细状态
        tasks = {}
        for tid in db_batch['sub_tasks']:
            db_task = task_coordinator.get_task(tid)
            if db_task:
                tasks[tid] = {
                    "status": db_task["status"],
                    "progress": db_task["progress"],
                    "error": db_task.get("error")
                }
        
        # 获取批量任务模式来决定下载文件名
        batch_mode = None
        for tid in db_batch['sub_tasks']:
            task = task_coordinator.get_task(tid)
            if task:
                batch_mode = task.get('mode', 'srt')
                break
        
        download_file = None
        if db_batch['status'] == '已完成':
            if batch_mode == 'video':
                download_file = f"{batch_id}_video.zip"
            else:
                download_file = f"{batch_id}_batch_srt.zip"
        
        return {
            "batch_id": batch_id,
            "status": db_batch['status'],
            "task_ids": list(db_batch['sub_tasks'].keys()),
            "tasks": tasks,
            "download_file": download_file
        }
    
    # 回退到内存查询
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
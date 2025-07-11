from flask import request, jsonify, send_file
import os
import json
from src.core.task import (
    check_invitation_code,
    create_single_task,
    create_batch_tasks,
    handle_file_download,
    clear_all_cache,
    TaskManager
)
from src.services.use_whisper import check_whisper_service


def config_ollama_api_handler(api_url):
    """配置Ollama API地址"""
    try:
        if not api_url.startswith(('http://', 'https://')):
            api_url = f'http://{api_url}'

        config_path = 'config/tran-py.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
            except json.JSONDecodeError:
                config = {}

        config['ollama_api'] = api_url

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return jsonify({"success": True, "message": f"API地址已更新为: {api_url}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def config_ollama_model_handler(model_name):
    """配置Ollama模型"""
    try:
        config_path = 'config/tran-py.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
            except json.JSONDecodeError:
                config = {}

        config['ollama_model'] = model_name

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return jsonify({"success": True, "message": f"模型已更新为: {model_name}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_tranpy_config_handler():
    """获取当前配置"""
    try:
        config_path = 'config/tran-py.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return jsonify(json.loads(content))
            except json.JSONDecodeError:
                pass
        return jsonify({"ollama_api": None, "ollama_model": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def whisper_health_handler():
    """检查Whisper服务健康状态"""
    available = check_whisper_service()
    return jsonify({"available": available})


def check_invitation_handler(invite_code):
    """检查邀请码有效性"""
    code, minutes = check_invitation_code(invite_code)
    return jsonify({
        "invite_code": code,
        "available_minutes": minutes,
        "valid": minutes > 0
    })


def get_status_handler(app_state, cache_dirs):
    """获取系统状态"""
    task_manager = TaskManager(app_state, cache_dirs)
    status = task_manager.get_system_status()
    return jsonify(status)


def process_batch_handler(invite_code, app_state, cache_dirs):
    """批量处理文件"""
    files = request.files.getlist('files')
    mode = request.form.get('mode', 'srt')

    result = create_batch_tasks(invite_code, files, mode, app_state, cache_dirs)

    if "error" in result:
        return jsonify({"error": result["error"]}), result.get("code", 500)

    return jsonify(result)


def get_batch_status_handler(batch_id, app_state):
    """获取批量任务状态"""
    cache_dirs = getattr(app_state, 'cache_dirs', {})
    task_manager = TaskManager(app_state, cache_dirs)
    status = task_manager.get_batch_status(batch_id)
    if status is None:
        return jsonify({'error': '批量任务不存在'}), 404
    return jsonify(status)


def download_batch_handler(batch_id, app_state, cache_dirs):
    """下载批量任务结果"""
    if batch_id not in app_state.batch_tasks:
        return jsonify({'error': '批量任务不存在'}), 404

    batch = app_state.batch_tasks[batch_id]
    if 'download_file' not in batch:
        return jsonify({'error': '下载文件尚未准备好'}), 404

    file_path = f"{cache_dirs['outputs']}/{batch['download_file']}"
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    handle_file_download(batch['download_file'], app_state.file_download_info,
                         app_state.file_deletion_timers, cache_dirs)
    return send_file(file_path, as_attachment=True)


def process_srt_only_handler(invite_code, app_state, cache_dirs):
    """处理单个文件生成SRT字幕"""
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    result = create_single_task(invite_code, file, "srt", app_state, cache_dirs)

    if "error" in result:
        return jsonify({"error": result["error"]}), result.get("code", 500)

    return jsonify(result)


def process_video_with_subtitles_handler(invite_code, app_state, cache_dirs):
    """处理单个文件生成带字幕的视频"""
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    result = create_single_task(invite_code, file, "video", app_state, cache_dirs)

    if "error" in result:
        return jsonify({"error": result["error"]}), result.get("code", 500)

    return jsonify(result)


def get_task_status_handler(task_id, app_state, cache_dirs):
    """获取单个任务状态"""
    task_manager = TaskManager(app_state, cache_dirs)
    status = task_manager.get_task_status(task_id)
    if status is None:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(status)


def download_file_common(filename, app_state, cache_dirs):
    """通用文件下载处理"""
    file_path = f"{cache_dirs['outputs']}/{filename}"
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    handle_file_download(filename, app_state.file_download_info,
                         app_state.file_deletion_timers, cache_dirs)
    return send_file(file_path, as_attachment=True)


def download_srt_handler(filename, app_state, cache_dirs):
    """下载SRT字幕文件"""
    return download_file_common(filename, app_state, cache_dirs)


def download_video_handler(filename, app_state, cache_dirs):
    """下载视频文件"""
    return download_file_common(filename, app_state, cache_dirs)


def delete_all_cache_handler(app_state, cache_dirs):
    """管理员功能：删除所有缓存"""
    result = clear_all_cache(app_state, cache_dirs)

    if "error" in result:
        return jsonify({"error": result["error"]}), result.get("code", 500)

    return jsonify(result)
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
from src.core.coordinate import task_coordinator
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
                        config = json.loads(content)
                        # 隐藏 API Key 信息
                        if 'openai_api_key' in config and config['openai_api_key']:
                            config['openai_api_key'] = '***'
                        return jsonify(config)
            except json.JSONDecodeError:
                pass
        return jsonify({"translator_type": "ollama", "ollama_api": None, "ollama_model": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def config_translator_type_handler(translator_type):
    """配置翻译器类型"""
    if translator_type not in ['ollama', 'openai']:
        return jsonify({"error": "不支持的翻译器类型"}), 400
    
    return update_config_field('translator_type', translator_type)


def config_openai_base_url_handler(base_url):
    """配置OpenAI基础URL"""
    try:
        # URL解码
        from urllib.parse import unquote
        decoded_url = unquote(base_url)
        
        # 验证URL格式
        if not decoded_url.startswith(('http://', 'https://')):
            return jsonify({"error": "URL格式错误，必须以http://或https://开头"}), 400
            
        return update_config_field('openai_base_url', decoded_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def config_openai_api_key_handler(api_key):
    """配置OpenAI API密钥"""
    try:
        from urllib.parse import unquote
        decoded_key = unquote(api_key)
        
        if not decoded_key or len(decoded_key.strip()) < 10:
            return jsonify({"error": "API密钥格式错误"}), 400
            
        return update_config_field('openai_api_key', decoded_key)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def config_openai_model_handler(model_name):
    """配置OpenAI模型名称"""
    try:
        from urllib.parse import unquote
        decoded_model = unquote(model_name)
        
        if not decoded_model or len(decoded_model.strip()) < 2:
            return jsonify({"error": "模型名称格式错误"}), 400
            
        return update_config_field('openai_model', decoded_model)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_config_field(field_name, field_value):
    """更新配置文件的指定字段"""
    try:
        config_path = 'config/tran-py.json'
        
        # 读取现有配置
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
            except json.JSONDecodeError:
                pass
        
        # 更新字段
        config[field_name] = field_value
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": f"{field_name} 配置已更新"})
        
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
    """获取系统状态 - 完全基于数据库查询"""
    try:
        # 使用TaskManager获取系统状态（纯数据库查询）
        task_manager = TaskManager(app_state, cache_dirs)
        system_status = task_manager.get_system_status()
        
        # 添加缓存信息
        system_status["cache_info"] = {
            "uploads": len(os.listdir(cache_dirs.get('uploads', ''))) if os.path.exists(cache_dirs.get('uploads', '')) else 0,
            "outputs": len(os.listdir(cache_dirs.get('outputs', ''))) if os.path.exists(cache_dirs.get('outputs', '')) else 0
        }
        
        # 添加批量任务信息
        all_tasks = task_coordinator.get_all_tasks()
        system_status["batch_tasks"] = len(all_tasks['batch_tasks'])
        
        return jsonify(system_status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    try:
        # 使用任务协调器获取批量任务状态
        batch_task = task_coordinator.get_batch_task(batch_id)
        if batch_task is None:
            return jsonify({'error': '批量任务不存在'}), 404
        
        # 计算批量任务的总体进度
        sub_tasks_with_progress = {}
        total_progress = 0
        task_count = len(batch_task["sub_tasks"])
        
        for task_id, sub_task in batch_task["sub_tasks"].items():
            db_task = task_coordinator.get_task(task_id)
            progress_percentage = db_task.get("prog_bar", 0) if db_task else 0
            total_progress += progress_percentage
            
            sub_tasks_with_progress[task_id] = {
                **sub_task,
                "progress_percentage": progress_percentage
            }
        
        batch_progress = total_progress / task_count if task_count > 0 else 0
        
        return jsonify({
            "batch_id": batch_id,
            "status": batch_task["status"],
            "created_at": batch_task["created_at"],
            "updated_at": batch_task["updated_at"],
            "progress_percentage": round(batch_progress, 1),  # 批量任务总体进度
            "sub_tasks": sub_tasks_with_progress
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def download_batch_handler(batch_id, app_state, cache_dirs):
    """下载批量任务结果"""
    try:
        # 使用任务协调器获取批量任务信息
        batch_task = task_coordinator.get_batch_task(batch_id)
        if batch_task is None:
            return jsonify({'error': '批量任务不存在'}), 404

        # 检查批量任务是否完成
        if batch_task['status'] != '已完成':
            return jsonify({'error': '批量任务尚未完成'}), 400

        # 查找批量下载文件 - 根据任务模式确定文件名
        # 从第一个子任务获取模式
        batch_mode = None
        for task_id in batch_task['sub_tasks']:
            task = task_coordinator.get_task(task_id)
            if task:
                batch_mode = task.get('mode', 'srt')
                break
        
        if batch_mode == 'video':
            download_file = f"{batch_id}_video.zip"
        else:
            download_file = f"{batch_id}_batch_srt.zip"
            
        file_path = f"{cache_dirs['outputs']}/{download_file}"
        
        if not os.path.exists(file_path):
            return jsonify({'error': '下载文件不存在'}), 404

        # 标记相关任务为已下载状态
        for task_id in batch_task['sub_tasks']:
            task_coordinator.mark_task_downloaded(task_id)

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    try:
        # 使用TaskManager获取任务状态（包含状态映射）
        task_manager = TaskManager(app_state, cache_dirs)
        task = task_manager.get_task_status(task_id)
        
        if task is None:
            return jsonify({'error': '任务不存在'}), 404
        
        # 从数据库获取进度条信息
        db_task = task_coordinator.get_task(task_id)
        progress_percentage = db_task.get("prog_bar", 0) if db_task else 0
        
        # 返回前端期望的任务状态格式
        return jsonify({
            "task_id": task_id,
            "status": task["status"],  # 已经过状态映射的英文状态
            "progress": task["progress"],
            "progress_percentage": progress_percentage,  # 进度百分比 (0-100)
            "queue_position": task.get("queue_position", ""),
            "mode": task.get("mode", "srt"),
            "filename": task.get("filename", ""),
            "error": task.get("error")
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def download_file_common(filename, app_state, cache_dirs):
    """通用文件下载处理"""
    try:
        file_path = f"{cache_dirs['outputs']}/{filename}"
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 从文件名中提取任务ID
        task_id = filename.split('_')[0]
        
        # 使用任务协调器标记任务为已下载
        task = task_coordinator.get_task(task_id)
        if task and task['status'] == '已完成':
            task_coordinator.mark_task_downloaded(task_id)

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
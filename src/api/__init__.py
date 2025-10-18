from flask import request, jsonify
import ipaddress
import time
from .security import RateLimiter, security_check
from .handlers import (
    config_ollama_api_handler,
    config_ollama_model_handler,
    get_tranpy_config_handler,
    config_translator_type_handler,
    config_openai_base_url_handler,
    config_openai_api_key_handler,
    config_openai_model_handler,
    whisper_health_handler,
    check_invitation_handler,
    get_status_handler,
    process_batch_handler,
    get_batch_status_handler,
    download_batch_handler,
    process_srt_only_handler,
    process_video_with_subtitles_handler,
    get_task_status_handler,
    download_srt_handler,
    download_video_handler,
    delete_all_cache_handler
)


def is_internal_ip(ip_str):
    """检查IP是否为内网地址"""
    try:
        ip = ipaddress.ip_address(ip_str)
        allowed_networks = [
            ipaddress.ip_network('192.168.9.0/24'),
            ipaddress.ip_network('127.0.0.0/8'),
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16'),
        ]
        return any(ip in network for network in allowed_networks)
    except:
        return False


def require_internal_access(f):
    """装饰器：限制只能内网访问"""

    def wrapper(*args, **kwargs):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        if not is_internal_ip(client_ip):
            return jsonify({
                "error": "访问被拒绝：管理功能仅限内网访问",
                "client_ip": client_ip
            }), 403

        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


def create_api_routes(app, app_state, cache_dirs):
    """创建所有API路由"""
    # 确保 app_state 有 cache_dirs 属性
    if not hasattr(app_state, 'cache_dirs'):
        app_state.cache_dirs = cache_dirs

    rate_limiter = RateLimiter()

    # 全局IP限制装饰器 - 2秒一次请求
    def global_rate_limit(f):
        def wrapper(*args, **kwargs):
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()

            # 检查IP访问频率
            current_time = time.time()
            if not hasattr(app_state, 'ip_last_request'):
                app_state.ip_last_request = {}

            last_request = app_state.ip_last_request.get(client_ip, 0)
            # 临时禁用限流以便测试 - 生产环境需要启用
            # if current_time - last_request < 0.3:  # 0.3秒限制，配合前端延迟
            #     return jsonify({"error": "请求过于频繁，请等待片刻", "client_ip": client_ip}), 429

            app_state.ip_last_request[client_ip] = current_time
            return f(*args, **kwargs)

        wrapper.__name__ = f.__name__
        return wrapper

    # 管理API - 需要内网访问
    @app.route("/api/tranpy/config-ollama-api/<path:api_url>", methods=['GET'])
    @require_internal_access
    def config_ollama_api(api_url):
        return config_ollama_api_handler(api_url)

    @app.route("/api/tranpy/config-ollama-model/<model_name>", methods=['GET'])
    @require_internal_access
    def config_ollama_model(model_name):
        return config_ollama_model_handler(model_name)

    @app.route("/api/administrator/delete_all_cache", methods=['POST'])
    @require_internal_access
    def delete_all_cache():
        return delete_all_cache_handler(app_state, cache_dirs)

    @app.route("/api/tranpy/config", methods=['GET'])
    @require_internal_access
    def get_tranpy_config():
        return get_tranpy_config_handler()

    @app.route("/api/tranpy/config-translator-type/<translator_type>", methods=['GET'])
    @require_internal_access
    def config_translator_type(translator_type):
        return config_translator_type_handler(translator_type)

    @app.route("/api/tranpy/config-openai-base-url/<path:base_url>", methods=['GET'])
    @require_internal_access
    def config_openai_base_url(base_url):
        return config_openai_base_url_handler(base_url)

    @app.route("/api/tranpy/config-openai-api-key/<path:api_key>", methods=['GET'])
    @require_internal_access
    def config_openai_api_key(api_key):
        return config_openai_api_key_handler(api_key)

    @app.route("/api/tranpy/config-openai-model/<path:model_name>", methods=['GET'])
    @require_internal_access
    def config_openai_model(model_name):
        return config_openai_model_handler(model_name)

    # 公开API - 使用新的安全检查系统

    @app.route("/api/whisper/health", methods=['GET'])
    @security_check()
    def whisper_health():
        return whisper_health_handler()

    @app.route("/api/invitation/check/<invite_code>", methods=['GET'])
    @security_check()
    def check_invitation(invite_code):
        return check_invitation_handler(invite_code)

    @app.route("/api/status", methods=['GET'])
    @security_check()
    def get_status():
        return get_status_handler(app_state, cache_dirs)

    # 处理API - 使用新的安全检查系统
    @app.route("/api/process/srt/<invite_code>", methods=['POST'])
    @security_check(check_file=True)
    def process_srt_only(invite_code):
        return process_srt_only_handler(invite_code, app_state, cache_dirs)

    @app.route("/api/process/video/<invite_code>", methods=['POST'])
    @security_check(check_file=True)
    def process_video_with_subtitles(invite_code):
        return process_video_with_subtitles_handler(invite_code, app_state, cache_dirs)

    @app.route("/api/batch/process/<invite_code>", methods=['POST'])
    @security_check(check_file=True)
    def process_batch(invite_code):
        return process_batch_handler(invite_code, app_state, cache_dirs)

    # 查询API - 使用新的安全检查
    @app.route("/api/batch/<batch_id>", methods=['GET'])
    @security_check()
    def get_batch_status(batch_id):
        return get_batch_status_handler(batch_id, app_state)

    @app.route("/api/task/<task_id>", methods=['GET'])
    @security_check()
    def get_task_status(task_id):
        return get_task_status_handler(task_id, app_state, cache_dirs)
    
    @app.route("/api/query/<task_id>", methods=['GET'])
    @security_check()
    def query_any_task(task_id):
        """统一查询接口：自动判断是批量任务还是单个任务"""
        from src.api.handlers import get_batch_status_handler, get_task_status_handler
        
        # 先尝试批量任务
        batch_result = get_batch_status_handler(task_id, app_state)
        if isinstance(batch_result, tuple) and batch_result[1] == 404:
            # 批量任务不存在，查询单个任务
            return get_task_status_handler(task_id, app_state, cache_dirs)
        else:
            # 批量任务存在
            return batch_result

    # 下载API - 使用新的安全检查
    @app.route("/api/batch/download/<batch_id>", methods=['GET'])
    @security_check()
    def download_batch(batch_id):
        return download_batch_handler(batch_id, app_state, cache_dirs)

    @app.route("/api/download/srt/<filename>", methods=['GET'])
    @security_check()
    def download_srt(filename):
        return download_srt_handler(filename, app_state, cache_dirs)

    @app.route("/api/download/video/<filename>", methods=['GET'])
    @security_check()
    def download_video(filename):
        return download_video_handler(filename, app_state, cache_dirs)

    print("[INFO] API 路由已创建")
    return app
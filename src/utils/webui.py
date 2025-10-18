from flask import send_file, send_from_directory, abort
import os


def create_webui_routes(app):
    """创建Web UI相关路由"""

    @app.route("/")
    def index():
        """主页路由 - 返回前端页面"""
        try:
            return send_file("webui/index.html")
        except FileNotFoundError:
            abort(404, description="前端文件未找到，请确保 webui/index.html 存在")

    @app.route("/api-docs.html")
    def api_docs():
        """API文档页面"""
        try:
            return send_file("webui/api-docs.html")
        except FileNotFoundError:
            abort(404, description="API文档文件未找到，请确保 webui/api-docs.html 存在")

    @app.route("/faq.html")
    def faq():
        """FAQ页面"""
        try:
            return send_file("webui/faq.html")
        except FileNotFoundError:
            abort(404, description="FAQ文件未找到，请确保 webui/faq.html 存在")

    @app.route("/static/<path:filename>")
    def serve_static(filename):
        """静态文件服务"""
        try:
            return send_from_directory("webui/static", filename)
        except FileNotFoundError:
            abort(404, description=f"静态文件 {filename} 未找到")

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        """CSS文件服务"""
        try:
            return send_from_directory("webui/css", filename)
        except FileNotFoundError:
            abort(404, description=f"CSS文件 {filename} 未找到")

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        """JavaScript文件服务"""
        try:
            return send_from_directory("webui/js", filename)
        except FileNotFoundError:
            abort(404, description=f"JavaScript文件 {filename} 未找到")

    @app.route("/debug_frontend.html")
    def debug_frontend():
        """调试前端API页面"""
        try:
            return send_file("debug_frontend.html")
        except FileNotFoundError:
            abort(404, description="调试页面未找到")
    
    @app.route("/test-query.html")
    def test_query():
        """任务查询测试页面"""
        try:
            return send_file("webui/test-query.html")
        except FileNotFoundError:
            abort(404, description="测试页面未找到")
    
    @app.route("/test-batch.html")
    def test_batch():
        """批量任务测试页面"""
        try:
            return send_file("webui/test-batch.html")
        except FileNotFoundError:
            abort(404, description="批量测试页面未找到")
    
    @app.route("/test-download-status.html")
    def test_download_status():
        """下载状态测试页面"""
        try:
            return send_file("webui/test-download-status.html")
        except FileNotFoundError:
            abort(404, description="下载状态测试页面未找到")

    @app.route("/images/<path:filename>")
    def serve_images(filename):
        """图片文件服务"""
        try:
            return send_from_directory("webui/images", filename)
        except FileNotFoundError:
            abort(404, description=f"图片文件 {filename} 未找到")

    @app.route("/favicon.ico")
    def favicon():
        """网站图标"""
        try:
            return send_from_directory("webui", "favicon.ico")
        except FileNotFoundError:
            # 如果没有favicon，返回204 No Content
            return '', 204

    @app.route("/robots.txt")
    def robots():
        """robots.txt文件"""
        try:
            return send_from_directory("webui", "robots.txt")
        except FileNotFoundError:
            # 默认的robots.txt内容
            return "User-agent: *\nDisallow: /api/\nDisallow: /cache/", 200, {'Content-Type': 'text/plain'}

    @app.route("/manifest.json")
    def manifest():
        """PWA manifest文件"""
        try:
            return send_from_directory("webui", "manifest.json")
        except FileNotFoundError:
            abort(404, description="Manifest文件未找到")

    @app.errorhandler(404)
    def not_found_error(error):
        """404错误处理 - 对于前端路由，重定向到index.html"""
        # 如果是API请求，返回JSON错误
        if "/api/" in str(error):
            return {"error": "API endpoint not found"}, 404

        # 对于前端路由，返回index.html让前端路由处理
        try:
            return send_file("webui/index.html")
        except FileNotFoundError:
            return "应用前端文件未找到", 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return {"error": "Internal server error"}, 500
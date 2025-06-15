from flask import Flask, request, jsonify, send_file, render_template_string
import os
import subprocess
import uuid
import threading
import time
import sys

app = Flask(__name__)

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    base_dir = os.path.dirname(sys.executable)
    script_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else base_dir
else:
    # 如果是Python脚本
    base_dir = os.path.dirname(__file__)
    script_dir = base_dir

def get_script_path(script_name):
    """获取脚本的完整路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(script_dir, script_name)
    return script_name

# 缓存目录
CACHE_DIRS = {
    'uploads': 'cache/uploads',
    'temp': 'cache/temp', 
    'outputs': 'cache/outputs'
}

for folder in CACHE_DIRS.values():
    os.makedirs(folder, exist_ok=True)

# 任务队列和状态管理
task_queue = []
task_status = {}
processing_lock = threading.Lock()
current_processing = None

# 文件自动删除管理
file_deletion_timers = {}  # 存储文件删除定时器
file_download_info = {}    # 存储文件下载信息：{filename: {"first_download": timestamp, "extended": bool}}

def schedule_file_deletion(filename, delay_minutes=30):
    """调度文件删除"""
    def delete_file():
        file_path = None
        # 查找文件路径
        for cache_dir in CACHE_DIRS.values():
            potential_path = f"{cache_dir}/{filename}"
            if os.path.exists(potential_path):
                file_path = potential_path
                break
        
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"自动删除文件: {filename}")
                # 清理相关记录
                if filename in file_deletion_timers:
                    del file_deletion_timers[filename]
                if filename in file_download_info:
                    del file_download_info[filename]
            except Exception as e:
                print(f"删除文件失败 {filename}: {e}")
    
    # 取消现有定时器
    if filename in file_deletion_timers:
        file_deletion_timers[filename].cancel()
    
    # 创建新定时器
    timer = threading.Timer(delay_minutes * 60, delete_file)
    timer.start()
    file_deletion_timers[filename] = timer
    print(f"已调度文件删除: {filename} (延迟 {delay_minutes} 分钟)")

def handle_file_download(filename):
    """处理文件下载逻辑"""
    import time
    current_time = time.time()
    
    if filename not in file_download_info:
        # 首次下载
        file_download_info[filename] = {
            "first_download": current_time,
            "extended": False
        }
        schedule_file_deletion(filename, 30)  # 30分钟后删除
        print(f"首次下载: {filename}, 30分钟后删除")
        
    else:
        # 再次下载
        download_info = file_download_info[filename]
        time_since_first = (current_time - download_info["first_download"]) / 60  # 转换为分钟
        
        if time_since_first <= 30 and not download_info["extended"]:
            # 在30分钟内且未延期过，延期15分钟
            download_info["extended"] = True
            schedule_file_deletion(filename, 15)  # 15分钟后删除
            print(f"延期下载: {filename}, 15分钟后删除")
            
        elif time_since_first <= 45:  # 30 + 15
            # 在延期的15分钟内，不再延期
            print(f"延期内下载: {filename}, 不再延期")
            
        else:
            # 超过时间限制，文件可能已被删除
            print(f"超时下载请求: {filename}")

def process_next_task():
    global current_processing
    while True:
        with processing_lock:
            if task_queue and current_processing is None:
                task_id = task_queue.pop(0)
                current_processing = task_id
                task_info = task_status[task_id]
                # 更新其他任务的队列位置
                for i, waiting_task in enumerate(task_queue):
                    if waiting_task in task_status:
                        task_status[waiting_task]["queue_position"] = f"队列: {i+1}"
            else:
                task_id = None
        
        if task_id:
            try:
                process_video_background(task_id, task_info['video_path'], task_info['mode'])
            finally:
                with processing_lock:
                    current_processing = None
        else:
            time.sleep(1)

def process_video_background(task_id, video_path, mode):
    try:
        task_status[task_id]["status"] = "processing"
        task_status[task_id]["progress"] = "提取字幕中..."
        
        srt_path = f"{CACHE_DIRS['temp']}/{task_id}.srt"
        translated_srt = f"{CACHE_DIRS['outputs']}/{task_id}_translated.srt"
        
        subprocess.run([
            'python', 'video2srt.py', 
            '--source-video', video_path,
            '--dist-srt-path', srt_path,
            '--model', 'large-v3'
        ], check=True)
        
        task_status[task_id]["progress"] = "翻译字幕中..."
        subprocess.run(['python', 'tran.py', srt_path, translated_srt], check=True)
        
        if mode == "video":
            task_status[task_id]["progress"] = "合成视频中..."
            output_video = f"{CACHE_DIRS['outputs']}/{task_id}_final.mp4"
            subprocess.run(['python', 'write.py', video_path, translated_srt, output_video], check=True)
            result_file = f"{task_id}_final.mp4"
        else:
            result_file = f"{task_id}_translated.srt"
        
        # 清理临时文件
        os.remove(video_path)
        if os.path.exists(srt_path):
            os.remove(srt_path)
        
        task_status[task_id] = {
            "status": "completed", 
            "filename": result_file,
            "mode": mode
        }
        
    except Exception as e:
        task_status[task_id] = {"status": "failed", "error": str(e)}

# 启动后台处理线程 - 延迟启动避免阻塞
def start_background_worker():
    time.sleep(2)  # 延迟2秒启动
    process_next_task()

threading.Thread(target=start_background_worker, daemon=True).start()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>视频字幕处理系统</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .mode-selector { margin: 20px 0; }
        .progress { display: none; margin: 20px 0; }
        .result { margin: 20px 0; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .mode { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>视频字幕处理系统</h1>
    
    <div class="mode-selector">
        <div class="mode">
            <input type="radio" id="srt_mode" name="mode" value="srt" checked>
            <label for="srt_mode">仅生成SRT字幕文件</label>
        </div>
        <div class="mode">
            <input type="radio" id="video_mode" name="mode" value="video">
            <label for="video_mode">生成带字幕的视频文件</label>
        </div>
    </div>
    
    <div class="upload-area">
        <input type="file" id="videoFile" accept="video/*" style="display: none;">
        <button onclick="document.getElementById('videoFile').click()">选择视频文件</button>
        <p id="fileName"></p>
    </div>
    
    <button onclick="processVideo()" id="processBtn" disabled>开始处理</button>
    <button onclick="checkStatus()">查询状态</button>
    
    <div style="margin: 20px 0;">
        <input type="text" id="taskIdInput" placeholder="输入Task ID查询进度" style="padding: 8px; width: 300px;">
        <button onclick="queryTask()">查询任务</button>
    </div>
    
    <div class="progress" id="progress">
        <p>处理中...</p>
        <div id="status">准备中</div>
    </div>
    
    <div class="result" id="result"></div>

    <script>
        let selectedFile = null;
        
        document.getElementById('videoFile').addEventListener('change', function(e) {
            selectedFile = e.target.files[0];
            document.getElementById('fileName').textContent = selectedFile.name;
            document.getElementById('processBtn').disabled = false;
        });
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const result = await response.json();
                document.getElementById('result').innerHTML = 
                    `<p>系统状态: ${result.busy ? '忙碌' : '空闲'} | 队列长度: ${result.queue_length}</p>`;
            } catch (error) {
                console.error('状态查询失败:', error);
            }
        }
        
        async function queryTask() {
            const taskId = document.getElementById('taskIdInput').value.trim();
            if (!taskId) {
                alert('请输入Task ID');
                return;
            }
            
            try {
                const response = await fetch(`/api/task/${taskId}`);
                if (response.ok) {
                    const task = await response.json();
                    let statusText = '';
                    
                    if (task.status === 'queued') {
                        statusText = `排队中 (${task.queue_position || '未知'})`;
                    } else if (task.status === 'processing') {
                        statusText = `处理中: ${task.progress || ''}`;
                    } else if (task.status === 'completed') {
                        const mode = task.mode || 'srt';
                        const downloadUrl = mode === 'srt' ? 
                            `/api/download/srt/${task.filename}` : 
                            `/api/download/video/${task.filename}`;
                        statusText = `已完成 <a href="${downloadUrl}" download><button>下载文件</button></a>`;
                    } else if (task.status === 'failed') {
                        statusText = `失败: ${task.error}`;
                    }
                    
                    document.getElementById('result').innerHTML = 
                        `<p>任务 ${taskId}: ${statusText}</p>`;
                } else {
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">任务不存在</p>`;
                }
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<p style="color: red;">查询失败: ${error.message}</p>`;
            }
        }
        
        async function processVideo() {
            if (!selectedFile) return;
            
            const mode = document.querySelector('input[name="mode"]:checked').value;
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            document.getElementById('progress').style.display = 'block';
            document.getElementById('processBtn').disabled = true;
            
            try {
                const response = await fetch(`/api/process/${mode}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('result').innerHTML = 
                        `<p>任务已提交！Task ID: <strong>${result.task_id}</strong></p>
                         <p>${result.queue_position}</p>`;
                    pollTaskStatus(result.task_id, mode);
                } else {
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">处理失败: ${result.detail}</p>`;
                    document.getElementById('progress').style.display = 'none';
                    document.getElementById('processBtn').disabled = false;
                }
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<p style="color: red;">错误: ${error.message}</p>`;
                document.getElementById('progress').style.display = 'none';
                document.getElementById('processBtn').disabled = false;
            }
        }
        
        async function pollTaskStatus(taskId, mode) {
            try {
                const response = await fetch(`/api/task/${taskId}`);
                const task = await response.json();
                
                if (task.status === 'processing') {
                    document.getElementById('status').textContent = task.progress || '处理中...';
                    setTimeout(() => pollTaskStatus(taskId, mode), 2000);
                } else if (task.status === 'completed') {
                    const downloadUrl = mode === 'srt' ? 
                        `/api/download/srt/${task.filename}` : 
                        `/api/download/video/${task.filename}`;
                    
                    document.getElementById('result').innerHTML = 
                        `<p>处理完成！</p>
                         <a href="${downloadUrl}" download>
                            <button>下载${mode === 'srt' ? 'SRT字幕' : '视频文件'}</button>
                         </a>`;
                    document.getElementById('progress').style.display = 'none';
                    document.getElementById('processBtn').disabled = false;
                } else if (task.status === 'failed') {
                    document.getElementById('result').innerHTML = 
                        `<p style="color: red;">处理失败: ${task.error}</p>`;
                    document.getElementById('progress').style.display = 'none';
                    document.getElementById('processBtn').disabled = false;
                } else {
                    setTimeout(() => pollTaskStatus(taskId, mode), 1000);
                }
            } catch (error) {
                console.error('轮询错误:', error);
                setTimeout(() => pollTaskStatus(taskId, mode), 2000);
            }
        }
    </script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def get_status():
    with processing_lock:
        queue_length = len(task_queue)
        is_processing = current_processing is not None
    return jsonify({
        "busy": is_processing,
        "queue_length": queue_length,
        "current_task": current_processing
    })

@app.route("/api/process/srt", methods=['POST'])
def process_srt_only():
    return start_processing("srt")

@app.route("/api/process/video", methods=['POST']) 
def process_video_with_subtitles():
    return start_processing("video")

def start_processing(mode):
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    task_id = str(uuid.uuid4())
    video_path = f"{CACHE_DIRS['uploads']}/{task_id}_{file.filename}"
    
    # 保存上传文件
    file.save(video_path)
    
    # 添加到队列
    with processing_lock:
        task_queue.append(task_id)
        if current_processing is not None:
            queue_position = f"队列: {len(task_queue)}"
        else:
            queue_position = "队列: Now"
    
    task_status[task_id] = {
        "status": "queued",
        "mode": mode,
        "video_path": video_path,
        "queue_position": queue_position
    }
    
    return jsonify({"task_id": task_id, "status": "queued", "queue_position": queue_position})

@app.route("/api/task/<task_id>")
def get_task_status(task_id):
    if task_id not in task_status:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task_status[task_id])

@app.route("/api/download/srt/<filename>")
def download_srt(filename):
    file_path = f"{CACHE_DIRS['outputs']}/{filename}"
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 处理下载逻辑
    handle_file_download(filename)
    return send_file(file_path, as_attachment=True)

@app.route("/api/download/video/<filename>")
def download_video(filename):
    file_path = f"{CACHE_DIRS['outputs']}/{filename}"
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 处理下载逻辑
    handle_file_download(filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    print("启动Flask服务器...")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
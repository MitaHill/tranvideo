# 代码结构文档

本文档详细介绍 Tranvideo 的代码组织结构和各模块功能。

## 目录

- [项目目录结构](#项目目录结构)
- [核心模块详解](#核心模块详解)
- [API 路由映射](#api-路由映射)
- [数据模型](#数据模型)
- [工具函数库](#工具函数库)
- [开发指南](#开发指南)

---

## 项目目录结构

```
tranvideo/
├── main.py                          # 应用程序入口
├── requirements.txt                 # Python 依赖列表
├── docker-compose.yaml              # Docker Compose 配置
├── Dockerfile                       # Docker 镜像构建文件
├── .gitignore                       # Git 忽略规则
├── README.md                        # 项目说明
├── LICENSE                          # MIT 许可证
│
├── config/                          # 配置文件目录
│   ├── tran-py.json                 # 主配置文件
│   └── prompt.txt                   # 翻译提示词
│
├── src/                             # 源代码目录
│   ├── api/                         # API 层
│   │   ├── __init__.py              # 路由定义 (20+ 端点)
│   │   ├── handlers.py              # 请求处理器
│   │   ├── security.py              # 安全管理器
│   │   ├── security_modules/        # 安全模块
│   │   │   ├── __init__.py
│   │   │   ├── file_type_verification.py  # 文件类型验证
│   │   │   ├── rate_limiting.py           # 速率限制
│   │   │   └── IP_banned.py               # IP 黑名单
│   │   └── prog_bar/                # 进度跟踪
│   │       ├── __init__.py
│   │       ├── progress_tracker.py  # 进度追踪器
│   │       └── progress_manager.py  # 进度管理器
│   │
│   ├── core/                        # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── task.py                  # 任务处理器 (核心)
│   │   ├── batch.py                 # 批量处理管理器
│   │   ├── video.py                 # 视频操作封装
│   │   ├── invite.py                # 邀请码验证
│   │   ├── coordinate.py            # 任务协调器
│   │   └── coordinate_models/       # 数据库模型
│   │       ├── __init__.py
│   │       ├── database_handler.py  # 数据库I/O
│   │       ├── task_manager.py      # 任务管理器
│   │       ├── batch_manager.py     # 批次管理器
│   │       └── cleanup_manager.py   # 缓存清理器
│   │
│   ├── services/                    # 外部服务接口
│   │   ├── __init__.py
│   │   ├── use_whisper.py           # Whisper 服务接口
│   │   ├── whisper_direct.py        # Whisper 直接调用
│   │   ├── whisper_service.py       # Whisper 服务管理
│   │   ├── tran.py                  # 翻译服务 (Ollama/OpenAI)
│   │   └── enabled.py               # 启动时任务恢复
│   │
│   └── utils/                       # 工具函数库
│       ├── __init__.py
│       ├── vram_manager.py          # GPU 显存管理 (核心)
│       ├── webui.py                 # Web UI 路由
│       ├── logger.py                # 日志系统
│       ├── filer.py                 # 文件操作工具
│       ├── bilingual_subtitle.py    # 双语字幕生成
│       ├── audio_preprocessor.py    # 音频预处理
│       ├── done_timeout_delete.py   # 定时清理
│       └── tq.py                    # 队列管理
│
├── webui/                           # 前端界面
│   ├── index.html                   # 主页面
│   ├── api-docs.html                # API 文档页面
│   ├── faq.html                     # FAQ 页面
│   ├── css/                         # 样式表
│   │   └── style.css
│   ├── js/                          # JavaScript
│   │   ├── main.js                  # 主逻辑
│   │   ├── upload.js                # 上传处理
│   │   └── progress.js              # 进度显示
│   └── images/                      # 图片资源
│
├── docs/                            # 文档目录
│   ├── wiki/                        # Wiki 文档
│   │   ├── Home.md
│   │   ├── Quick-Start.md
│   │   ├── API-Reference.md
│   │   ├── Installation.md
│   │   ├── Basic-Usage.md
│   │   ├── Batch-Processing.md
│   │   ├── Configuration.md
│   │   ├── Troubleshooting.md
│   │   ├── Architecture.md
│   │   ├── Code-Structure.md
│   │   └── VRAM-Management.md
│   ├── CONTRIBUTING.md              # 贡献指南
│   ├── RELEASE_GUIDE.md             # 发布指南
│   └── VERSION_POLICY.md            # 版本策略
│
├── cache/                           # 缓存目录 (运行时生成)
│   ├── uploads/                     # 上传的视频文件
│   ├── temp/                        # 临时处理文件
│   └── outputs/                     # 输出文件
│
├── db/                              # 数据库目录
│   └── tasks.json                   # 任务数据库 (JSON)
│
├── logs/                            # 日志目录
│   └── tranvideo.log                # 应用日志
│
└── whisper/                         # Whisper 模型目录
    └── large-v3-turbo.pt            # 模型文件 (需下载)
```

---

## 核心模块详解

### 1. main.py

**功能**: 应用程序入口，Flask 应用初始化

**关键代码**:

```python
from flask import Flask
from src.api import init_routes
from src.services.enabled import recovery_tasks
from src.utils.vram_manager import init_vram_manager

app = Flask(__name__)

# 初始化路由
init_routes(app)

# 启动时恢复未完成任务
recovery_tasks()

# 初始化 VRAM 管理器
init_vram_manager()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**流程**:
1. 创建 Flask 应用
2. 注册 API 路由
3. 恢复未完成任务
4. 初始化 VRAM 管理
5. 启动服务器

---

### 2. src/api/

#### __init__.py - 路由定义

**功能**: 定义所有 API 端点

**路由分类**:

```python
def init_routes(app):
    # 健康检查
    app.route('/api/whisper/health')(health_check)
    app.route('/api/status')(system_status)

    # 配置管理
    app.route('/api/tranpy/config')(get_config)
    app.route('/api/tranpy/config-ollama-api/<api_url>')(config_ollama_api)
    # ... 更多配置路由

    # 视频处理
    app.route('/api/process/srt/<invite_code>', methods=['POST'])(process_srt)
    app.route('/api/process/video/<invite_code>', methods=['POST'])(process_video)

    # 批量处理
    app.route('/api/batch/process/<invite_code>', methods=['POST'])(batch_process)
    app.route('/api/batch/<batch_id>')(get_batch_status)
    app.route('/api/batch/download/<batch_id>')(download_batch)

    # 任务查询
    app.route('/api/task/<task_id>')(get_task_status)
    app.route('/api/query/<task_id>')(query_task)

    # 文件下载
    app.route('/api/download/srt/<filename>')(download_srt)
    app.route('/api/download/video/<filename>')(download_video)

    # Web UI
    app.route('/')(index)
    app.route('/api-docs.html')(api_docs)
    app.route('/faq.html')(faq)
```

#### handlers.py - 请求处理器

**关键函数**:

```python
def process_srt(invite_code):
    """处理视频生成字幕"""
    # 1. 验证邀请码
    if not validate_invite_code(invite_code):
        return error_response('Invalid invite code')

    # 2. 获取上传文件
    file = request.files.get('file')
    if not file:
        return error_response('No file uploaded')

    # 3. 安全验证
    if not security_check(file, request.remote_addr):
        return error_response('Security check failed')

    # 4. 保存文件
    task_id = generate_task_id()
    file_path = save_upload_file(file, task_id)

    # 5. 创建任务
    task = create_task(
        task_id=task_id,
        file_path=file_path,
        mode='srt',
        invite_code=invite_code
    )

    # 6. 加入队列
    task_queue.add(task_id)

    # 7. 返回结果
    return success_response({
        'task_id': task_id,
        'video_name': file.filename,
        'estimated_time': calculate_estimate(file_path)
    })
```

#### security.py - 安全管理器

**功能**: 统一安全验证入口

```python
class SecurityManager:
    def __init__(self):
        self.file_verifier = FileTypeVerification()
        self.rate_limiter = RateLimiting()
        self.ip_filter = IPBanned()

    def check(self, file, ip_address):
        """执行所有安全检查"""
        # 1. IP 黑名单检查
        if self.ip_filter.is_banned(ip_address):
            return False, 'IP banned'

        # 2. 速率限制检查
        if not self.rate_limiter.check(ip_address):
            return False, 'Rate limit exceeded'

        # 3. 文件类型验证
        if not self.file_verifier.verify(file):
            return False, 'Invalid file type'

        return True, 'OK'
```

---

### 3. src/core/

#### task.py - 任务处理器

**功能**: 单任务的完整处理流程

**核心函数**:

```python
class TaskProcessor:
    def process(self, task_id):
        """处理单个任务"""
        task = db.get_task(task_id)

        try:
            # 1. 更新状态: processing
            update_status(task_id, 'processing', 0)

            # 2. 提取音频
            audio_path = extract_audio(task['video_path'])
            update_status(task_id, '提取原文字幕', 10)

            # 3. 语音识别
            raw_srt = whisper_transcribe(audio_path)
            update_status(task_id, '提取原文字幕', 50)

            # 4. 生成字幕文件
            save_srt(task_id, raw_srt, 'raw')

            # 5. 翻译
            update_status(task_id, '翻译原文字幕', 50)
            translated_srt = translate(raw_srt)
            save_srt(task_id, translated_srt, 'translated')

            # 6. 双语字幕
            bilingual_srt = merge_bilingual(raw_srt, translated_srt)
            save_srt(task_id, bilingual_srt, 'bilingual')
            update_status(task_id, '翻译原文字幕', 90)

            # 7. 视频合成 (可选)
            if task['mode'] == 'video':
                update_status(task_id, '合成视频', 90)
                merge_video(task_id)

            # 8. 完成
            update_status(task_id, '已完成', 100)

        except Exception as e:
            update_status(task_id, '失败', 0, error=str(e))
            logger.error(f"Task {task_id} failed: {e}")

def extract_audio(video_path):
    """提取音频"""
    output_path = video_path.replace('.mp4', '.wav')
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1',
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def whisper_transcribe(audio_path):
    """Whisper 语音识别"""
    whisper_service = WhisperService()
    result = whisper_service.transcribe(audio_path)
    return result_to_srt(result)

def translate(srt_content):
    """翻译 SRT 字幕"""
    translator = get_translator()
    translated_lines = []

    for subtitle in parse_srt(srt_content):
        translated_text = translator.translate(subtitle.text)
        subtitle.text = translated_text
        translated_lines.append(subtitle)

    return format_srt(translated_lines)
```

#### batch.py - 批量处理

**功能**: 批量任务管理

```python
class BatchProcessor:
    def create_batch(self, files, mode, invite_code):
        """创建批量任务"""
        batch_id = generate_batch_id()
        task_ids = []

        # 为每个文件创建任务
        for file in files:
            task_id = generate_task_id()

            # 保存文件
            file_path = save_upload_file(file, task_id)

            # 创建任务
            task = create_task(
                task_id=task_id,
                file_path=file_path,
                mode=mode,
                batch_id=batch_id,
                invite_code=invite_code
            )

            task_ids.append(task_id)

            # 加入队列
            task_queue.add(task_id)

        # 创建批次记录
        batch = {
            'batch_id': batch_id,
            'task_ids': task_ids,
            'status': '队列中',
            'created_at': datetime.now()
        }

        db.save_batch(batch)

        return batch_id, task_ids
```

#### coordinate.py - 任务协调器

**功能**: 队列管理和任务调度

```python
class TaskCoordinator:
    def __init__(self):
        self.queue = Queue()
        self.current_task = None
        self.running = False

    def start(self):
        """启动协调器"""
        self.running = True
        threading.Thread(target=self._process_loop, daemon=True).start()

    def add_task(self, task_id):
        """添加任务到队列"""
        self.queue.put(task_id)
        db.update_task_status(task_id, '队列中')

    def _process_loop(self):
        """任务处理循环"""
        while self.running:
            try:
                # 从队列获取任务
                task_id = self.queue.get(timeout=1)

                # 记录当前任务
                self.current_task = task_id

                # 处理任务
                processor = TaskProcessor()
                processor.process(task_id)

                # 清空当前任务
                self.current_task = None

            except Empty:
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing task: {e}")
```

---

### 4. src/services/

#### use_whisper.py - Whisper 服务

**功能**: Whisper 模型封装

```python
class WhisperService:
    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 加载模型
        self.model = whisper.load_model(
            "large-v3-turbo",
            device="cuda",
            download_root="./whisper"
        )

        self._initialized = True

    def transcribe(self, audio_path, language=None):
        """语音识别"""
        result = self.model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            fp16=True,  # 使用 FP16 加速
            verbose=False
        )

        return result

    def to(self, device):
        """移动模型到指定设备"""
        self.model.to(device)

    def health_check(self):
        """健康检查"""
        return {
            'status': 'healthy',
            'model': 'large-v3-turbo',
            'device': str(self.model.device)
        }
```

#### tran.py - 翻译服务

**功能**: 多后端翻译服务

```python
class TranslationService:
    def __init__(self):
        self.config = load_config()

    def translate(self, text):
        """翻译文本"""
        translator_type = self.config['translator_type']

        if translator_type == 'ollama':
            return self._ollama_translate(text)
        elif translator_type == 'openai':
            return self._openai_translate(text)
        else:
            raise ValueError(f"Unknown translator: {translator_type}")

    def _ollama_translate(self, text):
        """使用 Ollama 翻译"""
        url = f"{self.config['ollama_api']}/api/generate"

        payload = {
            'model': self.config['ollama_model'],
            'prompt': self._build_prompt(text),
            'stream': False
        }

        response = requests.post(url, json=payload)
        result = response.json()

        return self._extract_translation(result['response'])

    def _openai_translate(self, text):
        """使用 OpenAI 翻译"""
        url = f"{self.config['openai_base_url']}/chat/completions"

        headers = {
            'Authorization': f"Bearer {self.config['openai_api_key']}",
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.config['openai_model'],
            'messages': [
                {'role': 'system', 'content': load_prompt()},
                {'role': 'user', 'content': text}
            ]
        }

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

        return self._extract_translation(result['choices'][0]['message']['content'])

    def _build_prompt(self, text):
        """构建提示词"""
        system_prompt = load_prompt()
        return f"{system_prompt}\n\n{text}"

    def _extract_translation(self, response):
        """提取翻译结果"""
        # 提取代码块中的内容
        match = re.search(r'```\n(.*?)\n```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
```

---

### 5. src/utils/

#### vram_manager.py - VRAM 管理器

**功能**: GPU 显存智能调度

```python
class VRAMManager:
    def __init__(self):
        self.whisper_on_gpu = True
        self.ollama_loaded = False
        self.config = load_config()

    def is_polling_enabled(self):
        """检查是否启用显存轮询"""
        return (
            self.config['translator_type'] == 'ollama' and
            '127.0.0.1' in self.config['ollama_api']
        )

    def switch_to_translation_mode(self):
        """切换到翻译模式"""
        if not self.is_polling_enabled():
            return

        logger.info("Switching to translation mode...")

        # 1. Whisper 移至 CPU
        whisper_service = WhisperService()
        whisper_service.to('cpu')
        self.whisper_on_gpu = False

        # 2. 清理 GPU 缓存
        torch.cuda.empty_cache()
        gc.collect()

        time.sleep(2)  # 等待缓存清理

        # 3. 加载 Ollama 到 GPU
        self._load_ollama_to_gpu()
        self.ollama_loaded = True

        logger.info("Translation mode activated")

    def switch_to_transcription_mode(self):
        """切换到转录模式"""
        if not self.is_polling_enabled():
            return

        logger.info("Switching to transcription mode...")

        # 1. 卸载 Ollama
        self._unload_ollama()
        self.ollama_loaded = False

        # 2. 清理 GPU 缓存
        torch.cuda.empty_cache()
        gc.collect()

        time.sleep(2)

        # 3. Whisper 移至 GPU
        whisper_service = WhisperService()
        whisper_service.to('cuda')
        self.whisper_on_gpu = True

        logger.info("Transcription mode activated")

    def _load_ollama_to_gpu(self):
        """加载 Ollama 到 GPU"""
        url = f"{self.config['ollama_api']}/api/generate"

        # 预热模型（触发加载到 GPU）
        payload = {
            'model': self.config['ollama_model'],
            'prompt': 'Hello',
            'stream': False
        }

        requests.post(url, json=payload)

    def _unload_ollama(self):
        """卸载 Ollama 模型"""
        url = f"{self.config['ollama_api']}/api/unload"

        payload = {
            'model': self.config['ollama_model']
        }

        requests.post(url, json=payload)

    def cleanup(self):
        """清理资源"""
        if self.ollama_loaded:
            self._unload_ollama()

        if not self.whisper_on_gpu:
            whisper_service = WhisperService()
            whisper_service.to('cuda')

        torch.cuda.empty_cache()
        gc.collect()
```

---

## API 路由映射

| 路径 | 方法 | 处理器 | 功能 |
|------|------|--------|------|
| `/api/whisper/health` | GET | `health_check()` | Whisper 健康检查 |
| `/api/status` | GET | `system_status()` | 系统状态 |
| `/api/tranpy/config` | GET | `get_config()` | 获取配置 |
| `/api/tranpy/config-ollama-api/<api_url>` | GET | `config_ollama_api()` | 配置 Ollama API |
| `/api/process/srt/<invite_code>` | POST | `process_srt()` | 处理视频（字幕） |
| `/api/process/video/<invite_code>` | POST | `process_video()` | 处理视频（视频） |
| `/api/batch/process/<invite_code>` | POST | `batch_process()` | 批量处理 |
| `/api/batch/<batch_id>` | GET | `get_batch_status()` | 批次状态 |
| `/api/task/<task_id>` | GET | `get_task_status()` | 任务状态 |
| `/api/download/srt/<filename>` | GET | `download_srt()` | 下载字幕 |
| `/api/download/video/<filename>` | GET | `download_video()` | 下载视频 |

完整路由列表见 [API 参考文档](API-Reference.md)。

---

## 数据模型

### 任务模型 (Task)

```python
{
    "task_id": str,              # 唯一标识
    "video_path": str,           # 视频文件路径
    "video_name": str,           # 原始文件名
    "video_duration": float,     # 视频时长（秒）
    "mode": str,                 # "srt" 或 "video"
    "status": str,               # 任务状态
    "progress": str,             # 进度描述
    "current_step": str,         # 当前步骤
    "prog_bar": int,             # 进度百分比 (0-100)
    "batch_id": str | None,      # 所属批次（可为空）
    "invite_code": str,          # 邀请码
    "created_at": str,           # 创建时间
    "updated_at": str,           # 更新时间
    "downloaded": bool,          # 是否已下载
    "expired": bool,             # 是否已过期
    "error": str | None,         # 错误信息
    "resume_data": dict          # 恢复数据
}
```

### 批次模型 (Batch)

```python
{
    "batch_id": str,             # 批次ID
    "sub_tasks": dict,           # 子任务字典
    "status": str,               # 批次状态
    "progress": str,             # 进度描述
    "created_at": str,           # 创建时间
    "updated_at": str            # 更新时间
}
```

### 配置模型 (Config)

```python
{
    "translator_type": str,      # "ollama" 或 "openai"
    "ollama_api": str,           # Ollama API 地址
    "ollama_model": str,         # Ollama 模型名称
    "openai_base_url": str,      # OpenAI Base URL
    "openai_api_key": str,       # OpenAI API Key
    "openai_model": str          # OpenAI 模型名称
}
```

---

## 工具函数库

### filer.py - 文件操作

```python
def save_upload_file(file, task_id):
    """保存上传文件"""
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    save_path = f"cache/uploads/{task_id}{ext}"

    file.save(save_path)
    return save_path

def get_video_duration(video_path):
    """获取视频时长"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())
```

### logger.py - 日志系统

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    """配置日志系统"""
    logger = logging.getLogger('tranvideo')
    logger.setLevel(logging.INFO)

    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/tranvideo.log',
        maxBytes=2*1024*1024,  # 2MB
        backupCount=5
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

---

## 开发指南

### 添加新的 API 端点

1. **在 `src/api/__init__.py` 中注册路由**:

```python
app.route('/api/new-endpoint')(new_endpoint_handler)
```

2. **在 `src/api/handlers.py` 中实现处理器**:

```python
def new_endpoint_handler():
    # 处理逻辑
    return jsonify({'success': True})
```

### 添加新的翻译器

1. **创建翻译器类** (继承基类):

```python
class CustomTranslator(BaseTranslator):
    def translate(self, text):
        # 实现翻译逻辑
        return translated_text
```

2. **注册到工厂**:

```python
# 在 tran.py 中
TRANSLATORS = {
    'ollama': OllamaTranslator,
    'openai': OpenAITranslator,
    'custom': CustomTranslator  # 新增
}
```

### 修改显存管理策略

编辑 `src/utils/vram_manager.py`：

```python
class VRAMManager:
    # 修改参数
    WHISPER_MEMORY_FRACTION = 0.85  # 降低 Whisper 显存占用
    SWITCH_DELAY = 3                 # 增加切换延迟
```

---

## 代码规范

### Python 风格

- **PEP 8** 编码规范
- **类型注解**: 使用 Type Hints
- **文档字符串**: 所有函数需要 docstring

### 命名约定

- **变量**: `snake_case`
- **函数**: `snake_case`
- **类**: `PascalCase`
- **常量**: `UPPER_SNAKE_CASE`

### 示例

```python
from typing import Dict, List, Optional

class TaskProcessor:
    """任务处理器

    处理单个视频翻译任务的完整流程。
    """

    MAX_RETRIES: int = 3

    def __init__(self, task_id: str):
        """初始化处理器

        Args:
            task_id: 任务唯一标识符
        """
        self.task_id = task_id
        self.retry_count = 0

    def process(self) -> Dict[str, any]:
        """处理任务

        Returns:
            包含处理结果的字典

        Raises:
            ProcessingError: 处理失败时抛出
        """
        # 实现...
        pass
```

---

## 测试

### 单元测试

```python
# tests/test_task.py
import unittest
from src.core.task import TaskProcessor

class TestTaskProcessor(unittest.TestCase):
    def test_extract_audio(self):
        processor = TaskProcessor('test_task')
        audio_path = processor.extract_audio('test_video.mp4')
        self.assertTrue(os.path.exists(audio_path))
```

### 运行测试

```bash
python -m pytest tests/
```

---

## 相关文档

- 📖 [架构文档](Architecture.md) - 系统架构设计
- 🔧 [API 文档](API-Reference.md) - API 接口详情
- ⚙️ [配置指南](Configuration.md) - 配置说明
- 💡 [故障排除](Troubleshooting.md) - 问题解决

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

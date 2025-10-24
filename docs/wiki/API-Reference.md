# API 完整参考手册

本文档提供 Tranvideo API 的完整参考信息，包括所有端点、参数、响应格式和使用示例。

## 基础信息

- **基础URL**: `http://your-server:5000/api`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON / multipart/form-data
- **认证方式**: 邀请码 (Invite Code)
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误描述",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

## API 端点分类

- [健康检查](#健康检查)
- [配置管理](#配置管理)
- [单视频处理](#单视频处理)
- [批量处理](#批量处理)
- [任务查询](#任务查询)
- [文件下载](#文件下载)
- [系统管理](#系统管理)

---

## 健康检查

### 检查 Whisper 服务健康状态

检查 Whisper 语音识别服务是否正常运行。

**端点**: `GET /api/whisper/health`

**请求参数**: 无

**响应示例**:

```json
{
  "status": "healthy",
  "service": "whisper",
  "model": "large-v3-turbo",
  "device": "cuda:0"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/whisper/health
```

**Python 示例**:

```python
import requests

response = requests.get("http://localhost:5000/api/whisper/health")
print(response.json())
```

### 检查系统状态

获取系统整体状态，包括队列信息、缓存使用情况等。

**端点**: `GET /api/status`

**请求参数**: 无

**响应示例**:

```json
{
  "status": "running",
  "queue": {
    "total": 3,
    "processing": 1,
    "pending": 2
  },
  "cache": {
    "uploads": 1024000000,
    "outputs": 2048000000,
    "temp": 512000000
  },
  "uptime": 86400
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/status
```

---

## 配置管理

### 获取当前配置

获取系统当前的配置信息。

**端点**: `GET /api/tranpy/config`

**请求参数**: 无

**响应示例**:

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "sk-****",
  "openai_model": "gpt-3.5-turbo"
}
```

> **注意**: API Key 会被自动遮蔽显示

**cURL 示例**:

```bash
curl http://localhost:5000/api/tranpy/config
```

### 配置 Ollama API 地址

设置 Ollama 服务的 API 地址。

**端点**: `GET /api/tranpy/config-ollama-api/{api_url}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| api_url | String | ✅ | Ollama API 地址（不含 http://） |

**响应示例**:

```json
{
  "success": true,
  "message": "Ollama API 配置成功",
  "ollama_api": "http://192.168.1.100:11434"
}
```

**cURL 示例**:

```bash
# 配置本地 Ollama
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434

# 配置远程 Ollama
curl http://localhost:5000/api/tranpy/config-ollama-api/192.168.1.100:11434
```

**Python 示例**:

```python
import requests

# URL 编码处理冒号
api_url = "192.168.1.100:11434"
url = f"http://localhost:5000/api/tranpy/config-ollama-api/{api_url}"

response = requests.get(url)
print(response.json())
```

### 配置 Ollama 模型

设置使用的 Ollama 模型名称。

**端点**: `GET /api/tranpy/config-ollama-model/{model_name}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_name | String | ✅ | Ollama 模型名称 |

**常用模型**:
- `qwen3:8b` - 推荐，中文效果好
- `llama3:8b` - 通用模型
- `deepseek-r1:8b` - 深度推理模型

**响应示例**:

```json
{
  "success": true,
  "message": "Ollama 模型配置成功",
  "ollama_model": "qwen3:8b"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

### 配置翻译器类型

选择使用 Ollama 或 OpenAI 进行翻译。

**端点**: `GET /api/tranpy/config-translator-type/{translator_type}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| translator_type | String | ✅ | `ollama` 或 `openai` |

**响应示例**:

```json
{
  "success": true,
  "message": "翻译器类型配置成功",
  "translator_type": "ollama"
}
```

**cURL 示例**:

```bash
# 使用 Ollama
curl http://localhost:5000/api/tranpy/config-translator-type/ollama

# 使用 OpenAI
curl http://localhost:5000/api/tranpy/config-translator-type/openai
```

### 配置 OpenAI Base URL

设置 OpenAI API 的 Base URL（支持兼容接口）。

**端点**: `GET /api/tranpy/config-openai-base-url/{base_url}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| base_url | String | ✅ | OpenAI API Base URL（不含 https://） |

**响应示例**:

```json
{
  "success": true,
  "message": "OpenAI Base URL 配置成功",
  "openai_base_url": "https://api.openai.com/v1"
}
```

**cURL 示例**:

```bash
# OpenAI 官方
curl http://localhost:5000/api/tranpy/config-openai-base-url/api.openai.com/v1

# 国内替代服务
curl http://localhost:5000/api/tranpy/config-openai-base-url/api.siliconflow.cn/v1
```

### 配置 OpenAI API Key

设置 OpenAI API 密钥。

**端点**: `GET /api/tranpy/config-openai-api-key/{api_key}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| api_key | String | ✅ | OpenAI API Key |

**响应示例**:

```json
{
  "success": true,
  "message": "OpenAI API Key 配置成功"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/tranpy/config-openai-api-key/sk-xxxxxxxxxxxxxxxx
```

> **安全提示**: 请勿在日志或公共场合暴露 API Key

### 配置 OpenAI 模型

设置使用的 OpenAI 模型。

**端点**: `GET /api/tranpy/config-openai-model/{model_name}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_name | String | ✅ | OpenAI 模型名称 |

**常用模型**:
- `gpt-4o` - GPT-4 优化版
- `gpt-3.5-turbo` - 性价比高
- `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` - 国内模型

**响应示例**:

```json
{
  "success": true,
  "message": "OpenAI 模型配置成功",
  "openai_model": "gpt-4o"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/tranpy/config-openai-model/gpt-4o
```

---

## 单视频处理

### 处理视频（仅生成字幕）

上传视频文件，生成 SRT 字幕文件。

**端点**: `POST /api/process/srt/{invite_code}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invite_code | String | ✅ | 邀请码 |

**请求体**:

Content-Type: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ | 视频文件 |

**支持的视频格式**:
- MP4, AVI, MOV, MKV, FLV, WMV, WEBM

**文件大小限制**: 2GB

**响应示例**:

```json
{
  "success": true,
  "task_id": "20251023_103045_abc123",
  "message": "任务已创建",
  "mode": "srt",
  "video_name": "example.mp4",
  "video_duration": 1800.5,
  "estimated_time": "约 30 分钟"
}
```

**cURL 示例**:

```bash
curl -X POST http://localhost:5000/api/process/srt/kindmita \
  -F "file=@/path/to/video.mp4"
```

**Python 示例**:

```python
import requests

url = "http://localhost:5000/api/process/srt/kindmita"
files = {"file": open("video.mp4", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"任务ID: {result['task_id']}")
print(f"预计时间: {result['estimated_time']}")
```

**JavaScript 示例**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
  'http://localhost:5000/api/process/srt/kindmita',
  {
    method: 'POST',
    body: formData
  }
);

const result = await response.json();
console.log('任务ID:', result.task_id);
```

### 处理视频（生成带字幕的视频）

上传视频文件，生成嵌入字幕的视频文件。

**端点**: `POST /api/process/video/{invite_code}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invite_code | String | ✅ | 邀请码 |

**请求体**:

Content-Type: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ | 视频文件 |

**响应示例**:

```json
{
  "success": true,
  "task_id": "20251023_104530_def456",
  "message": "任务已创建",
  "mode": "video",
  "video_name": "example.mp4",
  "video_duration": 3600.0,
  "estimated_time": "约 60 分钟"
}
```

**cURL 示例**:

```bash
curl -X POST http://localhost:5000/api/process/video/kindmita \
  -F "file=@/path/to/video.mp4"
```

**Python 示例**:

```python
import requests

url = "http://localhost:5000/api/process/video/kindmita"
files = {"file": open("video.mp4", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"任务ID: {result['task_id']}")
print(f"模式: {result['mode']}")
```

---

## 批量处理

### 创建批量任务

一次上传多个视频文件进行批量处理。

**端点**: `POST /api/batch/process/{invite_code}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invite_code | String | ✅ | 邀请码 |

**请求体**:

Content-Type: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | File[] | ✅ | 多个视频文件 |
| mode | String | ✅ | `srt` 或 `video` |

**单次批量限制**: 最多 10 个文件

**响应示例**:

```json
{
  "success": true,
  "batch_id": "batch_20251023_105500",
  "total_tasks": 5,
  "task_ids": [
    "20251023_105500_001",
    "20251023_105500_002",
    "20251023_105500_003",
    "20251023_105500_004",
    "20251023_105500_005"
  ],
  "mode": "srt",
  "total_duration": 9000.0,
  "estimated_time": "约 150 分钟"
}
```

**cURL 示例**:

```bash
curl -X POST http://localhost:5000/api/batch/process/kindmita \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "files=@video3.mp4" \
  -F "mode=srt"
```

**Python 示例**:

```python
import requests

url = "http://localhost:5000/api/batch/process/kindmita"

files = [
    ('files', open('video1.mp4', 'rb')),
    ('files', open('video2.mp4', 'rb')),
    ('files', open('video3.mp4', 'rb'))
]

data = {'mode': 'srt'}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"批次ID: {result['batch_id']}")
print(f"任务数: {result['total_tasks']}")
print(f"任务ID列表: {result['task_ids']}")
```

**JavaScript 示例**:

```javascript
const formData = new FormData();
const files = fileInput.files;

for (let i = 0; i < files.length; i++) {
  formData.append('files', files[i]);
}
formData.append('mode', 'srt');

const response = await fetch(
  'http://localhost:5000/api/batch/process/kindmita',
  {
    method: 'POST',
    body: formData
  }
);

const result = await response.json();
console.log('批次ID:', result.batch_id);
```

### 查询批量任务状态

获取批量任务的整体进度和每个子任务的状态。

**端点**: `GET /api/batch/{batch_id}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batch_id | String | ✅ | 批次ID |

**响应示例**:

```json
{
  "success": true,
  "batch_id": "batch_20251023_105500",
  "status": "processing",
  "progress": "处理中... (3/5)",
  "total": 5,
  "completed": 2,
  "processing": 1,
  "pending": 2,
  "failed": 0,
  "sub_tasks": {
    "20251023_105500_001": {
      "task_id": "20251023_105500_001",
      "video_name": "video1.mp4",
      "status": "已完成",
      "progress": "完成",
      "prog_bar": 100
    },
    "20251023_105500_002": {
      "task_id": "20251023_105500_002",
      "video_name": "video2.mp4",
      "status": "已完成",
      "progress": "完成",
      "prog_bar": 100
    },
    "20251023_105500_003": {
      "task_id": "20251023_105500_003",
      "video_name": "video3.mp4",
      "status": "翻译原文字幕",
      "progress": "翻译中...",
      "prog_bar": 65
    },
    "20251023_105500_004": {
      "task_id": "20251023_105500_004",
      "video_name": "video4.mp4",
      "status": "队列中",
      "progress": "等待处理",
      "prog_bar": 0
    },
    "20251023_105500_005": {
      "task_id": "20251023_105500_005",
      "video_name": "video5.mp4",
      "status": "队列中",
      "progress": "等待处理",
      "prog_bar": 0
    }
  },
  "created_at": "2025-10-23 10:55:00",
  "updated_at": "2025-10-23 11:30:45"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/batch/batch_20251023_105500
```

**Python 示例（带轮询）**:

```python
import requests
import time

batch_id = "batch_20251023_105500"
url = f"http://localhost:5000/api/batch/{batch_id}"

while True:
    response = requests.get(url)
    result = response.json()

    print(f"\n批次状态: {result['status']}")
    print(f"进度: {result['progress']}")
    print(f"已完成: {result['completed']}/{result['total']}")

    if result['status'] == '已完成':
        print("批次处理完成!")
        break
    elif result['status'] == '失败':
        print("批次处理失败!")
        break

    time.sleep(10)  # 每10秒查询一次
```

### 下载批量任务结果

下载批量任务的所有结果文件（ZIP 压缩包）。

**端点**: `GET /api/batch/download/{batch_id}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| batch_id | String | ✅ | 批次ID |

**响应**: ZIP 文件流

**ZIP 包内容**:
- `video1_raw.srt` - 原始语言字幕
- `video1_translated.srt` - 翻译后字幕
- `video1_final.mp4` - 带字幕视频（如果模式为 video）
- `video2_raw.srt` - ...
- ...

**cURL 示例**:

```bash
curl -o batch_result.zip \
  http://localhost:5000/api/batch/download/batch_20251023_105500
```

**Python 示例**:

```python
import requests

batch_id = "batch_20251023_105500"
url = f"http://localhost:5000/api/batch/download/{batch_id}"

response = requests.get(url)

if response.status_code == 200:
    with open(f"{batch_id}.zip", "wb") as f:
        f.write(response.content)
    print("批量结果下载完成!")
else:
    print("下载失败:", response.json())
```

---

## 任务查询

### 查询单个任务状态

获取指定任务的详细状态信息。

**端点**: `GET /api/task/{task_id}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | String | ✅ | 任务ID |

**响应示例**:

```json
{
  "success": true,
  "task_id": "20251023_103045_abc123",
  "video_name": "example.mp4",
  "video_duration": 1800.5,
  "mode": "srt",
  "status": "翻译原文字幕",
  "progress": "翻译中... (150/300)",
  "current_step": "translation",
  "prog_bar": 50,
  "batch_id": null,
  "invite_code": "kindmita",
  "created_at": "2025-10-23 10:30:45",
  "updated_at": "2025-10-23 10:45:30",
  "downloaded": false,
  "expired": false,
  "error": null
}
```

**任务状态说明**:

| 状态 | 说明 | prog_bar 范围 |
|------|------|--------------|
| 队列中 | 等待处理 | 0 |
| processing | 初始化处理 | 0-10 |
| 提取原文字幕 | Whisper 语音识别 | 10-50 |
| 翻译原文字幕 | Ollama/OpenAI 翻译 | 50-90 |
| 合成视频 | FFmpeg 嵌入字幕 | 90-100 |
| 已完成 | 处理完成 | 100 |
| 失败 | 处理失败 | - |

**cURL 示例**:

```bash
curl http://localhost:5000/api/task/20251023_103045_abc123
```

**Python 示例（带进度跟踪）**:

```python
import requests
import time

task_id = "20251023_103045_abc123"
url = f"http://localhost:5000/api/task/{task_id}"

while True:
    response = requests.get(url)
    result = response.json()

    print(f"\r状态: {result['status']} | "
          f"进度: {result['prog_bar']}% | "
          f"{result['progress']}", end='', flush=True)

    if result['status'] == '已完成':
        print("\n任务完成!")
        break
    elif result['status'] == '失败':
        print(f"\n任务失败: {result.get('error', '未知错误')}")
        break

    time.sleep(3)  # 每3秒查询一次
```

### 智能查询任务

自动识别任务ID或批次ID，返回对应的状态信息。

**端点**: `GET /api/query/{task_id}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | String | ✅ | 任务ID 或 批次ID |

**响应**: 自动识别类型返回对应数据

**cURL 示例**:

```bash
# 查询单个任务
curl http://localhost:5000/api/query/20251023_103045_abc123

# 查询批量任务
curl http://localhost:5000/api/query/batch_20251023_105500
```

---

## 文件下载

### 下载 SRT 字幕文件

下载指定任务生成的 SRT 字幕文件。

**端点**: `GET /api/download/srt/{filename}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | String | ✅ | SRT 文件名 |

**文件名格式**:
- `{task_id}_raw.srt` - 原始语言字幕
- `{task_id}_translated.srt` - 翻译后字幕
- `{task_id}_bilingual.srt` - 双语字幕

**响应**: SRT 文件流

**cURL 示例**:

```bash
# 下载原始字幕
curl -o original.srt \
  http://localhost:5000/api/download/srt/20251023_103045_abc123_raw.srt

# 下载翻译字幕
curl -o translated.srt \
  http://localhost:5000/api/download/srt/20251023_103045_abc123_translated.srt

# 下载双语字幕
curl -o bilingual.srt \
  http://localhost:5000/api/download/srt/20251023_103045_abc123_bilingual.srt
```

**Python 示例**:

```python
import requests

task_id = "20251023_103045_abc123"

# 下载翻译字幕
url = f"http://localhost:5000/api/download/srt/{task_id}_translated.srt"
response = requests.get(url)

if response.status_code == 200:
    with open("translated.srt", "wb") as f:
        f.write(response.content)
    print("字幕下载完成!")
```

### 下载带字幕的视频

下载嵌入字幕的视频文件。

**端点**: `GET /api/download/video/{filename}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | String | ✅ | 视频文件名 |

**文件名格式**: `{task_id}_final.mp4`

**响应**: 视频文件流

**cURL 示例**:

```bash
curl -o final_video.mp4 \
  http://localhost:5000/api/download/video/20251023_104530_def456_final.mp4
```

**Python 示例（带进度）**:

```python
import requests

task_id = "20251023_104530_def456"
url = f"http://localhost:5000/api/download/video/{task_id}_final.mp4"

response = requests.get(url, stream=True)
total_size = int(response.headers.get('content-length', 0))

with open("final_video.mp4", "wb") as f:
    downloaded = 0
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            progress = (downloaded / total_size) * 100
            print(f"\r下载进度: {progress:.1f}%", end='', flush=True)

print("\n视频下载完成!")
```

---

## 系统管理

### 验证邀请码

检查邀请码是否有效及其剩余配额。

**端点**: `GET /api/invitation/check/{invite_code}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invite_code | String | ✅ | 邀请码 |

**响应示例**:

```json
{
  "success": true,
  "valid": true,
  "invite_code": "kindmita",
  "remaining_time": 7200,
  "quota": {
    "used": 3600,
    "total": 10800,
    "remaining": 7200
  },
  "expires_at": "2025-10-24 10:30:00"
}
```

**cURL 示例**:

```bash
curl http://localhost:5000/api/invitation/check/kindmita
```

### 清除所有缓存（管理员）

清除所有上传、临时和输出缓存文件。

**端点**: `POST /api/administrator/delete_all_cache`

**请求体**: 无

**响应示例**:

```json
{
  "success": true,
  "message": "缓存清理完成",
  "deleted": {
    "uploads": 1024000000,
    "temp": 512000000,
    "outputs": 2048000000,
    "total": 3584000000
  }
}
```

> **注意**: 此接口仅限内网访问（127.0.0.1/192.168.x.x）

**cURL 示例**:

```bash
curl -X POST http://localhost:5000/api/administrator/delete_all_cache
```

---

## 错误代码参考

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（邀请码无效） |
| 403 | 禁止访问（IP 限制） |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 | 解决方法 |
|--------|------|---------|
| `INVALID_INVITE_CODE` | 邀请码无效 | 检查邀请码是否正确 |
| `INVITE_CODE_EXPIRED` | 邀请码已过期 | 申请新的邀请码 |
| `INSUFFICIENT_QUOTA` | 配额不足 | 等待配额恢复或联系管理员 |
| `FILE_TOO_LARGE` | 文件过大 | 文件需小于 2GB |
| `UNSUPPORTED_FORMAT` | 不支持的格式 | 使用支持的视频格式 |
| `INVALID_VIDEO_FILE` | 无效的视频文件 | 检查文件是否损坏 |
| `PROCESSING_ERROR` | 处理失败 | 查看错误详情 |
| `TASK_NOT_FOUND` | 任务不存在 | 检查任务ID是否正确 |
| `BATCH_NOT_FOUND` | 批次不存在 | 检查批次ID是否正确 |
| `FILE_NOT_FOUND` | 文件不存在 | 文件可能已过期删除 |
| `RATE_LIMIT_EXCEEDED` | 超过速率限制 | 稍后再试 |
| `IP_BANNED` | IP 已被封禁 | 联系管理员 |
| `WHISPER_SERVICE_ERROR` | Whisper 服务错误 | 检查服务状态 |
| `TRANSLATION_ERROR` | 翻译服务错误 | 检查 Ollama/OpenAI 配置 |

---

## 完整工作流示例

### Python 完整示例

```python
import requests
import time
import os

class TransvideoClient:
    def __init__(self, base_url, invite_code):
        self.base_url = base_url
        self.invite_code = invite_code

    def check_health(self):
        """检查服务健康状态"""
        response = requests.get(f"{self.base_url}/whisper/health")
        return response.json()

    def upload_video(self, file_path, mode="srt"):
        """上传视频"""
        url = f"{self.base_url}/process/{mode}/{self.invite_code}"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
        return response.json()

    def get_task_status(self, task_id):
        """获取任务状态"""
        response = requests.get(f"{self.base_url}/task/{task_id}")
        return response.json()

    def download_srt(self, task_id, output_dir="."):
        """下载字幕文件"""
        files = [
            f"{task_id}_raw.srt",
            f"{task_id}_translated.srt",
            f"{task_id}_bilingual.srt"
        ]

        for filename in files:
            url = f"{self.base_url}/download/srt/{filename}"
            response = requests.get(url)

            if response.status_code == 200:
                output_path = os.path.join(output_dir, filename)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"下载成功: {filename}")

    def wait_for_completion(self, task_id, check_interval=5):
        """等待任务完成"""
        while True:
            status = self.get_task_status(task_id)

            print(f"\r状态: {status['status']} | "
                  f"进度: {status['prog_bar']}% | "
                  f"{status['progress']}", end='', flush=True)

            if status['status'] == '已完成':
                print("\n任务完成!")
                return True
            elif status['status'] == '失败':
                print(f"\n任务失败: {status.get('error', '未知错误')}")
                return False

            time.sleep(check_interval)

# 使用示例
if __name__ == "__main__":
    client = TransvideoClient(
        base_url="http://localhost:5000/api",
        invite_code="kindmita"
    )

    # 1. 检查服务状态
    health = client.check_health()
    print(f"服务状态: {health['status']}")

    # 2. 上传视频
    result = client.upload_video("example.mp4", mode="srt")
    task_id = result['task_id']
    print(f"\n任务已创建: {task_id}")
    print(f"预计时间: {result['estimated_time']}")

    # 3. 等待处理完成
    if client.wait_for_completion(task_id):
        # 4. 下载结果
        client.download_srt(task_id, output_dir="./output")
        print("\n所有字幕文件下载完成!")
```

### JavaScript/Node.js 完整示例

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

class TransvideoClient {
  constructor(baseUrl, inviteCode) {
    this.baseUrl = baseUrl;
    this.inviteCode = inviteCode;
  }

  async checkHealth() {
    const response = await axios.get(`${this.baseUrl}/whisper/health`);
    return response.data;
  }

  async uploadVideo(filePath, mode = 'srt') {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));

    const response = await axios.post(
      `${this.baseUrl}/process/${mode}/${this.inviteCode}`,
      formData,
      { headers: formData.getHeaders() }
    );

    return response.data;
  }

  async getTaskStatus(taskId) {
    const response = await axios.get(`${this.baseUrl}/task/${taskId}`);
    return response.data;
  }

  async downloadSrt(taskId, outputDir = '.') {
    const files = [
      `${taskId}_raw.srt`,
      `${taskId}_translated.srt`,
      `${taskId}_bilingual.srt`
    ];

    for (const filename of files) {
      const url = `${this.baseUrl}/download/srt/${filename}`;
      const response = await axios.get(url, { responseType: 'stream' });

      const outputPath = path.join(outputDir, filename);
      const writer = fs.createWriteStream(outputPath);

      response.data.pipe(writer);

      await new Promise((resolve, reject) => {
        writer.on('finish', resolve);
        writer.on('error', reject);
      });

      console.log(`下载成功: ${filename}`);
    }
  }

  async waitForCompletion(taskId, checkInterval = 5000) {
    while (true) {
      const status = await this.getTaskStatus(taskId);

      process.stdout.write(
        `\r状态: ${status.status} | ` +
        `进度: ${status.prog_bar}% | ` +
        `${status.progress}`
      );

      if (status.status === '已完成') {
        console.log('\n任务完成!');
        return true;
      } else if (status.status === '失败') {
        console.log(`\n任务失败: ${status.error || '未知错误'}`);
        return false;
      }

      await new Promise(resolve => setTimeout(resolve, checkInterval));
    }
  }
}

// 使用示例
(async () => {
  const client = new TransvideoClient(
    'http://localhost:5000/api',
    'kindmita'
  );

  try {
    // 1. 检查服务状态
    const health = await client.checkHealth();
    console.log(`服务状态: ${health.status}`);

    // 2. 上传视频
    const result = await client.uploadVideo('example.mp4', 'srt');
    const taskId = result.task_id;
    console.log(`\n任务已创建: ${taskId}`);
    console.log(`预计时间: ${result.estimated_time}`);

    // 3. 等待处理完成
    if (await client.waitForCompletion(taskId)) {
      // 4. 下载结果
      await client.downloadSrt(taskId, './output');
      console.log('\n所有字幕文件下载完成!');
    }
  } catch (error) {
    console.error('错误:', error.message);
  }
})();
```

---

## 速率限制

### 限制规则

| 端点类型 | 限制 |
|---------|------|
| 上传接口 | 每IP每分钟 5 次 |
| 查询接口 | 每IP每分钟 60 次 |
| 下载接口 | 每IP每分钟 20 次 |
| 配置接口 | 仅内网访问 |

### 响应头

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1698123456
```

### 超限响应

```json
{
  "success": false,
  "error": "速率限制超出",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## 最佳实践

### 1. 错误处理

```python
import requests
from requests.exceptions import RequestException

def safe_api_call(url, **kwargs):
    try:
        response = requests.get(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("请求超时")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误: {e.response.status_code}")
        print(e.response.json())
    except RequestException as e:
        print(f"请求失败: {e}")

    return None
```

### 2. 重试机制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=2, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise

                    print(f"重试 {attempt}/{max_attempts} "
                          f"({current_delay}秒后)")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def upload_with_retry(client, file_path):
    return client.upload_video(file_path)
```

### 3. 批量处理优化

```python
import concurrent.futures

def process_videos_parallel(client, video_files, mode="srt"):
    """并行上传多个视频"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(client.upload_video, f, mode): f
            for f in video_files
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            video_file = futures[future]
            try:
                result = future.result()
                results[video_file] = result['task_id']
                print(f"上传成功: {video_file}")
            except Exception as e:
                print(f"上传失败 {video_file}: {e}")

        return results
```

### 4. 进度监控

```python
import sys

def print_progress_bar(progress, total=100, length=50):
    """打印进度条"""
    filled = int(length * progress / total)
    bar = '█' * filled + '-' * (length - filled)
    sys.stdout.write(f'\r|{bar}| {progress}%')
    sys.stdout.flush()

def monitor_task_progress(client, task_id):
    """监控任务进度并显示进度条"""
    while True:
        status = client.get_task_status(task_id)
        print_progress_bar(status['prog_bar'])

        if status['status'] in ['已完成', '失败']:
            print()  # 换行
            break

        time.sleep(3)
```

---

## 相关文档

- [快速开始](Quick-Start.md) - 快速部署指南
- [基础使用](Basic-Usage.md) - 基本功能使用
- [批量处理](Batch-Processing.md) - 批量处理指南
- [故障排除](Troubleshooting.md) - 常见问题解决

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

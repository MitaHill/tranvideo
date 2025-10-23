# API 概览

Tranvideo 提供 RESTful API 接口,支持通过 HTTP 请求进行视频翻译和字幕生成。

## 基础信息

- **基础URL**: `http://your-server:5000/api`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **认证方式**: 邀请码 (Invite Code)

## 快速开始

### 获取邀请码

公开邀请码: `kindmita`

或通过邮件申请:
- kindmitaishere@gmail.com
- rttommmr@outlook.com

### 第一个API调用

```bash
# 检查服务状态
curl http://localhost:5000/api/whisper/health

# 查看配置
curl http://localhost:5000/api/tranpy/config
```

## 核心接口

### 1. 健康检查

检查服务是否正常运行:

```bash
GET /api/whisper/health
```

**响应**:
```json
{
  "status": "healthy",
  "service": "whisper",
  "version": "0.6.0"
}
```

### 2. 视频翻译

上传视频并生成翻译字幕:

```bash
POST /api/upload
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ | 视频文件 |
| mode | String | ✅ | 处理模式: "subtitle" 或 "video" |
| invite_code | String | ✅ | 邀请码 |

**示例**:

```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@video.mp4" \
  -F "mode=subtitle" \
  -F "invite_code=kindmita"
```

**响应**:
```json
{
  "success": true,
  "task_id": "abc123def456",
  "message": "任务已创建"
}
```

### 3. 查询任务状态

```bash
GET /api/task/{task_id}/status
```

**响应**:
```json
{
  "task_id": "abc123def456",
  "status": "翻译原文字幕",
  "progress": 45,
  "created_at": "2025-10-23 10:30:00",
  "updated_at": "2025-10-23 10:32:15"
}
```

**状态值**:
- `队列中` - 等待处理
- `提取原文字幕` - 语音识别中
- `翻译原文字幕` - 翻译中
- `完成` - 处理完成
- `失败` - 处理失败

### 4. 下载结果

```bash
GET /api/download/{task_id}
```

**响应**: 文件下载 (SRT 或 MP4)

### 5. 配置管理

#### 查看当前配置

```bash
GET /api/tranpy/config
```

**响应**:
```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b"
}
```

#### 更新 Ollama API

```bash
GET /api/tranpy/config-ollama-api/{api_url}
```

**示例**:
```bash
curl http://localhost:5000/api/tranpy/config-ollama-api/192.168.1.100:11434
```

#### 更新 Ollama 模型

```bash
GET /api/tranpy/config-ollama-model/{model_name}
```

**示例**:
```bash
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

## 批量处理

### 1. 创建批量任务

```bash
POST /api/batch-upload
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | File[] | ✅ | 多个视频文件 |
| mode | String | ✅ | 处理模式 |
| invite_code | String | ✅ | 邀请码 |

**示例**:

```bash
curl -X POST http://localhost:5000/api/batch-upload \
  -F "files=@video1.mp4" \
  -F "files=@video2.mp4" \
  -F "files=@video3.mp4" \
  -F "mode=subtitle" \
  -F "invite_code=kindmita"
```

**响应**:
```json
{
  "success": true,
  "batch_id": "batch_xyz789",
  "task_ids": ["task1", "task2", "task3"],
  "total_tasks": 3
}
```

### 2. 查询批量任务状态

```bash
GET /api/batch/{batch_id}/status
```

**响应**:
```json
{
  "batch_id": "batch_xyz789",
  "total": 3,
  "completed": 2,
  "processing": 1,
  "failed": 0,
  "tasks": [
    {
      "task_id": "task1",
      "status": "完成",
      "filename": "video1.mp4"
    },
    {
      "task_id": "task2",
      "status": "完成",
      "filename": "video2.mp4"
    },
    {
      "task_id": "task3",
      "status": "翻译原文字幕",
      "filename": "video3.mp4"
    }
  ]
}
```

### 3. 下载批量结果

```bash
GET /api/batch/{batch_id}/download
```

**响应**: ZIP 压缩包 (包含所有结果文件)

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

### 常见错误码

| 错误码 | 说明 | 解决方法 |
|-------|------|---------|
| `INVALID_INVITE_CODE` | 邀请码无效 | 检查邀请码是否正确 |
| `FILE_TOO_LARGE` | 文件过大 | 压缩视频或分割上传 |
| `UNSUPPORTED_FORMAT` | 不支持的格式 | 使用 MP4/AVI/MOV 格式 |
| `INSUFFICIENT_QUOTA` | 配额不足 | 等待配额恢复或联系管理员 |
| `PROCESSING_ERROR` | 处理失败 | 查看任务详情获取具体原因 |

## 速率限制

- **上传频率**: 每IP每分钟最多 5 次请求
- **文件大小**: 单文件最大 2GB
- **并发任务**: 单次最多 10 个任务

## SDK 和示例

### Python 示例

```python
import requests

# 配置
API_BASE = "http://localhost:5000/api"
INVITE_CODE = "kindmita"

def upload_video(file_path, mode="subtitle"):
    """上传视频进行翻译"""
    url = f"{API_BASE}/upload"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'mode': mode,
            'invite_code': INVITE_CODE
        }

        response = requests.post(url, files=files, data=data)
        return response.json()

def check_status(task_id):
    """检查任务状态"""
    url = f"{API_BASE}/task/{task_id}/status"
    response = requests.get(url)
    return response.json()

def download_result(task_id, output_path):
    """下载处理结果"""
    url = f"{API_BASE}/download/{task_id}"
    response = requests.get(url)

    with open(output_path, 'wb') as f:
        f.write(response.content)

# 使用示例
result = upload_video("video.mp4")
task_id = result['task_id']
print(f"任务创建成功: {task_id}")

# 轮询状态
import time
while True:
    status = check_status(task_id)
    print(f"状态: {status['status']}")

    if status['status'] == '完成':
        download_result(task_id, "result.srt")
        print("下载完成!")
        break
    elif status['status'] == '失败':
        print("处理失败!")
        break

    time.sleep(5)
```

### JavaScript 示例

```javascript
// 上传视频
async function uploadVideo(file, inviteCode) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', 'subtitle');
  formData.append('invite_code', inviteCode);

  const response = await fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// 检查状态
async function checkStatus(taskId) {
  const response = await fetch(
    `http://localhost:5000/api/task/${taskId}/status`
  );
  return await response.json();
}

// 使用示例
const fileInput = document.querySelector('#video-file');
const file = fileInput.files[0];

const result = await uploadVideo(file, 'kindmita');
console.log('Task ID:', result.task_id);

// 轮询状态
const interval = setInterval(async () => {
  const status = await checkStatus(result.task_id);
  console.log('Status:', status.status);

  if (status.status === '完成') {
    clearInterval(interval);
    window.location.href =
      `/api/download/${result.task_id}`;
  }
}, 5000);
```

## 完整 API 文档

详细的API接口文档请访问:

📖 [https://tranvideo.clash.ink/api-docs.html](https://tranvideo.clash.ink/api-docs.html)

## 相关资源

- [认证机制](API-Authentication.md) - API认证详解
- [任务管理](API-Tasks.md) - 任务管理接口
- [故障排除](Troubleshooting.md) - 常见问题

---

[返回 Wiki 首页](Home.md)

# 配置指南

本文档详细介绍 Tranvideo 的配置选项和最佳实践。

## 目录

- [配置文件概述](#配置文件概述)
- [主配置文件](#主配置文件)
- [翻译提示词配置](#翻译提示词配置)
- [Docker 环境配置](#docker-环境配置)
- [Ollama 配置](#ollama-配置)
- [OpenAI 配置](#openai-配置)
- [显存管理配置](#显存管理配置)
- [日志配置](#日志配置)
- [安全配置](#安全配置)

---

## 配置文件概述

### 配置文件位置

```
tranvideo/
├── config/
│   ├── tran-py.json      # 主配置文件
│   └── prompt.txt        # 翻译提示词
├── .env                   # 环境变量（可选）
└── docker-compose.yaml    # Docker配置
```

### 配置优先级

1. 环境变量（最高优先级）
2. `config/tran-py.json`
3. 默认值（最低优先级）

---

## 主配置文件

### 文件路径

`config/tran-py.json`

### 完整配置示例

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx",
  "openai_model": "gpt-3.5-turbo"
}
```

### 配置项说明

#### translator_type

选择翻译服务类型。

**类型**: String

**可选值**:
- `"ollama"` - 使用本地 Ollama 服务
- `"openai"` - 使用 OpenAI 兼容 API

**默认值**: `"ollama"`

**示例**:

```json
{
  "translator_type": "ollama"
}
```

**影响**:
- 决定使用哪个翻译服务
- 影响显存轮询是否启用
- 影响翻译速度和质量

#### ollama_api

Ollama 服务的 API 地址。

**类型**: String

**格式**: `http://host:port`

**默认值**: `"http://127.0.0.1:11434"`

**重要**:
- 使用 `127.0.0.1` 启用显存轮询
- 使用 `localhost` 不启用显存轮询

**示例**:

```json
{
  "ollama_api": "http://127.0.0.1:11434"  // 本地，启用显存轮询
}
```

```json
{
  "ollama_api": "http://192.168.1.100:11434"  // 远程，不启用显存轮询
}
```

#### ollama_model

使用的 Ollama 模型名称。

**类型**: String

**推荐模型**:

| 模型 | 大小 | 速度 | 质量 | 适用场景 |
|------|------|------|------|---------|
| qwen3:8b | 8B | ⚡⚡⚡ | ⭐⭐⭐ | 推荐，中文效果好 |
| qwen3:14b | 14B | ⚡⚡ | ⭐⭐⭐⭐ | 更高质量 |
| llama3:8b | 8B | ⚡⚡⚡ | ⭐⭐⭐ | 通用 |
| deepseek-r1:8b | 8B | ⚡⚡ | ⭐⭐⭐⭐ | 深度推理 |

**默认值**: `"qwen3:8b"`

**示例**:

```json
{
  "ollama_model": "qwen3:8b"
}
```

**拉取模型**:

```bash
# 拉取推荐模型
ollama pull qwen3:8b

# 拉取其他模型
ollama pull llama3:8b
ollama pull deepseek-r1:8b
```

#### openai_base_url

OpenAI API 的 Base URL。

**类型**: String

**格式**: `https://host/path`

**默认值**: `"https://api.openai.com/v1"`

**兼容服务**:

```json
{
  // OpenAI 官方
  "openai_base_url": "https://api.openai.com/v1"
}
```

```json
{
  // Azure OpenAI
  "openai_base_url": "https://your-resource.openai.azure.com"
}
```

```json
{
  // 国内替代服务（示例）
  "openai_base_url": "https://api.siliconflow.cn/v1"
}
```

#### openai_api_key

OpenAI API 密钥。

**类型**: String

**格式**: `sk-xxxxxxxxxxxxxxxx`

**安全提示**:
- 不要公开分享 API Key
- 定期轮换密钥
- 设置使用限额
- 监控使用情况

**示例**:

```json
{
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

**环境变量方式（更安全）**:

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

#### openai_model

使用的 OpenAI 模型。

**类型**: String

**推荐模型**:

| 模型 | 速度 | 质量 | 成本 | 适用场景 |
|------|------|------|------|---------|
| gpt-4o | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | 高质量翻译 |
| gpt-4o-mini | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰💰 | 性价比高 |
| gpt-3.5-turbo | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | 快速翻译 |

**默认值**: `"gpt-3.5-turbo"`

**示例**:

```json
{
  "openai_model": "gpt-4o-mini"
}
```

---

## 翻译提示词配置

### 文件路径

`config/prompt.txt`

### 默认提示词

```
你是专业翻译。将外语翻译成自然流畅的中文，保持原意可适当润色修饰。只输出代码块格式：``````，将译文内容放入代码块中，不要有其它提示性内容。
```

### 自定义提示词

#### 示例一：正式翻译风格

```
你是专业翻译。将外语翻译成正式、准确的中文，保持学术风格。
仅输出翻译结果，使用代码块格式：``````
```

#### 示例二：口语化风格

```
你是专业翻译。将外语翻译成口语化、易懂的中文，适合日常交流。
只输出代码块格式的译文：``````
```

#### 示例三：技术文档风格

```
你是技术翻译专家。将技术文档翻译成准确的中文，保留专业术语。
专业术语用英文标注，格式：中文（English）
仅输出代码块格式：``````
```

#### 示例四：翻译为英文

```
You are a professional translator. Translate the text into natural English.
Output only the translation in code block format: ``````
```

#### 示例五：翻译为日文

```
あなたはプロの翻訳者です。テキストを自然な日本語に翻訳してください。
翻訳結果のみをコードブロック形式で出力してください：``````
```

### 提示词最佳实践

1. **明确输出格式**：要求输出代码块格式 ``````
2. **指定翻译风格**：明确翻译风格（正式/口语/技术等）
3. **简洁清晰**：避免过长的提示词
4. **保持一致性**：整个批次使用相同的提示词

---

## Docker 环境配置

### docker-compose.yaml

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    network_mode: host
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: always

  tranvideo:
    image: kindmitaishere/tranvideo:0.6.0
    container_name: tranvideo
    depends_on:
      - ollama
    network_mode: host
    volumes:
      - ./cache:/root/tranvideo/cache
      - ./config:/root/tranvideo/config  # 挂载配置目录
      - ./logs:/root/tranvideo/logs      # 挂载日志目录
    environment:
      - OLLAMA_HOST=http://127.0.0.1:11434
      - TRANSLATOR_TYPE=ollama
      - LOG_LEVEL=INFO
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
        limits:
          memory: 16G
    restart: always

volumes:
  ollama_data:
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| OLLAMA_HOST | Ollama 服务地址 | http://127.0.0.1:11434 |
| TRANSLATOR_TYPE | 翻译器类型 | ollama |
| LOG_LEVEL | 日志级别 | INFO |
| OPENAI_API_KEY | OpenAI API Key | - |

### 资源限制配置

```yaml
deploy:
  resources:
    reservations:
      memory: 8G
      cpus: '4'
    limits:
      memory: 16G
      cpus: '8'
```

---

## Ollama 配置

### 本地部署配置

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b"
}
```

**特点**:
- ✅ 启用显存轮询
- ✅ 8GB 显存即可运行
- ✅ 无 API 成本
- ⚠️ 需要本地 GPU

### 远程 Ollama 配置

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://192.168.1.100:11434",
  "ollama_model": "qwen3:8b"
}
```

**特点**:
- ❌ 不启用显存轮询
- ⚠️ 需要更多显存（~12GB）
- ✅ 可使用远程 GPU
- ✅ 多用户共享

### Ollama 服务配置

#### 修改监听地址

允许远程访问 Ollama：

```bash
# 编辑环境变量
export OLLAMA_HOST=0.0.0.0:11434

# 或修改 systemd 服务
sudo systemctl edit ollama
```

添加：

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

重启服务：

```bash
sudo systemctl restart ollama
```

#### 设置并发数

```bash
export OLLAMA_NUM_PARALLEL=2  # 并发请求数
export OLLAMA_MAX_LOADED_MODELS=1  # 同时加载的模型数
```

---

## OpenAI 配置

### OpenAI 官方

```json
{
  "translator_type": "openai",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx",
  "openai_model": "gpt-4o-mini"
}
```

### Azure OpenAI

```json
{
  "translator_type": "openai",
  "openai_base_url": "https://your-resource.openai.azure.com",
  "openai_api_key": "your-azure-api-key",
  "openai_model": "gpt-4"
}
```

### 国内替代服务

```json
{
  "translator_type": "openai",
  "openai_base_url": "https://api.siliconflow.cn/v1",
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx",
  "openai_model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"
}
```

### 成本优化

#### 模型选择

| 需求 | 推荐模型 | 原因 |
|------|---------|------|
| 低成本 | gpt-3.5-turbo | 最便宜 |
| 平衡 | gpt-4o-mini | 性价比高 |
| 高质量 | gpt-4o | 最佳质量 |

#### 批量处理优化

使用批量 API（如果支持）降低成本：

```python
# 批量翻译可节省成本
batch_size = 10
```

---

## 显存管理配置

### 启用显存轮询

**前提条件**:

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434"  // 必须是 127.0.0.1
}
```

### 禁用显存轮询

**方式一**：使用远程 Ollama

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://192.168.1.100:11434"
}
```

**方式二**：使用 OpenAI

```json
{
  "translator_type": "openai"
}
```

### 显存优化参数

源码部署可修改 `src/utils/vram_manager.py`：

```python
class VRAMManager:
    # Whisper 显存限制（90%）
    WHISPER_MEMORY_FRACTION = 0.9

    # 模型切换延迟（秒）
    SWITCH_DELAY = 2

    # 垃圾回收频率
    GC_INTERVAL = 10
```

---

## 日志配置

### 日志级别

修改 `main.py` 或环境变量：

```python
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

**级别说明**:

| 级别 | 用途 |
|------|------|
| DEBUG | 详细调试信息 |
| INFO | 一般信息（默认） |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

### 日志轮转配置

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/tranvideo.log',
    maxBytes=2*1024*1024,  # 2MB
    backupCount=5          # 保留5个备份
)
```

### 日志格式

```python
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

---

## 安全配置

### 邀请码配置

邀请码配置文件（需自行实现）：

```json
{
  "invitations": {
    "kindmita": {
      "quota": 10800,
      "used": 0,
      "expires_at": "2025-12-31 23:59:59"
    }
  }
}
```

### IP 限流配置

位置: `src/api/security_modules/rate_limiting.py`

```python
# 限流配置
RATE_LIMITS = {
    'upload': 5,      # 每分钟5次上传
    'query': 60,      # 每分钟60次查询
    'download': 20    # 每分钟20次下载
}
```

### IP 黑名单

位置: `src/api/security_modules/IP_banned.py`

```python
# 黑名单 IP
BANNED_IPS = [
    '192.168.1.100',
    '10.0.0.50'
]
```

### 文件类型验证

位置: `src/api/security_modules/file_type_verification.py`

```python
# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'mp4', 'avi', 'mov', 'mkv',
    'flv', 'wmv', 'webm'
}

# 最大文件大小（字节）
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
```

---

## 通过 API 动态配置

### 查看当前配置

```bash
curl http://localhost:5000/api/tranpy/config
```

### 配置 Ollama

```bash
# 配置 API 地址
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434

# 配置模型
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b

# 设置翻译器类型
curl http://localhost:5000/api/tranpy/config-translator-type/ollama
```

### 配置 OpenAI

```bash
# 配置 Base URL
curl http://localhost:5000/api/tranpy/config-openai-base-url/api.openai.com/v1

# 配置 API Key
curl http://localhost:5000/api/tranpy/config-openai-api-key/sk-xxxxxxxx

# 配置模型
curl http://localhost:5000/api/tranpy/config-openai-model/gpt-4o-mini

# 设置翻译器类型
curl http://localhost:5000/api/tranpy/config-translator-type/openai
```

---

## 配置模板

### 模板一：8GB 显存本地部署

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "",
  "openai_api_key": "",
  "openai_model": ""
}
```

### 模板二：12GB+ 显存远程 Ollama

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://192.168.1.100:11434",
  "ollama_model": "qwen3:14b",
  "openai_base_url": "",
  "openai_api_key": "",
  "openai_model": ""
}
```

### 模板三：纯 OpenAI

```json
{
  "translator_type": "openai",
  "ollama_api": "",
  "ollama_model": "",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx",
  "openai_model": "gpt-4o-mini"
}
```

### 模板四：混合配置（可切换）

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "sk-xxxxxxxxxxxxxxxx",
  "openai_model": "gpt-4o-mini"
}
```

---

## 配置备份与恢复

### 备份配置

```bash
# 备份配置目录
cp -r config config_backup_$(date +%Y%m%d)

# 或创建配置快照
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

### 恢复配置

```bash
# 从备份恢复
cp -r config_backup_20251023 config

# 或从快照恢复
tar -xzf config_backup_20251023.tar.gz
```

### 配置版本控制

```bash
# 初始化 git
cd config
git init
git add .
git commit -m "Initial config"

# 修改后提交
git add tran-py.json
git commit -m "Update Ollama model to qwen3:14b"
```

---

## 故障排除

### 配置不生效

1. 检查 JSON 格式是否正确
2. 重启服务
3. 查看日志中的配置加载信息

### API Key 无效

1. 检查 API Key 是否正确
2. 检查 API Key 是否过期
3. 检查配额是否用完

### 模型加载失败

1. 检查模型是否已拉取
2. 检查 Ollama 服务是否运行
3. 检查显存是否充足

---

## 相关文档

- 📖 [安装指南](Installation.md) - 安装和部署
- 🎯 [显存管理](VRAM-Management.md) - 显存优化详解
- 🔧 [API 文档](API-Reference.md) - API 接口
- 💡 [故障排除](Troubleshooting.md) - 问题解决

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

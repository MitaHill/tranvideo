# Tranvideo - AI 视频字幕翻译平台

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![GPU](https://img.shields.io/badge/GPU-CUDA-orange.svg)

一个基于 Whisper Large V3 和 Ollama 的智能视频字幕提取与翻译平台，支持批量处理和多种输出方式。

## ✨ 主要功能

- 🎵 **提取**: 从视频文件中自动提取高质量音频
- 🎯 **识别**: 使用 Whisper Large V3 模型进行精准语音转文字
- 🌍 **翻译**: 集成 Ollama进行自然流畅的中文翻译
- 📝 **字幕**: 自动生成 SRT 格式字幕文件
- 🎬 **视频合成**: 将翻译后的字幕烧录到原视频中
- 📦 **批量处理**: 支持多文件同时处理和批量下载
- ⚡ **GPU 加速**: 充分利用 CUDA 进行高效处理

## 🎨 Web 界面预览

- 简洁直观的 Web 界面
- 邀请码验证系统
- 文件时长预检查
- 队列管理和状态监控

## 🚀 快速开始

### 方式一: Docker Compose（推荐）

1. **创建 docker-compose.yml**
```yaml
version: '3.8'

services:
  tranvideo:
    image: docker.io/kindmitaishere/tranvideo-v1.0:latest
    container_name: tranvideo-app
    restart: unless-stopped
    
    ports:
      - "5000:5000"
      - "2222:22"
    
    volumes:
      - ./data:/root/tranvideo/cache
      - ./logs:/root/tranvideo/log
      - ./config:/root/tranvideo/config
    
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

2. **启动服务**
```bash
# 创建必要目录
mkdir -p data logs config

# 启动容器
docker-compose up -d

# 查看启动日志
docker-compose logs -f tranvideo
```

### 方式二: Docker 命令

```bash
docker run -d \
  --name tranvideo-app \
  --gpus all \
  -p 5000:5000 \
  -p 2222:22 \
  -v $(pwd)/data:/root/tranvideo/cache \
  -v $(pwd)/logs:/root/tranvideo/log \
  -v $(pwd)/config:/root/tranvideo/config \
  kindmitaishere/tranvideo-v1.0:latest
```

## ⚙️ 初始配置

### 1. 配置 Ollama API

> ⚠️ **前提条件**: 需要先部署 Ollama 服务并安装 qwen3:8b 模型

访问以下 URL 配置 API 地址：
```
http://localhost:5000/api/tranpy/config-ollama-api/你的ollama地址:端口
```

**示例**:
```
http://localhost:5000/api/tranpy/config-ollama-api/192.168.1.100:11435
```

### 2. 配置翻译模型

```
http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

### 3. 验证配置

访问配置查看接口：
```
http://localhost:5000/api/tranpy/config
```

## 📖 使用指南

### 基础使用流程

1. **打开 Web 界面**
   ```
   http://localhost:5000
   ```

2. **输入邀请码**
   ```
   kindmita
   ```

3. **上传视频文件**
   - 支持常见视频格式（MP4, AVI, MOV 等）
   - 自动检查视频时长
   - 显示预估处理时间

4. **选择处理模式**
   - **仅字幕**: 输出 SRT 字幕文件
   - **视频+字幕**: 输出带字幕的视频文件

5. **监控处理进度**
   - 实时显示当前处理状态
   - 队列位置和预估完成时间
   - 详细的处理步骤信息

6. **下载结果**
   - 处理完成后自动提供下载链接
   - 支持批量下载打包文件

### 批量处理

1. 选择多个视频文件
2. 系统会自动计算总时长
3. 验证可用时长是否充足
4. 所有文件将按顺序处理
5. 完成后提供批量下载

### API 接口

#### 健康检查
```bash
curl http://localhost:5000/api/whisper/health
```

#### 邀请码验证
```bash
curl http://localhost:5000/api/invitation/check/kindmita
```

#### 任务状态查询
```bash
curl http://localhost:5000/api/task/{task_id}
```

## 🛠️ 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB RAM（推荐 16GB）
- **显存**: 16GB VRAM 或更多
- **存储**: 32GB 可用空间
- **GPU**: 支持 CUDA 的 NVIDIA 显卡

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Runtime
- CUDA 11.0+

### 日志管理

- 日志自动轮转，单文件最大 2MB
- 日志文件位置: `./logs/`
- 支持实时日志查看

### 性能优化

1. **GPU 显存优化**
   - Whisper 模型内存使用限制为 60%
   - 自动缓存清理和垃圾回收
   - 经测试，空载状态下显存占用为6.5-7GB

2. **并发处理**
   - 单任务队列，避免资源冲突
   - 可以充分利用常驻显存的模型，实现快速调用处理视频。

## 🐛 故障排除

### 常见问题

**Q: 容器启动失败**
```bash
# 检查 GPU 支持
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**Q: Whisper 服务未启动**
```bash
# 检查服务状态
curl http://localhost:5000/api/whisper/health

# 查看容器日志
docker-compose logs tranvideo
```

**Q: 翻译功能异常**
```bash
# 验证 Ollama 连接
curl http://your-ollama-server:11435/api/tags

# 检查配置
curl http://localhost:5000/api/tranpy/config
```

### 性能调优

- 根据显卡性能调整批处理大小
- 监控显存使用情况
- 适当调整并发任务数量

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔑API调用方式


这是一个基于Flask的视频字幕处理服务，主要API包括：

### 核心处理
- `POST /api/process/srt/<invite_code>` - 生成SRT字幕文件
- `POST /api/process/video/<invite_code>` - 生成带字幕的视频
- `POST /api/batch/process/<invite_code>` - 批量处理多个文件

### 状态查询
- `GET /api/task/<task_id>` - 查询单个任务状态
- `GET /api/batch/<batch_id>` - 查询批量任务状态
- `GET /api/status` - 查询系统处理状态

### 下载
- `GET /api/download/srt/<filename>` - 下载SRT文件
- `GET /api/download/video/<filename>` - 下载视频文件
- `GET /api/batch/download/<batch_id>` - 下载批量处理结果

## 配置管理
- `GET /api/tranpy/config-ollama-api/<api_url>` - 配置Ollama API地址
- `GET /api/tranpy/config-ollama-model/<model_name>` - 配置Ollama模型
- `GET /api/tranpy/config` - 获取当前配置

## 辅助功能
- `GET /api/invitation/check/<invite_code>` - 验证邀请码及可用时长
- `GET /api/whisper/health` - 检查Whisper服务状态
- `POST /api/administrator/delete_all_cache` - 清理缓存文件

系统使用邀请码控制访问，支持视频时长限制，集成Whisper进行语音识别和翻译。


## 📞 联系方式

- **邮箱**: kindmitaishere@gmail.com
- **备用邮箱**: rttommmr@outlook.com
- **网站**: [b.clash.ink](http://b.clash.ink)

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [Ollama](https://ollama.ai/) - 便捷的大模型部署工具
- [Qwen](https://github.com/QwenLM/Qwen) - 优秀的中文大语言模型

---

⭐ 如果这个项目对你有帮助，请给一个 Star！

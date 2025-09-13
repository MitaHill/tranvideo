# Tranvideo 项目总结

## 项目概述

**Tranvideo** 是一个基于人工智能的视频翻译自动化平台，专门用于将视频内容进行语音识别、翻译和字幕生成。该项目采用最先进的 AI 技术栈，包括 OpenAI Whisper Large V3 语音识别模型和 Ollama 大语言模型进行翻译。

## 核心技术架构

### 主要技术组件
1. **语音识别引擎**: OpenAI Whisper Large V3
2. **翻译引擎**: Ollama (支持 qwen3:8b 等多种模型)
3. **Web 框架**: Flask
4. **视频处理**: FFmpeg
5. **容器化**: Docker + Docker Compose
6. **GPU 加速**: CUDA 支持

### 系统架构
```
视频输入 → 音频提取 → Whisper 语音识别 → 原文字幕生成 
    ↓
翻译文本 ← Ollama API 调用 ← 字幕文本分析
    ↓
字幕文件生成 → 视频字幕合成 → 最终输出
```

## 主要功能特性

### 🎵 音频提取
- 自动从视频文件中提取高质量音频
- 支持多种视频格式（MP4, AVI, MOV 等）
- 优化音频参数以提高识别准确率

### 🎯 语音识别
- 使用 Whisper Large V3 模型进行高精度语音转文字
- 支持多语言语音识别
- 自动生成时间戳精确的字幕片段

### 🌍 智能翻译
- 集成 Ollama API 进行文本翻译
- 支持多种大语言模型 (如 qwen3:8b)
- 逐句翻译，保持语境连贯性

### 📝 字幕生成
- 自动生成标准 SRT 格式字幕文件
- 精确的时间同步
- 支持多语言字幕输出

### 🎬 视频合成
- 将翻译后的字幕嵌入到原视频中
- 自动适配视频分辨率调整字体大小
- 优化的字幕样式（颜色、描边、阴影）

### 📦 批量处理
- 支持多视频文件同时处理
- 队列管理系统
- 批量下载功能

### ⚡ 性能优化
- GPU 加速处理
- 内存管理和垃圾回收
- 异步任务队列
- 文件自动清理机制

## 项目文件结构

```
tranvideo/
├── main.py                 # 主应用入口
├── video2srt.py           # 视频转字幕独立模块
├── tran.py                # 翻译模块（NLLB-200）
├── write.py               # 字幕嵌入模块
├── config/                # 配置文件目录
│   └── tran-py.json      # Ollama API 配置
├── src/                   # 源代码目录
│   ├── api/              # API 接口层
│   ├── core/             # 核心业务逻辑
│   ├── services/         # 服务层
│   └── utils/            # 工具函数
├── webui/                # Web 界面
│   ├── index.html        # 主界面
│   ├── api-docs.html     # API 文档
│   ├── css/              # 样式文件
│   └── js/               # JavaScript 文件
├── log/                  # 日志目录
└── db/                   # 数据库目录
```

## 核心业务流程

### 1. 任务提交
```python
# 通过 Web 界面或 API 提交视频文件
# 系统验证文件格式和邀请码
# 添加到任务队列
```

### 2. 音频处理
```python
# FFmpeg 提取音频 (16kHz, 单声道)
# 临时文件管理
# 音频质量优化
```

### 3. 语音识别
```python
# Whisper 服务调用
# 生成原始字幕片段
# 时间戳精确对齐
```

### 4. 文本翻译
```python
# Ollama API 调用
# 逐句翻译处理
# 上下文保持
```

### 5. 输出生成
```python
# SRT 字幕文件生成
# 可选视频合成
# 文件下载链接
```

## 系统要求

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
- Python 3.8+

## 性能表现

### 测试环境
- **硬件**: V100 GPU (16GB 显存)
- **模型**: Whisper Large V3 + qwen:8b
- **测试样本**: 30分钟视频

### 性能指标
- **处理时间**: 约 10 分钟（30分钟视频）
- **显存占用**: 空载 6.5-7GB，满载 14-15GB
- **处理比例**: 约 3:1 (处理速度:视频长度)

## 部署方式

### Docker Compose（推荐）
```yaml
version: '3.8'
services:
  tranvideo:
    image: kindmitaishere/tranvideo-v1.0:latest
    ports:
      - "5000:5000"
    volumes:
      - ./data:/root/tranvideo/cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 源码运行
```bash
# 安装依赖
pip install -r requirements.txt

# 配置 Ollama API
curl http://localhost:5000/api/tranpy/config-ollama-api/your-ollama-url:11434

# 启动服务
python main.py
```

## API 接口

### 主要端点
- `POST /api/upload` - 文件上传
- `GET /api/status/{task_id}` - 任务状态查询
- `GET /api/download/{file_id}` - 文件下载
- `GET /api/tranpy/config` - 配置查看
- `POST /api/tranpy/config-ollama-api/{url}` - Ollama 配置

### 认证系统
- 邀请码验证机制
- 默认公开邀请码: `kindmita`
- 自定义邀请码管理

## 安全特性

### 文件管理
- 自动文件清理 (24小时超时)
- 临时文件隔离
- 上传文件验证

### 访问控制
- 邀请码验证
- 任务队列管理
- 资源使用限制

## 技术亮点

### 1. 智能资源管理
- GPU 显存优化分配
- 模型常驻内存，减少加载时间
- 自动垃圾回收机制

### 2. 高效处理流水线
- 异步任务队列
- 流式处理降低延迟
- 批量操作优化

### 3. 用户体验优化
- 实时进度反馈
- 直观的 Web 界面
- 多种输出格式选择

### 4. 扩展性设计
- 模块化架构
- 可插拔翻译引擎
- 容器化部署

## 应用场景

- **教育培训**: 外语视频课程本地化
- **内容创作**: 多语言视频内容制作
- **企业培训**: 国际化培训材料制作
- **媒体制作**: 影视内容字幕翻译
- **学术研究**: 多语言学术资料处理

## 开发与维护

### 项目状态
- 活跃开发中
- MIT 许可证
- 社区贡献友好
- 持续更新维护

### 技术支持
- **邮箱**: kindmitaishere@gmail.com
- **备用邮箱**: rttommmr@outlook.com
- **网站**: [b.clash.ink](http://b.clash.ink)
- **公开 API**: https://tranvideo.clash.ink/api

## 总结

Tranvideo 是一个技术先进、功能完整的视频翻译自动化解决方案。它结合了最新的 AI 技术和优秀的工程实践，为用户提供了高效、准确、易用的视频翻译服务。项目的模块化架构和容器化部署方式使其具有良好的可扩展性和维护性，适合个人用户和企业级应用。

通过 Whisper Large V3 的高精度语音识别和 Ollama 的强大翻译能力，该项目能够处理各种类型的视频内容，并生成高质量的翻译字幕。GPU 加速和优化的处理流水线确保了良好的性能表现，使得大规模视频处理成为可能。

该项目代表了当前 AI 辅助视频处理领域的先进水平，为多语言内容创作和传播提供了强有力的技术支持。
# Tranvideo - 自部署的翻译视频项目

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![GPU](https://img.shields.io/badge/GPU-CUDA-orange.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)

![GitHub Repo stars](https://img.shields.io/github/stars/MitaHill/tranvideo?style=social)
![GitHub forks](https://img.shields.io/github/forks/MitaHill/tranvideo?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/MitaHill/tranvideo?style=social)
![GitHub issues](https://img.shields.io/github/issues/MitaHill/tranvideo)
![GitHub pull requests](https://img.shields.io/github/issues-pr/MitaHill/tranvideo)
![GitHub last commit](https://img.shields.io/github/last-commit/MitaHill/tranvideo)
![GitHub repo size](https://img.shields.io/github/repo-size/MitaHill/tranvideo)
![GitHub language count](https://img.shields.io/github/languages/count/MitaHill/tranvideo)
![GitHub top language](https://img.shields.io/github/languages/top/MitaHill/tranvideo)

一个基于 Whisper Large V3 和 Ollama 的视频翻译项目。

将视频使用`Whisper Large V3`进行提取字幕，

并使用Ollama模型进行翻译，最后输出字幕到视频中。

支持批量处理和多种输出方式。

---------------


[API文档](https://tranvideo.clash.ink/api-docs.html)
[米塔山的网站](https://clash.ink)
[米塔山的博客](https://b.clash.ink)
[米塔山的论坛](https://cnm.clash.ink)

公开API地址
```https://tranvideo.clash.ink/api```

公开的网站
```https://tranvideo.clash.ink```

### 获取公开API的邀请号码

给 ```kindmitaishere@gmail.com```或```rttommmr@outlook.com```发送电子邮件，或者提出“问题”

 **请注意，获取公开API的邀请号码不是必须的。因为你可以自行部署，可以通过源码运行，也可以通过```docker```的方式运行（***推荐***）***


 ***公开邀请码为`kindmita`，在公开的API地址中***



 [前往哔哩哔哩获取通过Docker方式部署的方法](https://www.bilibili.com/video/BV1H7gSznE46)


---------------


 
## ✨ 主要功能

- 🎵 **提取**       从视频文件中自动提取高音频
- 🎯 **识别**       使用`Whisper Large V3`模型对音频进行文字提取
- 🌍 **翻译**       调用`Ollama`的API，对提取到的原文进行逐句翻译
- 📝 **字幕**       生成 SRT 格式字幕文件
- 🎬 **视频合成**   在***提取***、***翻译***工作完成后根据分配的任务，可以直接下载SRT字幕，也可以选择下载字幕合并过的视频文件
- 📦 **批量处理**   支持多个视频一次性处理和批量下载
- ⚡ **GPU 优化**   ***4G***B+GPU内存即可运行，推荐***7GB***+GPU内存


## 👀实例
 - ### 条件
 - RTX 3070计算卡8GB显存规格
 - Ollama模型为 `qwen3:8b` ***开启推理***版本
 - Whisper 服务和 `qwen3:8b` 运行在同一张计算卡上，通过显存轮询管理共享8GB显存
   
 经过测试
 
 在***显存大小8G***的***RTX 3070***计算卡上，30分钟的视频只需要大约15分钟就可以处理完毕。

 ⚠️ 具体的翻译速度根据需要翻译的视频中有多少说话的内容决定，速度瓶颈在Ollama模型翻译上。

### 显存轮询机制
项目实现了智能显存轮询管理：
- **转录阶段**：Whisper模型加载到GPU，Ollama模型卸载
- **翻译阶段**：Whisper模型移动到CPU，Ollama模型加载到GPU
- **优化效果**：8GB显存即可流畅运行，无需16GB

![展示1](https://p.clash.ink/i/2025/10/18/nh3nhv.png)
![展示2](https://p.clash.ink/i/2025/07/29/qs44ay.jpg)
![展示3](https://p.clash.ink/i/2025/07/29/qs4fa5.jpg)
![展示4](https://p.clash.ink/i/2025/07/29/qtvs04.jpg)

如图的显存占用情况

![展示5](https://p.clash.ink/i/2025/07/29/qug63i.jpg)


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
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  ollama-setup:
    image: ollama/ollama:latest
    container_name: ollama-setup
    depends_on:
      ollama:
        condition: service_healthy
    network_mode: host
    entrypoint: /bin/sh
    command: >
      -c "
      echo 'Waiting for Ollama service to be ready...';
      sleep 5;
      echo 'Pulling qwen3:8b model...';
      ollama pull qwen3:8b;
      echo 'Model pulled successfully';
      "
    environment:
      - OLLAMA_HOST=http://localhost:11434
    restart: "no"

  tranvideo:
    image: kindmitaishere/tranvideo-v0.6
    container_name: tranvideo
    depends_on:
      ollama-setup:
        condition: service_completed_successfully
    network_mode: host
    volumes:
      - ./cache:/root/tranvideo/cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    environment:
      - OLLAMA_HOST=http://localhost:11434
    restart: always

volumes:
  ollama_data:
    driver: local
  tranvideo_data:
    driver: local
```

2. **启动服务**
```bash
# 创建必要目录
mkdir -p cache

# 启动容器
docker-compose up -d

# 查看启动日志
docker-compose logs -f tranvideo
```

### 方式二: Docker 命令

```bash
docker run -d \
  --name tranvideo \
  --gpus all \
  -p 5000:5000 \
  -v $(pwd)/cache:/root/tranvideo/cache \
  kindmitaishere/tranvideo-v0.6
```

### 方式三: 源码部署

> ⚠️ **重要提示**: 通过源码部署时，需要手动下载 Whisper 模型文件

#### 1. 克隆仓库

```bash
git clone https://github.com/MitaHill/tranvideo.git
cd tranvideo
```

#### 2. 下载 Whisper Large-V3-Turbo 模型

由于 GitHub 仓库大小限制，Whisper 模型文件（约 1.5GB）未包含在仓库中，需要手动下载。

**方式 A: 从 Hugging Face 下载（推荐）**

```bash
# 创建 whisper 目录
mkdir -p whisper

# 下载模型文件
wget https://huggingface.co/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt -O whisper/large-v3-turbo.pt
```

或使用 Python 脚本下载：

```python
from huggingface_hub import hf_hub_download

# 下载模型
hf_hub_download(
    repo_id="openai/whisper-large-v3-turbo",
    filename="large-v3-turbo.pt",
    local_dir="./whisper"
)
```

**方式 B: 手动下载**

1. 访问 [Hugging Face - Whisper Large V3 Turbo](https://huggingface.co/openai/whisper-large-v3-turbo)
2. 下载 `large-v3-turbo.pt` 文件
3. 将文件放置到项目的 `whisper/` 目录下

**方式 C: 从官方源下载**

```bash
# 使用 OpenAI 官方下载链接
wget https://openaipublic.azureedge.net/main/whisper/models/large-v3-turbo.pt -O whisper/large-v3-turbo.pt
```

#### 3. 验证模型文件

确保模型文件位置正确：

```bash
ls -lh whisper/large-v3-turbo.pt
# 应该显示文件大小约为 1.5GB
```

#### 4. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 5. 配置环境

编辑 `config/tran-py.json` 文件，配置 Ollama API 地址和模型：

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "https://api.siliconflow.cn/v1",
  "openai_api_key": "apikey",
  "openai_model": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"
}
```

#### 6. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:5000` 启动。

#### 目录结构说明

```
tranvideo/
├── whisper/
│   └── large-v3-turbo.pt    # 需要手动下载的模型文件
├── config/
│   └── tran-py.json          # 配置文件
├── src/                      # 源代码
├── main.py                   # 主程序入口
└── requirements.txt          # Python 依赖
```

## ⚙️ 初始配置

### 1. 配置 Ollama API

> ⚠️ **前提条件**: 需要先部署 Ollama 服务并安装 qwen3:8b 模型

访问以下 URL 配置 API 地址：
```
http://地址:端口/api/tranpy/config-ollama-api/你的ollama地址:端口
```

**示例**:
```
http://192.168.1.50:5000/api/tranpy/config-ollama-api/192.168.1.100:11434
```

### 2. 配置翻译模型

```
http://地址:端口/api/tranpy/config-ollama-model/qwen3:8b
```

### 3. 验证配置

访问配置查看接口：
```
http://地址:端口/api/tranpy/config
```

## 📖 使用指南

### 基础使用流程

1. **打开 Web 界面**
   ```
   http://地址:端口
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

[获取API调用接口的文档](https://tranvideo.clash.ink/api-docs.html)



## 🛠️ 系统要求

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB RAM（推荐 16GB）
- **显存**: 8GB VRAM 或更多（支持显存轮询优化）
- **存储**: 32GB 可用空间
- **GPU**: 支持 CUDA 的 NVIDIA 显卡

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Runtime
- CUDA 11.0+

### 显存管理特性
- **智能轮询**：自动在Whisper和Ollama模型间切换GPU显存
- **内存优化**：使用Whisper Large-V3-Turbo模型，减少内存占用
- **自动清理**：任务完成后自动释放显存资源
- **8GB兼容**：优化后的代码可以在8GB显存环境下稳定运行

### 日志管理

- 日志自动轮转，单文件最大 2MB
- 日志文件位置: `./logs/`
- 支持实时日志查看

### 性能优化

1. **GPU 显存优化**
   - 显存轮询管理：自动在Whisper和Ollama模型间切换，8GB显存即可运行
   - Whisper模型使用90%显存，turbo版本优化
   - 自动缓存清理和垃圾回收
   - 经测试，空载状态下显存占用为6.5-7GB

2. **并发处理**
   - 单任务队列，避免资源冲突
   - 显存轮询机制确保内存高效利用
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
curl http://地址:端口/api/whisper/health

# 查看容器日志
docker-compose logs tranvideo
```

**Q: 翻译功能异常**
```bash
# 验证 Ollama 连接
curl http://地址:端口/api/tags

# 检查配置
curl http://地址:端口/api/tranpy/config
```

### 性能调优

- 根据显卡性能调整批处理大小
- 监控显存使用情况
- 适当调整并发任务数量
- 显存轮询机制自动优化内存使用
- 8GB显存即可运行，无需16GB

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

![Development Status](https://img.shields.io/badge/Development-Active-brightgreen)
![Maintenance](https://img.shields.io/badge/Maintained-Yes-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![Good First Issues](https://img.shields.io/badge/good%20first%20issues-open-blue)
![Help Wanted](https://img.shields.io/badge/help%20wanted-yes-yellow)

## 📞 联系方式

- **邮箱**: kindmitaishere@gmail.com
- **备用邮箱**: rttommmr@outlook.com
- **网站**: [b.clash.ink](http://b.clash.ink)

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [Ollama](https://ollama.ai/) - 便捷的大模型部署工具
- [Qwen](https://github.com/QwenLM/Qwen) - 优秀的中文大语言模型



⭐ 如果这个项目对你有帮助，请给一个 Star！



`tranvideo 2.0` 将考虑进行发布。

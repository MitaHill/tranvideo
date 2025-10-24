# 安装指南

本文档详细介绍 Tranvideo 的各种安装方式，包括 Docker、源码部署和开发环境搭建。

## 系统要求

### 最低配置

| 组件 | 要求 |
|------|------|
| CPU | 4 核心 |
| 内存 | 8GB RAM |
| GPU | NVIDIA GPU with 8GB VRAM |
| 存储 | 32GB 可用空间 |
| 操作系统 | Linux / Windows / macOS |

### 推荐配置

| 组件 | 推荐 |
|------|------|
| CPU | 8 核心以上 |
| 内存 | 16GB RAM |
| GPU | NVIDIA RTX 4070 或更高 |
| 存储 | 64GB+ SSD |
| 操作系统 | Ubuntu 20.04+ / Debian 11+ |

### 软件依赖

#### 通用依赖

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Runtime
- CUDA 11.0+

#### 源码部署额外依赖

- Python 3.8+
- FFmpeg 4.0+
- Git

---

## 方式一：Docker Compose（推荐）

这是最简单且推荐的部署方式，包含 Ollama 服务和自动模型下载。

### 1. 安装 Docker 和 Docker Compose

#### Ubuntu/Debian

```bash
# 卸载旧版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### CentOS/RHEL

```bash
# 卸载旧版本
sudo yum remove docker docker-client docker-client-latest docker-common

# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### Windows

1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 安装并重启系统
3. 启用 WSL 2 后端

#### macOS

1. 下载 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 安装并启动 Docker Desktop

### 2. 安装 NVIDIA Container Runtime

```bash
# 添加 NVIDIA Container Runtime 仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 更新并安装
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 重启 Docker
sudo systemctl restart docker
```

### 3. 验证 GPU 支持

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 测试 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 4. 下载 docker-compose.yaml

```bash
# 创建项目目录
mkdir -p tranvideo && cd tranvideo

# 下载配置文件
wget https://raw.githubusercontent.com/MitaHill/tranvideo/main/docker-compose.yaml

# 或使用 curl
curl -o docker-compose.yaml https://raw.githubusercontent.com/MitaHill/tranvideo/main/docker-compose.yaml
```

### 5. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看启动日志
docker compose logs -f tranvideo
```

### 6. 等待模型下载

首次启动会自动下载 Ollama 模型（约 4.5GB），需要 3-10 分钟：

```bash
# 监控模型下载进度
docker compose logs -f ollama-setup
```

### 7. 验证部署

```bash
# 检查服务状态
docker compose ps

# 检查 Whisper 服务
curl http://localhost:5000/api/whisper/health

# 检查配置
curl http://localhost:5000/api/tranpy/config
```

### 8. 访问 Web 界面

打开浏览器访问: `http://localhost:5000`

---

## 方式二：Docker 单容器

适合已有 Ollama 服务或想要独立部署的场景。

### 1. 确保 NVIDIA Docker 支持

```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 2. 运行容器

```bash
docker run -d \
  --name tranvideo \
  --gpus all \
  --network host \
  --restart always \
  -p 5000:5000 \
  -v $(pwd)/cache:/root/tranvideo/cache \
  kindmitaishere/tranvideo:0.6.0
```

### 3. 单独部署 Ollama

```bash
# 启动 Ollama
docker run -d \
  --name ollama \
  --gpus all \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  ollama/ollama:latest

# 拉取模型
docker exec -it ollama ollama pull qwen3:8b
```

### 4. 配置 Ollama API

```bash
# 配置 API 地址
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434

# 配置模型
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

---

## 方式三：源码部署

适合开发者或需要自定义的场景。

### 1. 安装系统依赖

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
  python3.8 \
  python3-pip \
  python3-venv \
  ffmpeg \
  git \
  build-essential
```

#### CentOS/RHEL

```bash
sudo yum install -y \
  python38 \
  python38-pip \
  ffmpeg \
  git \
  gcc \
  gcc-c++
```

#### macOS

```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install python@3.9 ffmpeg git
```

#### Windows

1. 安装 [Python 3.8+](https://www.python.org/downloads/)
2. 安装 [FFmpeg](https://ffmpeg.org/download.html)
3. 安装 [Git](https://git-scm.com/download/win)

### 2. 克隆仓库

```bash
git clone https://github.com/MitaHill/tranvideo.git
cd tranvideo
```

### 3. 下载 Whisper 模型

#### 方式 A：使用 wget（推荐）

```bash
mkdir -p whisper
cd whisper

# 从 Hugging Face 下载
wget https://huggingface.co/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt \
  -O large-v3-turbo.pt

cd ..
```

#### 方式 B：使用 Python 脚本

```bash
mkdir -p whisper

python3 << 'EOF'
import urllib.request
import os

url = "https://openaipublic.azureedge.net/main/whisper/models/large-v3-turbo.pt"
output = "whisper/large-v3-turbo.pt"

print("开始下载 Whisper 模型...")
urllib.request.urlretrieve(url, output)
print(f"下载完成: {output}")
print(f"文件大小: {os.path.getsize(output) / 1024 / 1024:.2f} MB")
EOF
```

#### 方式 C：手动下载

1. 访问 [Hugging Face](https://huggingface.co/openai/whisper-large-v3-turbo)
2. 下载 `large-v3-turbo.pt` 文件
3. 放置到项目的 `whisper/` 目录下

### 4. 验证模型文件

```bash
ls -lh whisper/large-v3-turbo.pt
# 应显示约 1.5GB 的文件
```

### 5. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 6. 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 7. 配置环境

创建或编辑 `config/tran-py.json`：

```json
{
  "translator_type": "ollama",
  "ollama_api": "http://127.0.0.1:11434",
  "ollama_model": "qwen3:8b",
  "openai_base_url": "https://api.openai.com/v1",
  "openai_api_key": "your-api-key-here",
  "openai_model": "gpt-3.5-turbo"
}
```

### 8. 安装和配置 Ollama

#### 安装 Ollama

```bash
# Linux
curl https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Windows
# 下载并安装: https://ollama.ai/download/windows
```

#### 拉取模型

```bash
ollama pull qwen3:8b
```

#### 启动 Ollama 服务

```bash
# Linux/macOS (后台运行)
ollama serve &

# Windows
# Ollama 会作为服务自动启动
```

### 9. 启动 Tranvideo

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 启动服务
python main.py
```

### 10. 验证安装

```bash
# 检查服务
curl http://localhost:5000/api/whisper/health

# 访问 Web 界面
# 打开浏览器: http://localhost:5000
```

---

## 环境变量配置

### Docker 环境变量

可以通过环境变量覆盖默认配置：

```yaml
# docker-compose.yaml
services:
  tranvideo:
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - TRANSLATOR_TYPE=ollama
      - OLLAMA_MODEL=qwen3:8b
      - LOG_LEVEL=INFO
```

### 源码部署环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
OLLAMA_HOST=http://127.0.0.1:11434
TRANSLATOR_TYPE=ollama
OLLAMA_MODEL=qwen3:8b
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
LOG_LEVEL=INFO
EOF

# 加载环境变量
source .env  # Linux/macOS
# 或在 Windows 手动设置
```

---

## 目录结构

### Docker 部署

```
tranvideo/
├── docker-compose.yaml    # Docker Compose 配置
└── cache/                 # 持久化数据目录
    ├── uploads/           # 上传文件
    ├── temp/              # 临时文件
    └── outputs/           # 输出文件
```

### 源码部署

```
tranvideo/
├── main.py                # 主程序入口
├── requirements.txt       # Python 依赖
├── config/                # 配置目录
│   ├── tran-py.json       # 主配置文件
│   └── prompt.txt         # 翻译提示词
├── whisper/               # Whisper 模型目录
│   └── large-v3-turbo.pt  # 模型文件（需下载）
├── src/                   # 源代码
│   ├── api/               # API 层
│   ├── core/              # 核心业务逻辑
│   ├── services/          # 外部服务
│   └── utils/             # 工具函数
├── webui/                 # Web 界面
├── cache/                 # 缓存目录
├── db/                    # 数据库
│   └── tasks.json         # 任务数据
└── logs/                  # 日志目录
```

---

## 升级指南

### Docker Compose 升级

```bash
# 进入项目目录
cd tranvideo

# 拉取最新镜像
docker compose pull

# 停止旧容器
docker compose down

# 启动新容器
docker compose up -d

# 查看日志
docker compose logs -f tranvideo
```

### Docker 单容器升级

```bash
# 停止并删除旧容器
docker stop tranvideo
docker rm tranvideo

# 拉取最新镜像
docker pull kindmitaishere/tranvideo:latest

# 启动新容器
docker run -d \
  --name tranvideo \
  --gpus all \
  --network host \
  --restart always \
  -p 5000:5000 \
  -v $(pwd)/cache:/root/tranvideo/cache \
  kindmitaishere/tranvideo:latest
```

### 源码部署升级

```bash
# 进入项目目录
cd tranvideo

# 备份配置
cp config/tran-py.json config/tran-py.json.bak

# 拉取最新代码
git fetch origin
git pull origin main

# 更新依赖
source venv/bin/activate
pip install --upgrade -r requirements.txt

# 恢复配置
cp config/tran-py.json.bak config/tran-py.json

# 重启服务
# 按 Ctrl+C 停止旧进程
python main.py
```

---

## 卸载指南

### Docker Compose 卸载

```bash
cd tranvideo

# 停止并删除容器
docker compose down

# 删除数据卷（可选）
docker compose down -v

# 删除镜像（可选）
docker rmi kindmitaishere/tranvideo:0.6.0
docker rmi ollama/ollama:latest

# 删除项目目录
cd ..
rm -rf tranvideo
```

### 源码部署卸载

```bash
cd tranvideo

# 停止服务（Ctrl+C）

# 删除虚拟环境
rm -rf venv

# 删除缓存
rm -rf cache

# 删除项目（可选）
cd ..
rm -rf tranvideo
```

---

## 故障排除

### GPU 不可用

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# 重新安装 NVIDIA Container Runtime
sudo apt-get install --reinstall nvidia-container-toolkit
sudo systemctl restart docker
```

### 模型下载失败

```bash
# Whisper 模型替代下载地址
wget https://openaipublic.azureedge.net/main/whisper/models/large-v3-turbo.pt

# Ollama 模型手动拉取
docker exec -it ollama ollama pull qwen3:8b

# 国内镜像加速
export HF_ENDPOINT=https://hf-mirror.com
```

### 端口冲突

```bash
# 检查端口占用
sudo lsof -i :5000
sudo lsof -i :11434

# 修改端口（docker-compose.yaml）
ports:
  - "5001:5000"  # 改为 5001
```

### 磁盘空间不足

```bash
# 清理 Docker
docker system prune -a

# 清理缓存
rm -rf tranvideo/cache/*

# 清理日志
rm -rf tranvideo/logs/*
```

---

## 性能优化建议

### 1. 使用 SSD

将缓存目录挂载到 SSD：

```yaml
volumes:
  - /path/to/ssd/cache:/root/tranvideo/cache
```

### 2. 增加共享内存

```yaml
services:
  tranvideo:
    shm_size: 8gb
```

### 3. 优化 Docker 资源限制

```yaml
services:
  tranvideo:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
```

---

## 下一步

- 📖 [快速开始](Quick-Start.md) - 快速上手指南
- ⚙️ [配置指南](Configuration.md) - 详细配置说明
- 🔧 [API 文档](API-Reference.md) - API 接口文档
- 💡 [故障排除](Troubleshooting.md) - 常见问题解决

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

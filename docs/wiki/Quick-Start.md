# 快速开始

本指南将帮助您在 **5分钟内** 快速部署和使用 Tranvideo。

## 前置要求

- 支持 CUDA 的 NVIDIA 显卡 (8GB+ 显存)
- Docker 和 Docker Compose
- NVIDIA Container Runtime

## 部署步骤

### 1. 创建项目目录

```bash
mkdir -p tranvideo && cd tranvideo
```

### 2. 下载配置文件

```bash
wget https://raw.githubusercontent.com/MitaHill/tranvideo/main/docker-compose.yaml
```

或者手动创建 `docker-compose.yaml`:

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

  ollama-setup:
    image: ollama/ollama:latest
    container_name: ollama-setup
    depends_on:
      - ollama
    network_mode: host
    entrypoint: /bin/sh
    command: >
      -c "
      echo 'Pulling qwen3:8b model...';
      sleep 10;
      ollama pull qwen3:8b;
      echo 'Model pulled successfully';
      "
    restart: "no"

  tranvideo:
    image: kindmitaishere/tranvideo:0.6.0
    container_name: tranvideo
    depends_on:
      - ollama-setup
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
    restart: always

volumes:
  ollama_data:
```

### 3. 启动服务

```bash
# 启动所有服务
docker compose up -d

# 查看启动日志
docker compose logs -f tranvideo
```

### 4. 等待服务就绪

首次启动需要下载模型,大约需要 **3-5分钟**:

```bash
# 监控 Ollama 模型下载进度
docker compose logs -f ollama-setup

# 查看 Tranvideo 启动状态
docker compose logs -f tranvideo
```

看到类似以下日志表示服务已就绪:

```
[INFO] Whisper 服务已就绪
[INFO] 启动 Flask 服务器...
 * Running on http://0.0.0.0:5000
```

### 5. 访问 Web 界面

打开浏览器访问: `http://localhost:5000`

或使用服务器IP: `http://your-server-ip:5000`

## 首次使用

### 1. 输入邀请码

默认邀请码: `kindmita`

### 2. 上传视频

- 点击上传按钮
- 选择视频文件 (支持 MP4, AVI, MOV 等)
- 系统会自动检测视频时长

### 3. 选择处理模式

- **仅字幕**: 生成 SRT 字幕文件
- **视频+字幕**: 生成带字幕的视频

### 4. 开始处理

点击"开始翻译"按钮,系统将:

1. 提取音频
2. 识别语音 (Whisper)
3. 翻译文本 (Ollama)
4. 生成字幕
5. (可选) 嵌入视频

### 5. 下载结果

处理完成后,点击下载按钮获取:
- SRT 字幕文件
- 带字幕的视频文件 (如果选择)

## 性能参考

在 RTX 4070 Ti (8GB) 环境下:

- **30分钟视频** → 约 15分钟处理时间
- **显存占用** → 6.5-7GB
- **处理速度** → 约 2:1 (视频时长:处理时间)

> 实际处理时间取决于视频中的语音密度

## 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f tranvideo

# 重启服务
docker compose restart tranvideo

# 停止服务
docker compose down

# 更新到最新版本
docker compose pull
docker compose up -d
```

## 常见问题

### GPU 不可用

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 服务启动失败

```bash
# 查看详细日志
docker compose logs tranvideo

# 重新启动
docker compose down
docker compose up -d
```

### 模型下载缓慢

```bash
# 手动拉取 Ollama 模型
docker exec -it ollama ollama pull qwen3:8b
```

## 下一步

- 📖 阅读 [基础使用](Basic-Usage.md) 了解更多功能
- ⚙️ 查看 [配置指南](Configuration.md) 优化设置
- 🔧 学习 [API文档](API-Overview.md) 进行集成
- 💡 浏览 [故障排除](Troubleshooting.md) 解决问题

## 需要帮助?

- GitHub Issues: [提交问题](https://github.com/MitaHill/tranvideo/issues)
- 邮件支持: kindmitaishere@gmail.com
- 社区论坛: [cnm.clash.ink](https://cnm.clash.ink)

---

[返回 Wiki 首页](Home.md)

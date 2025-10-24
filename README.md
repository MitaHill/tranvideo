# Tranvideo - 自部署视频翻译平台

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![GPU-Memory](https://img.shields.io/badge/GPU-8GB%2B%20Optimized-orange.svg)
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

Tranvideo 是一个基于 **Whisper Large V3** 和 **Ollama** 的开源视频翻译平台，支持自动语音识别、多语言翻译和字幕生成。

## 🎯 核心特性

- **🎯 智能显存管理** - 先进的显存轮询技术，8GB GPU 即可流畅运行
- **🌍 多语言支持** - 支持多种语言的语音识别和翻译
- **⚡ 高效处理** - 优化的流水线设计，快速处理视频文件
- **🔧 灵活部署** - 支持 Docker 和源码部署，适配多种环境

---------------


### 🔗 相关链接

- [📖 API 文档](http://39.104.48.129:5000/api-docs.html)
- [🌐 官方网站](https://tranvideo.clash.ink)
- [💻 米塔山的网站](https://clash.ink)
- [📝 技术博客](https://b.clash.ink)
- [💬 社区论坛](https://cnm.clash.ink)

### 获取公开API的邀请号码

给 ```kindmitaishere@gmail.com```或```rttommmr@outlook.com```发送电子邮件，或者提出“问题”

 **请注意，获取公开API的邀请号码不是必须的。因为你可以自行部署，可以通过源码运行，也可以通过```docker```的方式运行（***推荐***）***


 - **公开邀请码**: `kindmita` (在公开 API 中使用)



 [📺 哔哩哔哩 Docker 部署教程](https://www.bilibili.com/video/BV1H7gSznE46)


---------------


 
## ✨ 核心功能

- 🎵 **音频提取** - 从视频文件中自动提取高质量音频
- 🎯 **语音识别** - 使用 **Whisper Large V3** 模型进行精准文字识别
- 🌍 **智能翻译** - 调用 **Ollama** API 实现逐句翻译
- 📝 **字幕生成** - 生成标准 SRT 格式字幕文件
- 🎬 **视频合成** - 将字幕嵌入视频，支持多种输出格式
- 📦 **批量处理** - 支持多文件并行处理和批量下载
- 🚀 **显存优化** - **8GB GPU 显存**即可流畅运行，支持显存轮询管理


## 🧪 性能实例

### 测试环境
- **GPU**: NVIDIA RTX 4070 Ti (8GB 显存)
- **Ollama 模型**: `qwen3:8b` (推理模式)
- **Whisper 模型**: `large-v3-turbo`
- **显存管理**: 智能轮询机制

### 处理性能
在 **8GB 显存** 环境下，30分钟的视频处理耗时约 **15分钟**

> ⚠️ **注意**: 实际处理时间受视频中语音内容密度影响，翻译阶段是主要性能瓶颈

### 🎯 显存轮询机制详解

项目采用先进的显存轮询技术，实现高效的内存管理：

- **🎯 转录阶段** - Whisper 模型加载到 GPU，Ollama 模型被卸载
- **🌍 翻译阶段** - Whisper 模型移动到 CPU，Ollama 模型加载到 GPU  
- **⚡ 优化效果** - 8GB 显存即可流畅运行，无需 16GB 显存
- **🔧 智能调度** - 自动在模型间切换，最大化 GPU 利用率

![展示1](https://p.clash.ink/i/2025/10/18/nh3nhv.png)

如图的显存占用情况

![展示2](https://p.clash.ink/i/2025/10/18/njcyo8.png)


## 🎨 Web 界面预览

- 简洁直观的 Web 界面
- 邀请码验证系统
- 文件时长预检查
- 队列管理和状态监控

## 🚀 快速开始

### 方式一: Docker Compose（推荐）

#### 1. 下载配置文件
```bash
# 创建项目目录
mkdir -p tranvideo && cd tranvideo

# 下载 docker-compose.yaml
wget https://raw.githubusercontent.com/MitaHill/tranvideo/main/docker-compose.yaml
```

#### 2. 启动服务
```bash
# 启动所有服务
sudo docker compose up -d

# 查看启动状态
sudo docker compose logs -f tranvideo
```

#### 3. 访问服务
服务启动后，访问 `http://localhost:5000` 即可使用

### 方式二: Docker 命令（需要手动配置 Ollama）

```bash
docker run -d \
  --name tranvideo \
  --gpus all \
  --network host \
  --restart always \
  -p 5000:5000 \
  -v $(pwd)/cache:/root/tranvideo/cache \
  kindmitaishere/tranvideo-v0.6
```

> ⚠️ **注意**: 此方式需要单独部署 **Ollama** 服务并提前拉取模型文件

### 方式三: 源码部署

> ⚠️ **重要提示**: 通过源码部署时，需要手动下载 Whisper 模型文件

#### 1. 克隆仓库
```bash
git clone https://github.com/MitaHill/tranvideo.git
cd tranvideo
```

#### 2. 下载 Whisper Large-V3-Turbo 模型

**方式 A: 从 Hugging Face 下载（推荐）**
```bash
# 在项目根目录执行
mkdir -p whisper
cd whisper

# 下载模型文件
wget https://huggingface.co/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt -O large-v3-turbo.pt
```

**方式 B: 手动下载**
1. 访问 [Hugging Face - Whisper Large V3 Turbo](https://huggingface.co/openai/whisper-large-v3-turbo)
2. 下载 `large-v3-turbo.pt` 文件
3. 将文件放置到项目的 `whisper/` 目录下

**方式 C: 从官方源下载**
```bash
# 在项目根目录执行
mkdir -p whisper
cd whisper

# 使用 OpenAI 官方下载链接
wget https://openaipublic.azureedge.net/main/whisper/models/large-v3-turbo.pt -O large-v3-turbo.pt
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

编辑 `config/tran-py.json` 文件，配置翻译服务和模型：


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

### 🔧 配置说明

#### 翻译器类型选择
- **`"translator_type": "ollama"`** - 使用本地 Ollama 服务
- **`"translator_type": "openai"`** - 使用 OpenAI 兼容的云服务

#### 显存轮询触发条件
> ⚠️ **重要**: 显存轮询仅在以下条件触发：
> - `translator_type` 设置为 `"ollama"`
> - `ollama_api` 使用 **`http://127.0.0.1:11434`** (localhost 不会触发)
> - 本地部署的 Ollama 服务

#### 示例配置
- **本地 Ollama**: 启用显存轮询，8GB 显存即可运行
- **远程 Ollama**: 禁用显存轮询，需要更多显存
- **OpenAI API**: 禁用显存轮询，仅需 Whisper 模型显存

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
- **CPU**: 4核心及以上
- **内存**: 8GB RAM（推荐 16GB）
- **显存**: **8GB VRAM** 或更多（支持显存轮询优化）
- **存储**: 32GB 可用空间
- **GPU**: 支持 CUDA 的 NVIDIA 显卡

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Runtime
- CUDA 11.0+

### 🎯 显存管理特性
- **智能轮询** - 自动在 Whisper 和 Ollama 模型间切换 GPU 显存
- **内存优化** - 使用 Whisper Large-V3-Turbo 模型，减少内存占用
- **自动清理** - 任务完成后自动释放显存资源
- **8GB 兼容** - 优化后的代码可在 8GB 显存环境下稳定运行

### 日志管理

- 日志自动轮转，单文件最大 2MB
- 日志文件位置: `./logs/`
- 支持实时日志查看

### ⚡ 性能优化

#### 1. GPU 显存优化
- **显存轮询管理** - 自动在 Whisper 和 Ollama 模型间切换，8GB 显存即可运行
- **内存限制优化** - Whisper 模型使用 90% 显存，turbo 版本进一步优化
- **自动缓存清理** - 任务完成后自动执行垃圾回收
- **实测性能** - 空载状态下显存占用为 6.5-7GB

#### 2. 并发处理优化
- **单任务队列** - 避免资源冲突，确保任务处理的稳定性
- **显存轮询机制** - 最大化 GPU 内存利用效率
- **模型预热** - 减少模型加载时间，提升处理速度

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

### 🎯 性能调优建议

- **显卡性能** - 根据显卡性能调整批处理大小
- **显存监控** - 实时监控 GPU 显存使用情况
- **并发控制** - 适当调整并发任务数量
- **轮询优化** - 显存轮询机制自动优化内存使用
- **硬件要求** - **8GB 显存**即可运行，无需 16GB

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



## 📋 版本信息

- **当前版本**: v0.6.0
- **发布日期**: 2025年10月
- **Docker镜像**: `kindmitaishere/tranvideo:0.6.0`
- **下一版本**: v1.0.0 (正式版，计划中)

### 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本变更记录。

## 📦 发行说明

### 当前版本 (v0.6.0)

**主要特性**:
- 🎯 智能显存轮询管理 - 8GB显存即可运行
- 🌍 多语言支持 - Whisper + Ollama/OpenAI
- 📦 批量处理 - 支持多文件并行处理
- 🎬 视频合成 - 自动嵌入字幕
- 💾 任务管理 - SQLite数据库持久化

**Docker 镜像标签**:
```bash
# 推荐使用精确版本号
docker pull kindmitaishere/tranvideo:0.6.0

# 或使用 latest 标签 (当前指向 0.6.0)
docker pull kindmitaishere/tranvideo:latest
```

### 版本路线图

| 版本 | 状态 | 计划时间 | 主要内容 |
|------|------|---------|---------|
| v0.6.0 | ✅ 已发布 | 2025-10 | 显存优化、批量处理 |
| v0.7.0 | 📋 规划中 | 2025-Q2 | 性能优化、新功能 |
| v0.8.0 | 📋 规划中 | 2025-Q3 | UI增强、API扩展 |
| v1.0.0 | 🎯 目标版本 | 2025-Q4 | 正式版发布、生产就绪 |

查看 [VERSION_POLICY.md](VERSION_POLICY.md) 了解版本管理策略。

### 发布流程

项目采用规范的版本管理和发布流程:

- **版本号**: 遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)
- **发布流程**: 详见 [RELEASE_GUIDE.md](RELEASE_GUIDE.md)
- **Git 分支**: main(稳定版) / develop(开发版)
- **Docker 镜像**: 每个版本都会发布对应的镜像标签

## 📚 文档资源

### 官方文档
- 📖 [项目 Wiki](docs/wiki/Home.md) - 完整的使用文档
- 🚀 [快速开始](docs/wiki/Quick-Start.md) - 5分钟快速部署
- 🔧 [显存管理](docs/wiki/VRAM-Management.md) - 显存优化详解
- 📡 [API 文档](docs/wiki/API-Overview.md) - RESTful API 接口

### 项目管理
- 📝 [更新日志](CHANGELOG.md) - 版本变更记录
- 📋 [版本策略](VERSION_POLICY.md) - 版本管理规范
- 🚢 [发布指南](RELEASE_GUIDE.md) - 发布流程说明
- 🤝 [贡献指南](CONTRIBUTING.md) - 参与贡献指南

### 在线资源
- 🌐 [官方网站](https://tranvideo.clash.ink) - 项目主页
- 📖 [在线API文档](https://tranvideo.clash.ink/api-docs.html) - 详细的API文档
- 📝 [技术博客](https://b.clash.ink) - 技术文章和教程
- 💬 [社区论坛](https://cnm.clash.ink) - 讨论和反馈

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star！

[![Star History Chart](https://api.star-history.com/svg?repos=MitaHill/tranvideo&type=Date)](https://star-history.com/#MitaHill/tranvideo&Date)

# 故障排除指南

本文档汇总了 Tranvideo 使用过程中的常见问题及解决方案。

## 目录

- [安装部署问题](#安装部署问题)
- [服务运行问题](#服务运行问题)
- [视频处理问题](#视频处理问题)
- [性能问题](#性能问题)
- [网络问题](#网络问题)
- [配置问题](#配置问题)

---

## 安装部署问题

### GPU 不可用

**症状**:
```
RuntimeError: CUDA out of memory
CUDA error: no kernel image is available for execution on the device
```

**诊断**:

```bash
# 检查 NVIDIA 驱动
nvidia-smi

# 检查 CUDA 版本
nvcc --version

# 检查 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**解决方案**:

1. **安装 NVIDIA 驱动**:

```bash
# Ubuntu
sudo apt-get update
sudo apt-get install nvidia-driver-535

# 重启系统
sudo reboot
```

2. **安装 NVIDIA Container Runtime**:

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

3. **验证安装**:

```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Docker Compose 启动失败

**症状**:
```
ERROR: for tranvideo  Cannot start service tranvideo: OCI runtime create failed
```

**解决方案**:

1. **检查端口占用**:

```bash
sudo lsof -i :5000
sudo lsof -i :11434

# 终止占用进程
sudo kill -9 <PID>
```

2. **检查磁盘空间**:

```bash
df -h
docker system prune -a
```

3. **重新构建**:

```bash
docker compose down -v
docker compose pull
docker compose up -d
```

### Whisper 模型下载失败

**症状**:
```
FileNotFoundError: whisper/large-v3-turbo.pt
```

**解决方案**:

```bash
mkdir -p whisper
cd whisper

# 方案一：从 Hugging Face
wget https://huggingface.co/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt

# 方案二：从 Azure
wget https://openaipublic.azureedge.net/main/whisper/models/large-v3-turbo.pt

# 方案三：使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
wget https://hf-mirror.com/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt
```

### Ollama 模型下载慢

**解决方案**:

1. **使用代理**:

```bash
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
ollama pull qwen3:8b
```

2. **手动下载并导入**:

```bash
# 从其他机器复制模型
scp -r ~/.ollama/models user@target:~/.ollama/
```

---

## 服务运行问题

### Whisper 服务未启动

**症状**:
```json
{
  "error": "Whisper service not available"
}
```

**诊断**:

```bash
curl http://localhost:5000/api/whisper/health
docker compose logs tranvideo
```

**解决方案**:

1. **检查服务日志**:

```bash
docker compose logs -f tranvideo | grep -i whisper
```

2. **重启服务**:

```bash
docker compose restart tranvideo
```

3. **检查 GPU 显存**:

```bash
nvidia-smi
# 确保有足够的显存（至少 4GB）
```

### Ollama 服务连接失败

**症状**:
```json
{
  "error": "Failed to connect to Ollama service"
}
```

**诊断**:

```bash
# 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 检查配置
curl http://localhost:5000/api/tranpy/config
```

**解决方案**:

1. **启动 Ollama 服务**:

```bash
# Docker
docker compose restart ollama

# 源码部署
ollama serve
```

2. **检查网络**:

```bash
# 测试连接
telnet localhost 11434
curl http://localhost:11434/api/version
```

3. **更新配置**:

```bash
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434
```

### Flask 服务无法访问

**症状**:
```
curl: (7) Failed to connect to localhost port 5000
```

**解决方案**:

1. **检查服务状态**:

```bash
docker compose ps
docker compose logs tranvideo
```

2. **检查防火墙**:

```bash
# Ubuntu
sudo ufw allow 5000
sudo ufw reload

# CentOS
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

3. **检查监听地址**:

```bash
# 应该监听 0.0.0.0:5000，而不是 127.0.0.1:5000
netstat -tlnp | grep 5000
```

---

## 视频处理问题

### 上传失败

**症状**:
```json
{
  "error": "File upload failed"
}
```

**可能原因**:

1. **文件过大（>2GB）**

```bash
# 压缩视频
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
```

2. **文件格式不支持**

```bash
# 转换格式
ffmpeg -i input.avi -c copy output.mp4
```

3. **网络超时**

```bash
# 增加上传超时时间
curl -X POST -F "file=@large.mp4" --max-time 600 http://localhost:5000/api/...
```

### 语音识别不准确

**问题**: 字幕内容不准确或包含大量错误

**解决方案**:

1. **提高音频质量**:

```bash
# 降噪处理
ffmpeg -i input.mp4 -af "highpass=f=200, lowpass=f=3000" output.mp4
```

2. **调整音量**:

```bash
# 归一化音量
ffmpeg -i input.mp4 -af "loudnorm" output.mp4
```

3. **使用更大的 Whisper 模型** (如果显存充足):

```python
# 修改为 large-v3 模型（需要更多显存）
whisper_model = "large-v3"
```

### 翻译质量差

**问题**: 翻译不自然或有错误

**解决方案**:

1. **更换翻译模型**:

```bash
# 使用更大的模型
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:14b

# 或使用 OpenAI
curl http://localhost:5000/api/tranpy/config-translator-type/openai
```

2. **优化提示词**:

编辑 `config/prompt.txt`:

```
你是专业翻译专家。将外语翻译成自然流畅的中文，
注意语境和文化差异，确保译文通顺易懂。
只输出代码块格式：``````
```

3. **手动修正**:

下载 SRT 文件后手动编辑修正。

### 视频合成失败

**症状**:
```
FFmpeg error: Cannot find a suitable output format
```

**解决方案**:

1. **检查 FFmpeg 安装**:

```bash
ffmpeg -version

# 重新安装
# Ubuntu
sudo apt-get install --reinstall ffmpeg

# Docker
docker compose restart tranvideo
```

2. **检查磁盘空间**:

```bash
df -h
# 确保有足够空间存储输出文件
```

### 任务卡住不动

**症状**: 进度条长时间不更新

**诊断**:

```bash
# 查看任务状态
curl http://localhost:5000/api/task/{task_id}

# 查看服务日志
docker compose logs -f tranvideo
```

**解决方案**:

1. **检查是否在队列中**:

```bash
curl http://localhost:5000/api/status
```

2. **检查 GPU 状态**:

```bash
nvidia-smi
# 查看 GPU 是否在工作
```

3. **重启服务**（最后手段）:

```bash
docker compose restart tranvideo
```

---

## 性能问题

### 处理速度太慢

**症状**: 处理时间远超预期

**诊断**:

```bash
# 监控 GPU 使用率
watch -n 1 nvidia-smi

# 监控 CPU 使用率
top
```

**优化方案**:

1. **检查 GPU 是否被使用**:

```bash
# 应该看到 GPU 利用率 > 50%
nvidia-smi
```

2. **优化翻译模型**:

```bash
# 使用更小/更快的模型
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

3. **检查显存轮询配置**:

```bash
# 确保使用 127.0.0.1 而不是 localhost
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434
```

4. **增加系统资源**:

```yaml
# docker-compose.yaml
deploy:
  resources:
    limits:
      memory: 16G  # 增加内存限制
```

### 显存不足

**症状**:
```
CUDA out of memory. Tried to allocate X.XX GiB
```

**解决方案**:

1. **启用显存轮询**:

```bash
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434
```

2. **使用更小的模型**:

```bash
# Whisper: 使用 turbo 版本（已默认）
# Ollama: 使用 8B 模型
curl http://localhost:5000/api/tranpy/config-ollama-model/qwen3:8b
```

3. **释放其他 GPU 进程**:

```bash
# 查看 GPU 进程
nvidia-smi

# 终止其他进程
kill -9 <PID>
```

4. **降低批处理大小**:

```python
# 修改批处理参数
BATCH_SIZE = 8  # 降低批处理大小
```

### 内存泄漏

**症状**: 系统内存持续增长

**解决方案**:

1. **定期重启服务**:

```bash
# 使用 cron 定期重启
0 3 * * * docker compose restart tranvideo
```

2. **清理缓存**:

```bash
# 清理任务缓存
curl -X POST http://localhost:5000/api/administrator/delete_all_cache

# 手动清理
rm -rf cache/temp/*
```

3. **增加垃圾回收**:

```python
# 在代码中增加 GC
import gc
gc.collect()
torch.cuda.empty_cache()
```

---

## 网络问题

### 无法访问 Web 界面

**解决方案**:

1. **检查端口映射**:

```bash
docker compose ps
# 确保端口映射为 0.0.0.0:5000->5000/tcp
```

2. **检查防火墙**:

```bash
sudo ufw status
sudo ufw allow 5000
```

3. **检查绑定地址**:

```python
# main.py
app.run(host='0.0.0.0', port=5000)
```

### API 请求超时

**症状**:
```
Request timeout after 120 seconds
```

**解决方案**:

1. **增加超时时间**:

```python
import requests
response = requests.post(url, files=files, timeout=600)
```

2. **使用流式处理**:

```python
response = requests.post(url, files=files, stream=True)
```

3. **检查网络质量**:

```bash
ping localhost
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/whisper/health
```

### 下载文件失败

**症状**: 下载中断或文件损坏

**解决方案**:

1. **使用断点续传**:

```bash
curl -C - -O http://localhost:5000/api/download/video/xxx.mp4
```

2. **检查文件是否过期**:

```bash
# 文件保留 24 小时后自动删除
curl http://localhost:5000/api/task/{task_id}
```

3. **重新生成下载链接**:

刷新页面或重新查询任务状态。

---

## 配置问题

### JSON 配置格式错误

**症状**:
```
JSONDecodeError: Expecting property name enclosed in double quotes
```

**解决方案**:

1. **验证 JSON 格式**:

```bash
# 使用 jq 验证
cat config/tran-py.json | jq .

# 在线验证
# https://jsonlint.com/
```

2. **常见错误**:

```json
// 错误：使用了单引号
{
  'translator_type': 'ollama'
}

// 正确：使用双引号
{
  "translator_type": "ollama"
}

// 错误：多余的逗号
{
  "translator_type": "ollama",
}

// 正确
{
  "translator_type": "ollama"
}
```

### 配置不生效

**症状**: 修改配置后没有变化

**解决方案**:

1. **重启服务**:

```bash
docker compose restart tranvideo
```

2. **检查配置加载**:

```bash
docker compose logs tranvideo | grep -i config
```

3. **使用 API 动态配置**:

```bash
curl http://localhost:5000/api/tranpy/config-ollama-api/127.0.0.1:11434
```

### 环境变量不生效

**解决方案**:

1. **检查环境变量语法**:

```yaml
# docker-compose.yaml
environment:
  - OLLAMA_HOST=http://127.0.0.1:11434  # 正确
  # OLLAMA_HOST: http://127.0.0.1:11434  # 也正确
```

2. **检查加载顺序**:

```bash
docker compose config  # 查看最终配置
```

---

## 日志分析

### 查看实时日志

```bash
# 所有服务
docker compose logs -f

# 特定服务
docker compose logs -f tranvideo
docker compose logs -f ollama

# 过滤关键词
docker compose logs -f tranvideo | grep -i error
docker compose logs -f tranvideo | grep -i warning
```

### 保存日志

```bash
# 导出日志
docker compose logs > tranvideo_logs_$(date +%Y%m%d).log

# 查看最近的错误
docker compose logs --tail=100 tranvideo | grep ERROR
```

### 常见日志错误

#### 1. CUDA 错误

```
RuntimeError: CUDA error: out of memory
```

**解决**: 启用显存轮询或使用更小的模型

#### 2. 连接错误

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**解决**: 检查 Ollama 服务是否运行

#### 3. 文件权限错误

```
PermissionError: [Errno 13] Permission denied
```

**解决**:

```bash
sudo chown -R $USER:$USER cache/
chmod -R 755 cache/
```

---

## 调试模式

### 启用调试日志

```python
# main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

或环境变量:

```bash
export LOG_LEVEL=DEBUG
docker compose up -d
```

### Python 调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()
```

### Docker 调试

```bash
# 进入容器
docker compose exec tranvideo bash

# 检查进程
ps aux

# 检查网络
netstat -tlnp

# 检查文件系统
ls -la cache/
```

---

## 获取帮助

### 检查问题清单

1. ✅ 查看本文档相关章节
2. ✅ 搜索 [GitHub Issues](https://github.com/MitaHill/tranvideo/issues)
3. ✅ 查看服务日志
4. ✅ 检查系统资源（GPU、内存、磁盘）

### 提交 Issue

如果问题未解决，请提交 Issue 并包含：

1. **环境信息**:

```bash
# 系统信息
uname -a
docker --version
nvidia-smi

# 配置信息
curl http://localhost:5000/api/tranpy/config

# 日志
docker compose logs --tail=100 tranvideo
```

2. **重现步骤**:
   - 详细描述操作步骤
   - 提供视频文件信息（格式、大小、时长）
   - 提供错误截图

3. **预期行为** vs **实际行为**

### 联系方式

- **GitHub Issues**: [提交问题](https://github.com/MitaHill/tranvideo/issues)
- **邮件**: kindmitaishere@gmail.com
- **社区**: [cnm.clash.ink](https://cnm.clash.ink)

---

## 常见问题 FAQ

### Q: 支持哪些语言？

A: Whisper 支持 99+ 种语言的识别，默认翻译为中文，可通过修改提示词更改目标语言。

### Q: 可以离线使用吗？

A: 可以。使用 Ollama 翻译器可完全离线使用（需要预先下载模型）。

### Q: 处理时间如何估算？

A: 大约为视频时长的 0.5-1 倍。30 分钟视频约需 15-30 分钟处理。

### Q: 支持实时翻译吗？

A: 目前不支持，只支持上传后离线处理。

### Q: 可以同时处理多个视频吗？

A: 支持批量上传，但是按顺序处理（一次只处理一个任务）。

### Q: 文件会保留多久？

A: 处理完成后保留 24 小时，请及时下载。

### Q: 可以自定义字幕样式吗？

A: SRT 文件本身不包含样式信息，样式由播放器控制。如需自定义样式，可转换为 ASS 格式。

### Q: 支持商业使用吗？

A: 项目采用 MIT 许可证，可商业使用。但请注意 Whisper 和 Ollama 的许可证要求。

---

## 预防性维护

### 定期清理

```bash
# 每周清理缓存
0 3 * * 0 rm -rf /path/to/tranvideo/cache/temp/*

# 每月清理 Docker
0 3 1 * * docker system prune -a -f
```

### 监控脚本

```bash
#!/bin/bash
# monitor.sh - 健康检查脚本

# 检查服务
if ! curl -s http://localhost:5000/api/whisper/health > /dev/null; then
    echo "Tranvideo service is down!"
    docker compose restart tranvideo
fi

# 检查磁盘空间
DISK_USAGE=$(df -h /path/to/tranvideo | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is $DISK_USAGE%"
    # 清理缓存
    find cache/ -mtime +1 -delete
fi

# 检查内存
MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "Memory usage is high: $MEM_USAGE%"
    docker compose restart tranvideo
fi
```

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

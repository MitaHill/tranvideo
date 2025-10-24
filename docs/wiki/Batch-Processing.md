# 批量处理指南

本文档介绍如何使用 Tranvideo 的批量处理功能，一次性处理多个视频文件。

## 目录

- [批量处理概述](#批量处理概述)
- [Web 界面批量处理](#web-界面批量处理)
- [API 批量处理](#api-批量处理)
- [批量任务管理](#批量任务管理)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

---

## 批量处理概述

### 什么是批量处理

批量处理允许一次上传多个视频文件，系统会：

1. 创建一个批次（Batch）
2. 为每个视频创建一个子任务
3. 按顺序依次处理所有视频
4. 提供批量下载功能

### 批量处理的优势

- **节省时间**：一次上传，无需重复操作
- **统一管理**：所有任务集中管理
- **批量下载**：一个 ZIP 包下载所有结果
- **队列管理**：自动排队处理

### 限制说明

| 限制项 | 值 | 说明 |
|--------|-----|------|
| 单次最大文件数 | 10 个 | 一次批量最多 10 个文件 |
| 单文件最大大小 | 2GB | 每个文件不超过 2GB |
| 总配额限制 | 依邀请码 | 总时长不超过配额 |
| 并发处理 | 1 个 | 同时只处理一个任务 |

---

## Web 界面批量处理

### 步骤一：选择多个文件

#### 方式一：Ctrl/Cmd + 点击

1. 点击上传区域
2. 在文件选择器中按住 Ctrl（Windows）或 Cmd（Mac）
3. 点击选择多个文件
4. 点击"打开"

#### 方式二：拖拽多个文件

1. 在文件管理器中选择多个视频文件
2. 拖拽到上传区域
3. 松开鼠标

#### 方式三：Shift + 点击（连续选择）

1. 点击第一个文件
2. 按住 Shift
3. 点击最后一个文件
4. 所有中间文件都会被选中

### 步骤二：确认文件列表

上传后会显示文件列表：

```
已选择 5 个文件:

┌──────────────────────────────────────────┐
│ 文件名              时长      大小        │
├──────────────────────────────────────────┤
│ lesson_01.mp4      10:30     125MB       │
│ lesson_02.mp4      15:45     189MB       │
│ lesson_03.mp4      08:20     98MB        │
│ lesson_04.mp4      12:10     145MB       │
│ lesson_05.mp4      09:55     118MB       │
├──────────────────────────────────────────┤
│ 总计               56:40     675MB       │
└──────────────────────────────────────────┘

预估处理时间: 约 30-40 分钟
```

### 步骤三：选择处理模式

与单文件相同，选择：

- **仅生成字幕**：输出 SRT 文件
- **生成带字幕的视频**：输出 SRT + 视频文件

**注意**：批量中所有文件使用相同的处理模式

### 步骤四：开始批量处理

点击"开始批量处理"按钮：

```
批次 ID: batch_20251023_105500
总任务数: 5
状态: 处理中 (1/5)

当前处理: lesson_01.mp4
进度: ████████░░░░░░░░ 50%
翻译原文字幕 (45/90)

队列中:
  ⏳ lesson_02.mp4
  ⏳ lesson_03.mp4
  ⏳ lesson_04.mp4
  ⏳ lesson_05.mp4
```

### 步骤五：监控批量进度

#### 整体进度

```
批次进度: 2/5 已完成 (40%)
总耗时: 15 分钟
预计剩余: 22 分钟
```

#### 各任务状态

```
✅ lesson_01.mp4  已完成  100%
✅ lesson_02.mp4  已完成  100%
🔄 lesson_03.mp4  处理中   65%
⏳ lesson_04.mp4  队列中    0%
⏳ lesson_05.mp4  队列中    0%
```

### 步骤六：下载批量结果

所有任务完成后：

```
✅ 批次处理完成！

已完成: 5/5
失败: 0/5

下载选项:
[下载全部 (ZIP)]  [逐个下载]
```

#### 下载全部（推荐）

点击"下载全部"获得 ZIP 压缩包：

```
batch_20251023_105500.zip
├── lesson_01_raw.srt
├── lesson_01_translated.srt
├── lesson_01_bilingual.srt
├── lesson_01_final.mp4         # 如果是视频模式
├── lesson_02_raw.srt
├── lesson_02_translated.srt
├── lesson_02_bilingual.srt
├── lesson_02_final.mp4
├── ...
└── batch_summary.txt           # 批次摘要
```

#### 逐个下载

展开文件列表，逐个下载每个任务的结果。

---

## API 批量处理

### 创建批量任务

**端点**: `POST /api/batch/process/{invite_code}`

**请求示例**:

```bash
curl -X POST http://localhost:5000/api/batch/process/kindmita \
  -F "files=@lesson_01.mp4" \
  -F "files=@lesson_02.mp4" \
  -F "files=@lesson_03.mp4" \
  -F "files=@lesson_04.mp4" \
  -F "files=@lesson_05.mp4" \
  -F "mode=srt"
```

**响应**:

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
  "total_duration": 3400.0,
  "estimated_time": "约 30 分钟"
}
```

### 查询批量状态

**端点**: `GET /api/batch/{batch_id}`

**请求示例**:

```bash
curl http://localhost:5000/api/batch/batch_20251023_105500
```

**响应**:

```json
{
  "success": true,
  "batch_id": "batch_20251023_105500",
  "status": "processing",
  "progress": "处理中... (2/5)",
  "total": 5,
  "completed": 2,
  "processing": 1,
  "pending": 2,
  "failed": 0,
  "sub_tasks": {
    "20251023_105500_001": {
      "task_id": "20251023_105500_001",
      "video_name": "lesson_01.mp4",
      "status": "已完成",
      "progress": "完成",
      "prog_bar": 100
    },
    "20251023_105500_002": {
      "task_id": "20251023_105500_002",
      "video_name": "lesson_02.mp4",
      "status": "已完成",
      "progress": "完成",
      "prog_bar": 100
    },
    "20251023_105500_003": {
      "task_id": "20251023_105500_003",
      "video_name": "lesson_03.mp4",
      "status": "翻译原文字幕",
      "progress": "翻译中...",
      "prog_bar": 65
    },
    "20251023_105500_004": {
      "task_id": "20251023_105500_004",
      "video_name": "lesson_04.mp4",
      "status": "队列中",
      "progress": "等待处理",
      "prog_bar": 0
    },
    "20251023_105500_005": {
      "task_id": "20251023_105500_005",
      "video_name": "lesson_05.mp4",
      "status": "队列中",
      "progress": "等待处理",
      "prog_bar": 0
    }
  },
  "created_at": "2025-10-23 10:55:00",
  "updated_at": "2025-10-23 11:15:30"
}
```

### 下载批量结果

**端点**: `GET /api/batch/download/{batch_id}`

**请求示例**:

```bash
curl -o batch_result.zip \
  http://localhost:5000/api/batch/download/batch_20251023_105500
```

### Python 批量处理示例

```python
import requests
import time
import os

class BatchProcessor:
    def __init__(self, base_url, invite_code):
        self.base_url = base_url
        self.invite_code = invite_code

    def create_batch(self, video_files, mode="srt"):
        """创建批量任务"""
        url = f"{self.base_url}/batch/process/{self.invite_code}"

        files = [('files', open(f, 'rb')) for f in video_files]
        data = {'mode': mode}

        try:
            response = requests.post(url, files=files, data=data)
            return response.json()
        finally:
            # 关闭文件句柄
            for _, file_obj in files:
                file_obj.close()

    def get_batch_status(self, batch_id):
        """获取批量状态"""
        url = f"{self.base_url}/batch/{batch_id}"
        response = requests.get(url)
        return response.json()

    def download_batch(self, batch_id, output_path):
        """下载批量结果"""
        url = f"{self.base_url}/batch/download/{batch_id}"
        response = requests.get(url, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100
                    print(f"\r下载进度: {progress:.1f}%", end='', flush=True)

        print("\n下载完成!")

    def wait_for_completion(self, batch_id, check_interval=10):
        """等待批量任务完成"""
        while True:
            status = self.get_batch_status(batch_id)

            print(f"\n批次状态: {status['status']}")
            print(f"进度: {status['progress']}")
            print(f"已完成: {status['completed']}/{status['total']}")
            print(f"处理中: {status['processing']}")
            print(f"队列中: {status['pending']}")
            print(f"失败: {status['failed']}")

            # 显示各任务状态
            print("\n任务详情:")
            for task_id, task in status['sub_tasks'].items():
                icon = "✅" if task['status'] == "已完成" else \
                       "❌" if task['status'] == "失败" else \
                       "🔄" if task['status'] in ["processing", "提取原文字幕", "翻译原文字幕"] else \
                       "⏳"
                print(f"  {icon} {task['video_name']:<20} {task['status']:<15} {task['prog_bar']:>3}%")

            if status['status'] == '已完成':
                print("\n✅ 批次处理完成!")
                return True
            elif status['status'] == '失败':
                print("\n❌ 批次处理失败!")
                return False

            time.sleep(check_interval)

# 使用示例
if __name__ == "__main__":
    processor = BatchProcessor(
        base_url="http://localhost:5000/api",
        invite_code="kindmita"
    )

    # 准备视频文件列表
    video_files = [
        "lesson_01.mp4",
        "lesson_02.mp4",
        "lesson_03.mp4",
        "lesson_04.mp4",
        "lesson_05.mp4"
    ]

    # 创建批量任务
    print("创建批量任务...")
    result = processor.create_batch(video_files, mode="srt")
    batch_id = result['batch_id']

    print(f"批次ID: {batch_id}")
    print(f"任务数: {result['total_tasks']}")
    print(f"预计时间: {result['estimated_time']}")

    # 等待完成
    if processor.wait_for_completion(batch_id):
        # 下载结果
        output_file = f"{batch_id}.zip"
        print(f"\n开始下载结果到 {output_file}...")
        processor.download_batch(batch_id, output_file)
        print(f"✅ 批量处理完成，结果已保存到 {output_file}")
```

---

## 批量任务管理

### 批次状态说明

| 状态 | 说明 |
|------|------|
| 队列中 | 整个批次在队列中等待 |
| processing | 批次正在处理中 |
| 已完成 | 所有任务都成功完成 |
| 部分完成 | 部分任务完成，部分失败 |
| 失败 | 所有任务都失败 |

### 子任务状态

每个子任务都有独立的状态：

- **队列中**：等待处理
- **processing**：正在处理
- **提取原文字幕**：语音识别中
- **翻译原文字幕**：翻译中
- **已完成**：成功完成
- **失败**：处理失败

### 批次数据结构

```json
{
  "batch_id": "batch_20251023_105500",
  "status": "processing",
  "total": 5,
  "completed": 2,
  "processing": 1,
  "pending": 2,
  "failed": 0,
  "sub_tasks": {
    "task_id_1": {...},
    "task_id_2": {...},
    ...
  },
  "created_at": "2025-10-23 10:55:00",
  "updated_at": "2025-10-23 11:15:30"
}
```

### 查询单个子任务

也可以单独查询批次中的某个子任务：

```bash
curl http://localhost:5000/api/task/20251023_105500_003
```

---

## 最佳实践

### 1. 文件命名规范

使用清晰的命名规则，便于后期管理：

```
# 好的命名
lesson_01_introduction.mp4
lesson_02_basic_concepts.mp4
lesson_03_advanced_topics.mp4

# 不好的命名
video1.mp4
new_video.mp4
final_final_v2.mp4
```

### 2. 文件组织

按批次组织文件：

```
videos/
├── batch_1_basic/
│   ├── lesson_01.mp4
│   ├── lesson_02.mp4
│   └── lesson_03.mp4
├── batch_2_advanced/
│   ├── lesson_04.mp4
│   ├── lesson_05.mp4
│   └── lesson_06.mp4
└── batch_3_projects/
    ├── project_01.mp4
    └── project_02.mp4
```

### 3. 批次大小控制

#### 推荐批次大小

| 场景 | 推荐文件数 | 原因 |
|------|-----------|------|
| 快速处理 | 2-3 个 | 可快速完成 |
| 系列视频 | 5-8 个 | 平衡效率和管理 |
| 大批量 | 分多个批次 | 避免单批次过大 |

#### 示例：处理 30 个视频

```python
# 分成 3 个批次
batches = [
    videos[0:10],   # 批次 1
    videos[10:20],  # 批次 2
    videos[20:30]   # 批次 3
]

for i, batch in enumerate(batches, 1):
    print(f"处理批次 {i}...")
    result = processor.create_batch(batch)
    processor.wait_for_completion(result['batch_id'])
```

### 4. 配额管理

在批量处理前检查配额：

```python
def check_quota_before_batch(processor, video_files, invite_code):
    """检查配额是否充足"""
    # 计算总时长
    total_duration = sum(get_video_duration(f) for f in video_files)

    # 检查配额
    url = f"{processor.base_url}/invitation/check/{invite_code}"
    response = requests.get(url)
    quota = response.json()

    if quota['quota']['remaining'] < total_duration:
        print(f"⚠️ 配额不足！")
        print(f"需要: {total_duration} 秒")
        print(f"剩余: {quota['quota']['remaining']} 秒")
        return False

    print(f"✅ 配额充足")
    print(f"需要: {total_duration} 秒")
    print(f"剩余: {quota['quota']['remaining']} 秒")
    return True
```

### 5. 错误处理

处理部分失败的批次：

```python
def handle_failed_tasks(processor, batch_id):
    """处理失败的任务"""
    status = processor.get_batch_status(batch_id)

    failed_tasks = []
    for task_id, task in status['sub_tasks'].items():
        if task['status'] == '失败':
            failed_tasks.append({
                'task_id': task_id,
                'video_name': task['video_name'],
                'error': task.get('error', '未知错误')
            })

    if failed_tasks:
        print(f"\n❌ 发现 {len(failed_tasks)} 个失败任务:")
        for task in failed_tasks:
            print(f"  - {task['video_name']}: {task['error']}")

        # 重新处理失败的视频
        retry_files = [task['video_name'] for task in failed_tasks]
        print(f"\n重新处理失败的任务...")
        result = processor.create_batch(retry_files)
        return result['batch_id']

    return None
```

### 6. 进度通知

添加进度通知功能：

```python
def notify_on_complete(batch_id, email=None):
    """批次完成时发送通知"""
    import smtplib
    from email.mime.text import MIMEText

    if email:
        msg = MIMEText(f"批次 {batch_id} 处理完成！")
        msg['Subject'] = 'Tranvideo 批量任务完成'
        msg['From'] = 'noreply@tranvideo.com'
        msg['To'] = email

        # 发送邮件（需要配置 SMTP）
        # smtp = smtplib.SMTP('localhost')
        # smtp.send_message(msg)
        # smtp.quit()

        print(f"✅ 通知已发送到 {email}")
```

---

## 批量下载结果

### ZIP 包结构

```
batch_20251023_105500.zip
├── batch_summary.txt          # 批次摘要
├── lesson_01/
│   ├── raw.srt
│   ├── translated.srt
│   ├── bilingual.srt
│   └── final.mp4             # 仅视频模式
├── lesson_02/
│   ├── raw.srt
│   ├── translated.srt
│   ├── bilingual.srt
│   └── final.mp4
└── ...
```

### 批次摘要示例

```txt
=====================================
Tranvideo 批量处理摘要
=====================================

批次 ID: batch_20251023_105500
创建时间: 2025-10-23 10:55:00
完成时间: 2025-10-23 11:45:30
处理模式: srt

任务统计:
- 总任务数: 5
- 已完成: 5
- 失败: 0
- 总耗时: 50 分钟

任务详情:
1. lesson_01.mp4 - 已完成 (10:30)
2. lesson_02.mp4 - 已完成 (15:45)
3. lesson_03.mp4 - 已完成 (08:20)
4. lesson_04.mp4 - 已完成 (12:10)
5. lesson_05.mp4 - 已完成 (09:55)

总视频时长: 56:40
=====================================
```

### 解压和使用

```bash
# 解压 ZIP 包
unzip batch_20251023_105500.zip -d results/

# 查看目录结构
tree results/

# 使用字幕文件
vlc video.mp4 --sub-file=results/lesson_01/translated.srt
```

---

## 故障排除

### 批量上传失败

**问题**: 无法上传多个文件

**解决方法**:

1. 检查文件数量是否超过 10 个
2. 检查单文件大小是否超过 2GB
3. 检查总大小是否过大（建议 < 10GB）
4. 尝试分批上传

### 部分任务失败

**问题**: 批次中部分任务失败

**解决方法**:

1. 查看失败任务的错误信息
2. 单独重新处理失败的视频
3. 检查失败视频的文件是否损坏

```python
# 重新处理失败的任务
failed_videos = ['lesson_03.mp4', 'lesson_05.mp4']
result = processor.create_batch(failed_videos)
```

### 下载 ZIP 失败

**问题**: 无法下载批量结果

**解决方法**:

1. 检查所有任务是否都已完成
2. 尝试逐个下载任务结果
3. 检查磁盘空间是否充足
4. 重新请求下载链接

### 批次状态不更新

**问题**: 批次状态停滞不前

**解决方法**:

1. 刷新页面或重新查询
2. 检查服务器日志
3. 检查是否有任务卡住
4. 联系管理员

---

## 高级用法

### 自动化批量处理

```python
#!/usr/bin/env python3
"""
自动化批量处理脚本
监控目录，自动批量处理新视频
"""

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BatchHandler(FileSystemEventHandler):
    def __init__(self, processor, batch_size=5):
        self.processor = processor
        self.batch_size = batch_size
        self.pending_files = []

    def on_created(self, event):
        if event.src_path.endswith('.mp4'):
            self.pending_files.append(event.src_path)
            print(f"检测到新文件: {event.src_path}")

            if len(self.pending_files) >= self.batch_size:
                self.process_batch()

    def process_batch(self):
        if not self.pending_files:
            return

        print(f"\n开始处理 {len(self.pending_files)} 个文件...")
        result = self.processor.create_batch(self.pending_files)
        batch_id = result['batch_id']

        self.pending_files = []

        # 等待完成并下载
        if self.processor.wait_for_completion(batch_id):
            self.processor.download_batch(batch_id, f"{batch_id}.zip")

# 运行监控
processor = BatchProcessor("http://localhost:5000/api", "kindmita")
handler = BatchHandler(processor, batch_size=5)

observer = Observer()
observer.schedule(handler, path='./videos', recursive=False)
observer.start()

print("开始监控 ./videos 目录...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
```

---

## 相关文档

- 📖 [基础使用](Basic-Usage.md) - 单文件处理指南
- 🔧 [API 文档](API-Reference.md) - 批量 API 详细文档
- ⚙️ [配置指南](Configuration.md) - 系统配置
- 💡 [故障排除](Troubleshooting.md) - 问题解决

---

**文档版本**: v1.0
**最后更新**: 2025-10-24
**维护者**: MitaHill

[返回 Wiki 首页](Home.md)

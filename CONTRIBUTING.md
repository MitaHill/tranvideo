# 贡献指南 (Contributing Guide)

感谢您对 Tranvideo 项目的关注！我们欢迎各种形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [报告问题](#报告问题)
- [提交代码](#提交代码)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交信息规范](#提交信息规范)

## 行为准则

参与本项目即表示您同意遵守以下准则:

- 尊重所有贡献者
- 接受建设性的批评
- 关注项目的最佳利益
- 对社区成员表现出同理心

## 如何贡献

### 贡献方式

我们欢迎以下形式的贡献:

- 🐛 **报告 Bug** - 发现问题并提交 Issue
- 💡 **功能建议** - 提出新功能想法
- 📖 **改进文档** - 完善或修正文档
- 🔧 **提交代码** - 修复 Bug 或实现新功能
- 🌐 **翻译** - 帮助翻译文档和界面
- 🎨 **设计** - 改进 UI/UX
- 🧪 **测试** - 帮助测试新功能

### 快速开始

1. **Fork 项目**
   ```bash
   # 在 GitHub 上点击 Fork 按钮
   ```

2. **克隆仓库**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tranvideo.git
   cd tranvideo
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行开发**
   - 编写代码
   - 添加测试
   - 更新文档

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 访问 GitHub 仓库
   - 点击 "New Pull Request"
   - 填写 PR 描述

## 报告问题

### 提交 Bug 报告

在提交 Issue 前,请先:

1. 搜索现有 Issues,避免重复
2. 确认问题可以复现
3. 收集相关信息

**Bug 报告模板**:

```markdown
### 问题描述
简要描述问题

### 复现步骤
1. 第一步
2. 第二步
3. ...

### 期望行为
应该发生什么

### 实际行为
实际发生了什么

### 环境信息
- 操作系统: [例如 Ubuntu 22.04]
- Docker 版本: [例如 24.0.0]
- GPU: [例如 RTX 4070 Ti]
- 显存: [例如 8GB]
- Tranvideo 版本: [例如 v0.6.0]

### 日志信息
```
粘贴相关日志
```

### 截图
如果适用,添加截图
```

### 功能建议

**功能建议模板**:

```markdown
### 功能描述
清晰简洁地描述您希望添加的功能

### 使用场景
这个功能解决了什么问题?

### 建议的实现方式
(可选) 您认为应该如何实现

### 替代方案
(可选) 您考虑过的其他解决方案

### 附加信息
其他相关信息、截图或示例
```

## 提交代码

### Pull Request 流程

1. **Fork 并克隆**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tranvideo.git
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **开发和测试**
   - 编写代码
   - 添加/更新测试
   - 确保所有测试通过
   - 更新文档

4. **提交更改**
   ```bash
   git commit -m "feat: add amazing feature"
   ```

5. **保持同步**
   ```bash
   git remote add upstream https://github.com/MitaHill/tranvideo.git
   git fetch upstream
   git rebase upstream/main
   ```

6. **推送到 Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **创建 Pull Request**
   - 提供清晰的标题和描述
   - 引用相关 Issues
   - 添加截图(如适用)
   - 等待代码审查

### PR 检查清单

在提交 PR 前,请确认:

- [ ] 代码遵循项目的代码规范
- [ ] 已添加必要的测试
- [ ] 所有测试通过
- [ ] 已更新相关文档
- [ ] 提交信息符合规范
- [ ] 已从最新的 main 分支 rebase
- [ ] 没有合并冲突

## 开发流程

### 搭建开发环境

1. **克隆项目**
   ```bash
   git clone https://github.com/MitaHill/tranvideo.git
   cd tranvideo
   ```

2. **安装依赖**
   ```bash
   # 创建虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows

   # 安装依赖
   pip install -r requirements.txt
   ```

3. **下载模型文件**
   ```bash
   # 下载 Whisper 模型
   mkdir -p whisper
   cd whisper
   wget https://huggingface.co/openai/whisper-large-v3-turbo/resolve/main/large-v3-turbo.pt
   cd ..
   ```

4. **配置环境**
   ```bash
   # 编辑配置文件
   vim config/tran-py.json
   ```

5. **运行服务**
   ```bash
   python main.py
   ```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_whisper.py

# 生成覆盖率报告
pytest --cov=src tests/
```

### 代码检查

```bash
# 代码格式化
black src/

# 代码检查
flake8 src/

# 类型检查
mypy src/
```

## 代码规范

### Python 代码规范

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范:

- 使用 4 个空格缩进
- 行长度不超过 88 字符 (Black 默认)
- 使用有意义的变量名
- 添加适当的注释和文档字符串

**示例**:

```python
def process_video(video_path: str, mode: str = "subtitle") -> dict:
    """
    处理视频文件并生成字幕

    Args:
        video_path: 视频文件路径
        mode: 处理模式，可选 "subtitle" 或 "video"

    Returns:
        包含处理结果的字典

    Raises:
        FileNotFoundError: 当视频文件不存在时
        ValueError: 当模式参数无效时
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    if mode not in ["subtitle", "video"]:
        raise ValueError(f"无效的模式: {mode}")

    # 处理逻辑
    result = {"status": "success", "mode": mode}
    return result
```

### 文档规范

- 使用 Markdown 格式
- 遵循中文文案排版指北
- 提供清晰的代码示例
- 保持文档与代码同步

## 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范:

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化(不影响代码运行)
- `refactor`: 重构(既不是新功能也不是修复)
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链更新
- `ci`: CI 配置更新

### 示例

```bash
# 新功能
git commit -m "feat: add batch download support"

# Bug 修复
git commit -m "fix: resolve memory leak in VRAM manager"

# 文档更新
git commit -m "docs: update API documentation"

# 带 scope 和 body
git commit -m "feat(api): add new translation endpoint

- Add POST /api/translate endpoint
- Support multiple language pairs
- Add rate limiting

Closes #123"
```

## 分支命名规范

- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 重构
- `test/xxx` - 测试

示例:
```bash
feature/batch-processing
fix/vram-memory-leak
docs/api-guide
refactor/task-manager
```

## 版本发布

版本发布由项目维护者负责,流程详见 [RELEASE_GUIDE.md](RELEASE_GUIDE.md)。

贡献者可以:
- 参与版本规划讨论
- 帮助测试预发布版本
- 更新 CHANGELOG.md

## 社区交流

- **GitHub Issues**: [提交问题](https://github.com/MitaHill/tranvideo/issues)
- **GitHub Discussions**: [参与讨论](https://github.com/MitaHill/tranvideo/discussions)
- **邮件**: kindmitaishere@gmail.com
- **论坛**: [cnm.clash.ink](https://cnm.clash.ink)

## 许可证

提交代码即表示您同意将贡献内容以 MIT 许可证发布。

## 致谢

感谢所有贡献者的付出！您的每一个贡献都让 Tranvideo 变得更好。

---

**最后更新**: 2025-10-23

# 发布指南 (Release Guide)

本文档详细说明 Tranvideo 项目的版本发布流程。

## 目录

- [准备工作](#准备工作)
- [发布流程](#发布流程)
- [Docker镜像发布](#docker镜像发布)
- [GitHub Release](#github-release)
- [发布后工作](#发布后工作)
- [回滚流程](#回滚流程)

## 准备工作

### 1. 环境检查

```bash
# 确认在正确的分支
git branch

# 拉取最新代码
git pull origin develop

# 检查工作区状态
git status
```

### 2. 版本号确定

根据 [VERSION_POLICY.md](VERSION_POLICY.md) 确定新版本号:

- 主版本号: 不兼容的API修改
- 次版本号: 新功能添加(向下兼容)
- 修订号: Bug修复(向下兼容)

**示例**:
```
当前版本: 0.6.0
下一版本: 0.7.0 (新增功能)
下一版本: 0.6.1 (Bug修复)
下一版本: 1.0.0 (正式版发布)
```

## 发布流程

### 步骤 1: 创建发布分支

```bash
# 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/0.7.0
```

### 步骤 2: 更新版本信息

#### 2.1 更新 CHANGELOG.md

```markdown
## [0.7.0] - 2025-10-23

### 新增
- 新功能A
- 新功能B

### 优化
- 性能优化C

### 修复
- Bug修复D
```

#### 2.2 更新 README.md

更新版本徽章和相关信息:

```markdown
## 📋 版本信息

- **当前版本**: v0.7.0
- **发布日期**: 2025-10-23
- **Docker镜像**: `kindmitaishere/tranvideo:0.7.0`
```

#### 2.3 更新 docker-compose.yaml

```yaml
tranvideo:
  image: kindmitaishere/tranvideo:0.7.0  # 更新版本号
```

### 步骤 3: 测试

```bash
# 运行单元测试(如果有)
pytest tests/

# 本地Docker构建测试
docker build -t tranvideo:0.7.0-test .

# 启动测试
docker run --rm tranvideo:0.7.0-test

# 功能测试
# - 上传视频
# - 字幕生成
# - 翻译功能
# - API接口
```

### 步骤 4: 代码审查

```bash
# 提交所有更改
git add .
git commit -m "chore: prepare release 0.7.0"

# 推送发布分支
git push origin release/0.7.0
```

创建 Pull Request: `release/0.7.0 → main`

### 步骤 5: 合并到主分支

```bash
# 审查通过后,合并到 main
git checkout main
git pull origin main
git merge --no-ff release/0.7.0 -m "Release version 0.7.0"

# 创建版本标签
git tag -a v0.7.0 -m "Release version 0.7.0

主要变更:
- 新增功能A
- 新增功能B
- 性能优化C
- Bug修复D

完整变更日志: https://github.com/MitaHill/tranvideo/blob/main/CHANGELOG.md#070"

# 推送到远程
git push origin main
git push origin v0.7.0
```

### 步骤 6: 同步到 develop

```bash
# 将发布更改同步回 develop 分支
git checkout develop
git merge --no-ff release/0.7.0 -m "Merge release 0.7.0 into develop"
git push origin develop

# 删除发布分支
git branch -d release/0.7.0
git push origin --delete release/0.7.0
```

## Docker镜像发布

### 方式一: 手动构建推送

```bash
# 构建 Docker 镜像
docker build -t kindmitaishere/tranvideo:0.7.0 .

# 创建多个标签
docker tag kindmitaishere/tranvideo:0.7.0 kindmitaishere/tranvideo:0.7
docker tag kindmitaishere/tranvideo:0.7.0 kindmitaishere/tranvideo:latest

# 推送到 Docker Hub
docker push kindmitaishere/tranvideo:0.7.0
docker push kindmitaishere/tranvideo:0.7
docker push kindmitaishere/tranvideo:latest

# 验证镜像
docker pull kindmitaishere/tranvideo:0.7.0
docker run --rm kindmitaishere/tranvideo:0.7.0 python --version
```

### 方式二: 使用 CI/CD (推荐)

配置 GitHub Actions 自动构建和推送:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: kindmitaishere/tranvideo
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=raw,value=latest

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
```

## GitHub Release

### 创建 GitHub Release

1. 访问 [GitHub Releases 页面](https://github.com/MitaHill/tranvideo/releases)

2. 点击 "Draft a new release"

3. 填写发布信息:

```markdown
## 标签版本
v0.7.0

## 发布标题
Tranvideo v0.7.0 - 功能名称

## 描述

### 🎉 主要更新

- 🎯 新功能A - 详细说明
- 🌍 新功能B - 详细说明
- ⚡ 性能优化C - 详细说明

### 🐛 问题修复

- 修复显存泄漏问题
- 修复任务状态同步问题

### 📦 Docker 镜像

\`\`\`bash
docker pull kindmitaishere/tranvideo:0.7.0

# 或使用 docker-compose
docker compose pull
docker compose up -d
\`\`\`

### 📚 文档

- [完整更新日志](https://github.com/MitaHill/tranvideo/blob/main/CHANGELOG.md)
- [使用文档](https://github.com/MitaHill/tranvideo/wiki)
- [API文档](https://tranvideo.clash.ink/api-docs.html)

### ⚠️ 升级提示

1. 备份现有数据
2. 停止当前服务: `docker compose down`
3. 拉取新版本: `docker compose pull`
4. 启动服务: `docker compose up -d`

### 🔗 相关链接

- [官方网站](https://tranvideo.clash.ink)
- [技术博客](https://b.clash.ink)
- [问题反馈](https://github.com/MitaHill/tranvideo/issues)

---

**完整变更日志**: https://github.com/MitaHill/tranvideo/compare/v0.6.0...v0.7.0
```

4. 上传附加文件(如有):
   - 编译后的二进制文件
   - 额外的配置文件
   - 发布说明PDF

5. 选择发布类型:
   - ✅ 正式版本 (Latest release)
   - ⬜ 预发布版本 (Pre-release) - 用于 alpha/beta/rc

6. 点击 "Publish release"

### 自动化 GitHub Release (推荐)

使用 GitHub CLI 自动创建:

```bash
# 安装 gh CLI
# https://cli.github.com/

# 从 CHANGELOG.md 提取发布说明
gh release create v0.7.0 \
  --title "Tranvideo v0.7.0" \
  --notes-file release-notes.md \
  --draft  # 先创建草稿,检查后再发布

# 发布草稿
gh release edit v0.7.0 --draft=false
```

## 发布后工作

### 1. 验证发布

```bash
# 检查 GitHub Release
curl -s https://api.github.com/repos/MitaHill/tranvideo/releases/latest | jq .tag_name

# 验证 Docker 镜像
docker pull kindmitaishere/tranvideo:0.7.0
docker pull kindmitaishere/tranvideo:latest

# 检查镜像标签
curl -s https://registry.hub.docker.com/v2/repositories/kindmitaishere/tranvideo/tags/ | jq
```

### 2. 更新文档网站

- 更新官方网站版本信息
- 更新 API 文档
- 发布博客文章

### 3. 社区公告

在以下渠道发布更新公告:

- GitHub Discussions
- 社区论坛 (https://cnm.clash.ink)
- 技术博客 (https://b.clash.ink)
- 相关社交媒体

公告模板:

```markdown
🎉 Tranvideo v0.7.0 发布!

我们很高兴地宣布 Tranvideo v0.7.0 正式发布!

本次更新包括:
- 🎯 新功能A
- 🌍 新功能B
- ⚡ 性能提升

📦 Docker 镜像:
docker pull kindmitaishere/tranvideo:0.7.0

📖 完整说明:
https://github.com/MitaHill/tranvideo/releases/tag/v0.7.0

欢迎试用并提供反馈!
```

### 4. 监控和反馈

- 监控 GitHub Issues
- 收集用户反馈
- 关注性能指标
- 准备 Hotfix (如需要)

## 回滚流程

如果发现严重问题需要回滚:

### 1. Docker 镜像回滚

```bash
# 更新 docker-compose.yaml 为上一版本
tranvideo:
  image: kindmitaishere/tranvideo:0.6.0

# 重新部署
docker compose pull
docker compose up -d
```

### 2. Git 回滚

```bash
# 创建紧急修复分支
git checkout v0.6.0
git checkout -b hotfix/0.6.1

# 修复问题后发布 0.6.1
```

### 3. 删除有问题的 Release

```bash
# 删除 GitHub Release (仅在非常严重的情况下)
gh release delete v0.7.0 --yes

# 删除 Git 标签
git tag -d v0.7.0
git push origin :refs/tags/v0.7.0
```

### 4. 发布公告

在 GitHub 和社区发布回滚公告,说明原因和解决方案。

## 紧急修复发布 (Hotfix)

对于生产环境的紧急问题:

```bash
# 1. 从 main 创建 hotfix 分支
git checkout main
git checkout -b hotfix/0.7.1

# 2. 修复问题
# ... 进行修复 ...

# 3. 更新 CHANGELOG.md
## [0.7.1] - 2025-10-24
### 修复
- 紧急修复问题描述

# 4. 提交并测试
git commit -am "fix: 紧急修复问题"

# 5. 合并到 main 和 develop
git checkout main
git merge --no-ff hotfix/0.7.1
git tag -a v0.7.1 -m "Hotfix 0.7.1"
git push origin main v0.7.1

git checkout develop
git merge --no-ff hotfix/0.7.1
git push origin develop

# 6. 立即构建和发布 Docker 镜像
docker build -t kindmitaishere/tranvideo:0.7.1 .
docker push kindmitaishere/tranvideo:0.7.1

# 7. 创建 GitHub Release 并标注为 Hotfix
```

## 检查清单

使用此清单确保发布流程完整:

### 发布前
- [ ] 确定版本号
- [ ] 更新 CHANGELOG.md
- [ ] 更新 README.md
- [ ] 更新 docker-compose.yaml
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 创建发布分支

### 发布中
- [ ] 合并到 main 分支
- [ ] 创建 Git 标签
- [ ] 构建 Docker 镜像
- [ ] 推送 Docker 镜像
- [ ] 创建 GitHub Release
- [ ] 同步到 develop 分支

### 发布后
- [ ] 验证 Docker 镜像
- [ ] 验证 GitHub Release
- [ ] 更新文档网站
- [ ] 发布社区公告
- [ ] 监控问题反馈

---

**参考文档**:
- [VERSION_POLICY.md](VERSION_POLICY.md) - 版本管理策略
- [CHANGELOG.md](CHANGELOG.md) - 变更日志
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南

**最后更新**: 2025-10-23

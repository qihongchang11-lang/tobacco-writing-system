# 🚀 云端部署指南 - 一键上线访问

## 🎯 概述

通过云端部署，用户可以直接访问网址使用完整的Agent系统，无需本地安装配置。

## ☁️ 部署选项（推荐顺序）

### 方案1：Streamlit Cloud（推荐）⭐
- ✅ **完全免费**
- ✅ **最简单**，GitHub连接即可
- ✅ **专为Streamlit优化**
- ❌ 需要公开GitHub仓库

### 方案2：Railway 
- ✅ **部署简单**
- ✅ **性能优秀**
- ✅ **支持私有仓库**
- ⚠️ 免费额度有限

### 方案3：Render
- ✅ **慷慨的免费额度**
- ✅ **支持多种应用类型**
- ⚠️ 冷启动时间较长

---

## 🚀 方案1：Streamlit Cloud 部署（推荐）

### 准备工作
1. **GitHub账号**：确保你有GitHub账号
2. **Claude API密钥**：在 https://console.anthropic.com/ 获取

### 部署步骤

#### 第1步：上传代码到GitHub
```bash
# 如果还没有Git仓库
git init
git add .
git commit -m "Initial commit"

# 创建GitHub仓库并推送
# (在GitHub.com创建新仓库：tobacco-writing-system)
git remote add origin https://github.com/你的用户名/tobacco-writing-system.git
git push -u origin main
```

#### 第2步：部署到Streamlit Cloud
1. 访问 **https://share.streamlit.io/**
2. 使用GitHub账号登录
3. 点击 **"New app"**
4. 选择你的仓库：`tobacco-writing-system`
5. 主文件路径：`streamlit_app.py`
6. 点击 **"Deploy!"**

#### 第3步：配置环境变量
1. 在Streamlit Cloud应用页面
2. 点击 **"Settings"** → **"Secrets"**
3. 添加以下内容：
```toml
CLAUDE_API_KEY = "sk-ant-api03-你的密钥"
```
4. 保存并重启应用

#### 第4步：访问应用
- 部署完成后，你会得到一个网址，例如：
- **https://tobacco-writing-system.streamlit.app/**
- 用户可以直接访问使用！

---

## 🚀 方案2：Railway 部署

### 部署步骤
1. 访问 **https://railway.app/**
2. 使用GitHub登录
3. 点击 **"New Project"** → **"Deploy from GitHub repo"**
4. 选择你的仓库
5. 在环境变量中设置：
   - `CLAUDE_API_KEY`: 你的API密钥
6. Railway会自动检测并使用 `railway.toml` 配置
7. 部署完成后获得访问网址

---

## 🚀 方案3：Render 部署

### 部署步骤
1. 访问 **https://render.com/**
2. 注册并连接GitHub
3. 点击 **"New +"** → **"Web Service"**
4. 选择你的仓库
5. Render会自动检测 `render.yaml` 配置
6. 在环境变量中设置：
   - `CLAUDE_API_KEY`: 你的API密钥
7. 点击 **"Create Web Service"**

---

## 🔧 本地测试云端版本

在部署前，可以本地测试云端优化版本：

```bash
# 安装云端依赖
pip install -r requirements-cloud.txt

# 设置环境变量
export CLAUDE_API_KEY="你的密钥"

# 启动云端版本
streamlit run streamlit_app.py
```

---

## 🎯 部署后的访问体验

用户访问你的网址后，可以：

1. **直接使用**：无需任何配置
2. **完整功能**：调用全部6个Agent
3. **实时处理**：看到完整的改写流程
4. **结果导出**：下载改写后的文档

### 用户界面特色
- 🎭 **体裁识别**：自动判断文章类型
- 🏗️ **结构重组**：优化文章布局
- ✨ **风格改写**：转换为烟草报风格
- 🔍 **事实校对**：检查准确性
- 📊 **质量评估**：多维度评分
- 💾 **导出下载**：TXT/Markdown格式

---

## ⚡ 快速部署（5分钟上线）

如果你想最快速度上线：

### 使用我们的模板仓库
1. Fork这个项目到你的GitHub
2. 修改仓库名为 `tobacco-writing-system`
3. 在Streamlit Cloud部署
4. 添加你的API密钥到Secrets
5. 完成！

### 一键部署链接（即将提供）
我们会提供一键部署按钮，点击即可自动部署到各个平台。

---

## 🎉 成功标志

部署成功后，你将拥有：

### ✅ **完整的在线服务**
- 用户直接访问网址即可使用
- 完全调用我们的Agent系统
- 无需用户配置任何环境

### ✅ **专业的改写效果**
- 体裁判定 → 结构重组 → 风格改写 → 事实校对 → 版式导出
- 符合中国烟草报风格要求
- 可追溯的修改过程

### ✅ **用户友好的体验**
- 简洁直观的界面
- 实时处理进度显示
- 详细的结果分析和导出

这样就真正实现了**云端部署，直接访问，完整调用Agent系统**的目标！

需要我帮你完成具体的部署操作吗？
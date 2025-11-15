# 智能文稿改写系统 - 统一仓库

## 📋 项目简介

本仓库包含两个独立的AI驱动智能改写系统：

### 1. 东方烟草报 & 新华财经风格改写系统（端口8081）
基于Few-shot学习的新闻文稿改写，支持两种专业财经报道风格

### 2. CNIPA发明专利高质量改写系统（端口8082）
符合中国国家知识产权局标准的专利文档自动生成系统

**两个系统共享开发环境，但功能完全独立，可分别部署使用。**

---

## 🎯 系统概览

### 新闻改写系统

**核心功能**：
- ✅ 东方烟草报风格：行业专业、准确严谨
- ✅ 新华财经风格：文学化、诗意化、修辞丰富
- ✅ Few-shot学习（34个高质量样本）
- ✅ 混合检索（BM25 + 语义相似度）
- ✅ XHF文学化增强组件
- ✅ 约束解码保护重要实体

**开发程度**：90%完成
**端口**：8081(API) / 8501(Streamlit)
**主要文件**：`news_api_main.py`, `streamlit_app.py`, `core/`, `agents/`, `knowledge_base/`

### 专利生成系统

**核心功能**：
- 🔧 自动生成专利四件套（说明书、权利要求书、摘要、交底书）
- 🔧 PSE提取（Problem-Solution-Effect）
- 🔧 KTF DAG构建（关键技术特征有向无环图）
- 🔧 6个质量门自动验证
- 🔧 CNIPA 2024标准合规

**开发程度**：60-70%完成（框架完整，业务逻辑待补全）
**端口**：8082
**主要文件**：`patent_api_main.py`, `docs/patent/`

---

## 🚀 快速开始

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/qihongchang11-lang/tobacco-writing-system.git
cd tobacco-writing-system

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建`.env`文件：

```bash
cp .env.separated .env
# 编辑.env文件，配置API密钥和端口
```

示例配置：
```env
# OpenAI API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 新闻系统
NEWS_API_HOST=0.0.0.0
NEWS_API_PORT=8081

# 专利系统
PATENT_API_HOST=0.0.0.0
PATENT_API_PORT=8082
```

### 启动服务

#### 启动新闻系统

```bash
# FastAPI后端（端口8081）
python news_api_main.py

# Streamlit前端（端口8501）
streamlit run streamlit_app.py

# 使用启动脚本
./scripts/start-news.sh
```

访问：http://localhost:8081/docs 或 http://localhost:8501

#### 启动专利系统

```bash
# FastAPI后端（端口8082）
python patent_api_main.py

# 使用启动脚本
./scripts/start-patent.sh
```

访问：http://localhost:8082/docs

#### 同时启动两个系统

```bash
./scripts/start-all.sh
```

---

## 📁 项目结构

```
tobacco-writing-system/
├── README.md                          # 本文件（总览）
│
├── 【新闻系统】
├── news_api_main.py                   # 新闻API入口
├── streamlit_app.py                   # Streamlit前端
├── core/                              # 核心模块
│   ├── constraint_decoder.py          # 约束解码器
│   ├── xhf_style_injector.py          # XHF风格注入器
│   ├── xhf_quality_checker.py         # XHF质量检查器
│   └── ...
├── agents/                            # 智能代理
│   └── few_shot_rewriter.py          # Few-shot改写器
├── knowledge_base/                    # 知识库（34样本）
│   └── intelligent_retriever.py       # 智能检索器
├── conf/                              # 新闻系统配置
│
├── 【专利系统】
├── patent_api_main.py                 # 专利API入口
├── docs/patent/                       # 专利文档
│   ├── Project_Requirements_Summary.md
│   └── Patent_Rewrite_SOP_v1.1.md
│
├── 【共享文档】
├── docs/
│   ├── shared/                        # 跨系统文档
│   │   ├── SYSTEM_ANALYSIS_REPORT.md  # ⭐三系统完整分析
│   │   └── GITHUB_SYNC_README.md
│   └── news-system-docs/              # 新闻系统文档
│       ├── PROJECT_K2_SPECIFICATION.md
│       ├── PHASE1_COMPLETION_REPORT.md
│       └── ...
│
├── 【部署脚本】
├── scripts/
│   ├── start-news.sh                  # 启动新闻系统
│   ├── start-patent.sh                # 启动专利系统
│   └── start-all.sh                   # 同时启动
│
└── 【配置】
    ├── .env                           # 环境变量（不提交）
    ├── .env.separated                 # 环境变量示例
    └── requirements.txt               # Python依赖
```

---

## 📡 API使用

### 新闻系统

```bash
# 改写接口
curl -X POST http://localhost:8081/rewrite \
  -H "Content-Type: application/json" \
  -d '{
    "text": "原始文稿...",
    "style": "tobacco",
    "strict_mode": false
  }'

# 健康检查
curl http://localhost:8081/health
```

### 专利系统

```bash
# 专利处理
curl -X POST http://localhost:8082/process \
  -H "Content-Type: application/json" \
  -d '{
    "draft_content": "发明草稿...",
    "title": "一种xxx装置",
    "invention_type": "invention",
    "enable_checks": true
  }'

# 质量门检查
curl http://localhost:8082/gates/A
```

---

## 📚 重要文档

### 必读
- [三系统完整分析报告](docs/shared/SYSTEM_ANALYSIS_REPORT.md) ⭐ **推荐首读**
- [项目工作总结与经验教训](docs/shared/PROJECT_WORK_SUMMARY.md) 📋 **完整工作回顾**

### 项目管理与决策
- [技术决策记录(ADR)](docs/shared/ARCHITECTURE_DECISIONS.md) - 重要技术决策的背景和理由
- [开发与协作最佳实践](docs/shared/BEST_PRACTICES.md) - 基于实战的开发指南

### 新闻系统
- [K2项目规格](docs/news-system-docs/PROJECT_K2_SPECIFICATION.md)
- [阶段1完成报告](docs/news-system-docs/PHASE1_COMPLETION_REPORT.md)
- [质量差距分析](docs/news-system-docs/QUALITY_GAP_ANALYSIS_REPORT.md)
- [使用指南](docs/news-system-docs/USAGE_GUIDE.md)
- [一键工作流操作手册](docs/news-system-docs/ONE_CLICK_WORKFLOW.md)
- [简易入口汇总](docs/news-system-docs/SIMPLE_ENTRY.md)
- [Claude控制台版流程](docs/news-system-docs/CLAUDE_CONSOLE_GUIDE.md)
- [完整开发计划](docs/news-system-docs/DEVELOPMENT_PLAN_FINAL.md)

### 专利系统
- [项目需求总结](docs/patent/Project_Requirements_Summary.md)
- [专利改写SOP v1.1](docs/patent/Patent_Rewrite_SOP_v1.1.md)

### 通用运维与部署
- [云端部署指南](docs/shared/CLOUD_DEPLOY_GUIDE.md)
- [部署检查清单](docs/shared/DEPLOY_CHECKLIST.md)
- [服务分离实施说明](docs/shared/README_SERVICE_SEPARATION.md)
- [服务分离PR摘要](docs/shared/PR_SUMMARY_SERVICE_SEPARATION.md)

---

## 🔧 开发状态

| 系统 | 进度 | 主要功能 | 待完成 |
|------|------|----------|--------|
| 新闻系统 | 90% | ✅ Few-shot学习<br>✅ 双风格支持<br>✅ XHF增强 | ⏳ 风格选择参数<br>⏳ 性能优化 |
| 专利系统 | 60-70% | ✅ API框架<br>✅ 文档规范<br>✅ 质量门定义 | ⏳ PSE提取器<br>⏳ KTF构建<br>⏳ Claims生成 |

---

## 🤝 协作指南

### 新协作者快速上手

1. **理解全局**（15分钟）：阅读 [SYSTEM_ANALYSIS_REPORT.md](docs/shared/SYSTEM_ANALYSIS_REPORT.md)
2. **选择系统**：根据兴趣阅读对应系统文档
3. **查看代码**：
   - 新闻：`news_api_main.py` + `agents/few_shot_rewriter.py`
   - 专利：`patent_api_main.py` + `docs/patent/`

### 为什么单仓库？

✅ 保留完整Git历史
✅ 统一协作环境
✅ 共享文档和分析报告
✅ 可能有共享代码模块

---

## 📞 联系方式

- **Issues**: https://github.com/qihongchang11-lang/tobacco-writing-system/issues
- **项目主页**: https://github.com/qihongchang11-lang/tobacco-writing-system

---

**最后更新**：2025年11月14日
**维护状态**：活跃开发中
**技术栈**：Python + FastAPI + Streamlit + DeepSeek + Sentence-Transformers

🤖 Generated with Claude Code
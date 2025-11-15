# 文档索引 - 东方烟草报风格改写系统

## 📚 文档导航

本项目包含完整的技术文档和知识沉淀，帮助您快速上手和持续改进系统。

---

## 📖 主要文档

### 1. [README.md](../README.md)
**快速入门指南**

**适用人群**: 新用户、首次使用者
**包含内容**:
- ✅ 项目简介和核心特性
- ✅ 快速安装和启动步骤
- ✅ 使用示例（Web界面 + API）
- ✅ 常见问题解答
- ✅ 版本历史和路线图

**推荐阅读顺序**: 🥇 首先阅读

---

### 2. [PROJECT_IMPROVEMENTS.md](PROJECT_IMPROVEMENTS.md)
**项目改进记录与使用指南**

**适用人群**: 维护者、问题排查、后续改进
**包含内容**:
- ✅ 完整的项目结构说明
- ✅ 关键文件详细改进记录
- ✅ 常见问题和解决方案
- ✅ 性能指标和监控建议
- ✅ 版本历史和优化方向

**核心价值**:
- 🔍 **快速定位**: 按文件名快速找到改进位置
- 🐛 **问题排查**: 详细的故障排查和修复记录
- 📊 **性能参考**: 明确的性能指标和优化建议

**典型使用场景**:
1. 遇到超时问题？→ 查看"问题1: 请求超时"章节
2. 标题显示不全？→ 查看"问题2: 标题显示不完整"章节
3. 需要修改超时配置？→ 查看"关键文件改进详解"

**推荐阅读顺序**: 🥈 使用中遇到问题时查阅

---

### 3. [TECHNICAL_METHODOLOGY.md](TECHNICAL_METHODOLOGY.md)
**技术方案与方法论总结**

**适用人群**: 开发者、架构设计、类似项目复用
**包含内容**:
- ✅ 核心方法论（Few-shot学习、混合检索）
- ✅ 系统架构设计原则
- ✅ 核心技术组件详解
- ✅ 提示词工程最佳实践
- ✅ 前端开发规范
- ✅ API设计规范
- ✅ 测试与质量保证
- ✅ 项目复用指南

**核心价值**:
- 📐 **架构参考**: 完整的系统设计思路
- 💡 **方法论沉淀**: 可复用的技术方案
- 🔧 **最佳实践**: 经过验证的开发规范
- 🚀 **快速复用**: 新项目启动指南

**典型使用场景**:
1. 理解Few-shot学习原理？→ 查看"1. 学习驱动的文本风格迁移框架"
2. 设计新的检索算法？→ 查看"3.2 混合检索算法实现"
3. 需要编写提示词？→ 查看"3.1 Few-shot学习提示词工程"
4. 开发类似项目？→ 查看"🎯 项目复用指南"

**推荐阅读顺序**: 🥉 深入理解或新项目启动时学习

---

## 🗂️ 文档层次结构

```
tobacco-writing-pipeline/
├── README.md                          # 【入门】快速开始
├── docs/
│   ├── INDEX.md                       # 【本文档】文档导航
│   ├── PROJECT_IMPROVEMENTS.md        # 【实战】改进记录和问题排查
│   └── TECHNICAL_METHODOLOGY.md       # 【进阶】技术方案和方法论
└── api_main.py, frontend/app.py...   # 源代码（参考文档中的行号）
```

---

## 📋 按使用场景查找

### 场景1: 我是新用户，第一次使用系统
**推荐路径**:
1. 阅读 [README.md](../README.md) 了解系统功能
2. 按照"快速开始"章节安装和启动
3. 通过"使用示例"章节学习如何使用

### 场景2: 系统出现问题，需要排查
**推荐路径**:
1. 查看 [PROJECT_IMPROVEMENTS.md](PROJECT_IMPROVEMENTS.md) 的"常见问题和解决方案"章节
2. 根据具体问题找到对应的修复方法
3. 如果是新问题，参考"关键文件改进详解"了解系统组件

### 场景3: 需要添加新功能或优化
**推荐路径**:
1. 查看 [PROJECT_IMPROVEMENTS.md](PROJECT_IMPROVEMENTS.md) 的"后续优化方向"
2. 参考 [TECHNICAL_METHODOLOGY.md](TECHNICAL_METHODOLOGY.md) 了解技术方案
3. 按照"开发指南"进行开发

### 场景4: 想深入理解技术原理
**推荐路径**:
1. 阅读 [TECHNICAL_METHODOLOGY.md](TECHNICAL_METHODOLOGY.md) 的"核心方法论"
2. 学习"核心技术组件"章节的详细实现
3. 查看源代码中标注的关键行号

### 场景5: 准备开发类似项目
**推荐路径**:
1. 阅读 [TECHNICAL_METHODOLOGY.md](TECHNICAL_METHODOLOGY.md) 全文
2. 重点关注"项目复用指南"章节
3. 参考"最佳实践总结"进行开发

---

## 🔍 快速查找指南

### 按关键词查找

| 关键词 | 在哪个文档查找 | 章节 |
|--------|--------------|------|
| 安装、启动、配置 | README.md | 快速开始 |
| 超时问题 | PROJECT_IMPROVEMENTS.md | 问题1: 请求超时 |
| 标题显示不全 | PROJECT_IMPROVEMENTS.md | 问题2: 标题显示不完整 |
| Few-shot学习 | TECHNICAL_METHODOLOGY.md | 1. 学习驱动的文本风格迁移框架 |
| 混合检索 | TECHNICAL_METHODOLOGY.md | 3.2 混合检索算法实现 |
| 约束解码 | TECHNICAL_METHODOLOGY.md | 3.3 约束解码器设计 |
| 提示词工程 | TECHNICAL_METHODOLOGY.md | 3.1 Few-shot学习提示词工程 |
| 前端开发 | TECHNICAL_METHODOLOGY.md | 4. 前端开发最佳实践 |
| API设计 | TECHNICAL_METHODOLOGY.md | 5. API设计规范 |
| 添加新栏目 | README.md | 开发指南 → 添加新栏目 |
| 性能指标 | PROJECT_IMPROVEMENTS.md | 📊 性能指标 |

### 按文件查找改进记录

| 文件路径 | 在哪个文档查找 | 章节 |
|---------|--------------|------|
| agents/few_shot_rewriter.py | PROJECT_IMPROVEMENTS.md | 关键文件改进详解 → 1 |
| frontend/app.py | PROJECT_IMPROVEMENTS.md | 关键文件改进详解 → 2 |
| knowledge_base/intelligent_retriever.py | PROJECT_IMPROVEMENTS.md | 关键文件改进详解 → 3 |
| api_main.py | PROJECT_IMPROVEMENTS.md | 关键文件改进详解 → 4 |

---

## 📚 扩展阅读

### 在线文档
- **API交互文档**: 启动服务后访问 http://localhost:8081/docs
- **健康检查**: http://localhost:8081/health

### 学习资源
- Few-shot Learning相关论文（见TECHNICAL_METHODOLOGY.md参考资料）
- FastAPI官方文档
- Streamlit官方文档
- Sentence-Transformers文档

---

## 🔄 文档更新记录

| 日期 | 更新内容 | 涉及文档 |
|------|---------|---------|
| 2025-11-08 | 创建完整文档体系 | 全部文档 |
| 2025-11-08 | 记录v2.0.0学习驱动升级 | PROJECT_IMPROVEMENTS.md |
| 2025-11-08 | 沉淀技术方法论 | TECHNICAL_METHODOLOGY.md |

---

## 📞 反馈与贡献

如果您发现文档有遗漏、错误或改进建议：

1. **提交Issue**: 描述问题和建议
2. **补充文档**: 直接提交PR更新文档
3. **知识分享**: 在团队内分享使用经验

---

**维护状态**: ✅ 活跃维护
**最后更新**: 2025-11-08
**下次审查**: 根据项目重大更新同步更新文档

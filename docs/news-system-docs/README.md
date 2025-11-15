# 新闻系统文档目录

## 📋 目录用途

此目录存放**东方烟草报 & 新华财经风格改写系统**相关文档，包括：
- 📖 用户操作指南与工作流程
- 🏗️ 开发计划与项目规格
- 📊 质量分析与性能报告
- 🎨 风格样本与训练素材

## 📚 文档索引

### 用户指南
- [使用指南](USAGE_GUIDE.md) - 系统基础操作说明
- [一键工作流操作手册](ONE_CLICK_WORKFLOW.md) - 快速改写流程
- [简易入口汇总](SIMPLE_ENTRY.md) - 各种使用方式汇总
- [Claude控制台版流程](CLAUDE_CONSOLE_GUIDE.md) - Claude Code环境使用

### 项目管理
- [K2项目规格](PROJECT_K2_SPECIFICATION.md) - 核心功能需求定义
- [阶段1完成报告](PHASE1_COMPLETION_REPORT.md) - 基础功能交付总结
- [完整开发计划](DEVELOPMENT_PLAN_FINAL.md) - 长期迭代路线图
- [第一阶段README](README_PHASE1.md) - 早期版本文档

### 质量分析
- [质量差距分析](QUALITY_GAP_ANALYSIS_REPORT.md) - 输出质量评估
- [风格优化报告](STYLE_OPTIMIZATION_REPORT.md) - 烟草报与新华财经风格调优
- [前端交付报告](FRONTEND_DELIVERY_REPORT.md) - Streamlit界面开发总结

### 训练素材与样本
- [补充样本.txt](补充样本.txt) - 额外训练文本
- [刊物训练改写系统.txt](刊物训练改写系统.txt) - 系统训练说明
- [新华财经样稿.txt](新华财经样稿.txt) - 新华财经风格参考
- [东方烟草报.docx/.pdf](东方烟草报.docx) - 东方烟草报样本文档
- [新华财经.docx/.pdf](新华财经.docx) - 新华财经样本文档

---

**系统信息**：
- **端口**：8081 (API) / 8501 (Streamlit)
- **开发进度**：约90%（东方烟草报主流程可用）
- **主要入口**：`news_api_main.py`, `streamlit_app.py`
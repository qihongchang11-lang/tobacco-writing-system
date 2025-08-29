# 中国烟草报风格改写流水线系统

基于Claude多Agent架构的中国烟草报风格公文写作改写应用，通过学习行业写作风格，将初稿改写为符合中国烟草报标准的专业稿件。

## 🏗️ 系统架构

```
原稿输入 → 体裁判定 → 结构重组 → 风格改写 → 事实校对 → 版式导出 → 质量评估
```

## 📁 项目结构

```
tobacco-writing-pipeline/
├── agents/                 # 6个专业Agent
│   ├── genre_classifier.py      # 体裁识别Agent
│   ├── structure_reorganizer.py # 结构重组Agent
│   ├── style_rewriter.py        # 风格改写Agent
│   ├── fact_checker.py          # 事实校对Agent
│   ├── format_exporter.py       # 版式导出Agent
│   └── quality_evaluator.py     # 质量评估Agent
├── knowledge_base/         # 知识库系统
│   ├── style_cards/        # 风格卡库
│   ├── sentence_patterns/  # 句式库
│   └── terminology/        # 术语口径库
├── templates/              # 文档模板
├── web_interface/          # Web界面
├── utils/                  # 工具函数
├── data/                   # 数据存储
└── tests/                  # 测试代码
```

## 🚀 快速开始

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入Claude API密钥
```

3. **启动Web界面**
```bash
streamlit run web_interface/app.py
```

## 🔧 核心功能

- **智能体裁识别**: 自动识别新闻、评论、通讯等文章类型
- **结构化重组**: 按烟草报标准重新组织文章结构
- **风格化改写**: 基于大量样本学习的语言风格转换
- **专业校对**: 术语一致性和事实准确性检查
- **标准化导出**: 生成符合格式要求的DOCX文档
- **质量评估**: 多维度评分和改进建议

## 📚 知识库

系统内置三大知识库：
- **风格卡**: 不同体裁的写作特征
- **句式库**: 常用表达和转换模式  
- **术语库**: 行业标准用词规范

## 🔄 持续优化

- 回归测试框架
- A/B测试对比
- 人工反馈循环
- 增量学习机制

## 📊 质量指标

- 标题导语完整性
- 数据事实准确性
- 语言风格一致性
- 格式规范符合度
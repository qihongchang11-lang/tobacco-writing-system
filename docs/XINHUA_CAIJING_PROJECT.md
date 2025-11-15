# 新华财经风格改写系统 - 核心方案

## 🎯 项目目标
将**中烟工业企业文稿**（特别是浙江中烟）改写为**新华财经风格的高质量报道**，达到发表投稿标准。

## 📋 技术方案（最终选型）
**基于tobacco-writing-pipeline架构的最小侵入式改造**
- 复用tobacco 95%代码，新增3个模块，修改2处API调用
- 开发周期：2-3天
- 核心优势：不重复造轮子，快速上线

## 🔧 技术架构

```
tobacco-writing-pipeline/  # 复用现有项目
├── core/                  # 新增3个核心模块
│   ├── xhf_sample_retriever.py    # 新华财经样本检索器
│   ├── xhf_style_injector.py      # 风格注入器（原句原型）
│   └── xhf_quality_checker.py     # 财经发表体检器
├── data/
│   ├── xhf_samples/              # 新华财经样稿库
│   ├── xhf_prototypes/           # 提取的原句原型
│   └── xhf_style_guide.yaml     # 风格指导配置
├── scripts/
│   └── xhf_distill.py           # 样本蒸馏脚本
└── api_main.py                   # 仅2处改动
```

## 🚀 核心技术

### 1. 同域蒸馏（离线）
- 从新华财经样本提取原句原型
- 生成可配置的风格指导规则
- 建立样本检索索引

### 2. Few-shot风格注入（在线）
- 复用tobacco的检索引擎
- 注入新华财经原句原型到prompt
- 保持tobacco的约束解码保护

### 3. 财经发表体检（后处理）
- 官腔密度检查（≤0.1%）
- 财经术语覆盖（≥95%）
- 导语长度控制（60-90字）
- 归因规范验证

## 📊 验收标准
- 端到端响应：≤15秒
- 一次通过率：≥70%
- 最终通过率：≥90%（含纠偏）
- A/B盲评"更像新华财经"：≥70%

## 🔄 API改动点
```python
# api_main.py 仅2处改动

# 改动1：prompt增强
style_enhancement = inject_xinhua_style(request.text, doc_type)
enhanced_prompt = original_prompt + style_enhancement

# 改动2：质量体检
final_result = check_and_refine(title, lead, body)
```

## 📁 样稿要求
- 数量：15-20篇新华财经报道中烟工业的样稿
- 类型：企业新闻、财务业绩、行业分析、社会责任等
- 来源：新华财经正式发表的文章

## ⏰ 开发时间线
- Day 1：样稿处理+蒸馏脚本
- Day 2：核心3模块开发
- Day 3：API集成+测试验证

## 💡 关键优势
- ✅ 技术风险低（tobacco架构已验证）
- ✅ 开发速度快（最小改动）
- ✅ 质量有保障（原句原型few-shot）
- ✅ 易于维护（模块化设计）

**最后更新**: 2025-11-08
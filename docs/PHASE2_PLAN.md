# Phase 2 开发规划 - 1周极简MVP方案

> **创建时间**: 2025-11-07  
> **目标**: 1周内上线可用系统（个人使用、质量优先、界面精美）  
> **总工时**: 约13.5小时  
> **核心原则**: 复用Phase 1成果 + 快速迭代 + 体验优先

---

## 🎯 项目目标

构建一个**看得见改写效果、界面好看、体验顺滑**的个人改写系统：

- ✅ **改写质量**: 从0.92提升到0.94+
- ✅ **用户界面**: 专业美观的Web界面
- ✅ **操作体验**: 3步完成（粘贴→改写→下载）
- ✅ **启动简单**: 双击脚本即可使用
- ✅ **响应速度**: <15秒完成改写

---

## 📋 核心设计理念

### 1. 就地取材策略（GPT-5建议）
**不重复造轮子，最大化复用现有能力**：

已有资源：
- ✅ `ConstraintDecoder`（实体锁定/白名单/新数字检测）
- ✅ `BM25KnowledgeRetriever`（知识检索 + LRU缓存）
- ✅ DeepSeek API集成（已验证通过）

只需补充：
- ➕ 后处理模块（标题数字前置、导语裁剪）
- ➕ Streamlit前端（快速可视化）
- ➕ 启动脚本（一键运行）

### 2. MVP功能取舍

#### ✅ 必做（影响第一印象）
- 白名单实体锁定
- 新数字检查
- BM25缓存展示
- 后处理规范化
- Streamlit美观界面
- 样本分析（5-10篇）

#### ❌ 延后到Phase 2.5
- 批量处理功能
- React复杂前端
- 导语要素验证器
- 质量评估器扩展
- 历史记录管理
- 用户权限系统

---

## 📅 1周开发计划

### Day 1: 后端质量增强（3.5小时）

#### 1.1 创建后处理模块 `postprocess.py`（1小时）

**文件位置**: `core/postprocess.py`

**核心功能**:
```python
class RewritePostProcessor:
    def process(self, title: str, lead: str, body: str, column_id: str):
        """统一后处理入口"""
        return {
            'title': self._process_title(title, column_id),
            'lead': self._process_lead(lead),
            'body': self._process_body(body)
        }
```

**处理规则**:
- **标题**: 去感叹号、数字前置（经济类）、长度控制8-15字
- **导语**: 字数控制40-80字、标点规范化
- **正文**: 去空段落、标点规范化

#### 1.2 更新 `api_main.py` 集成后处理（1小时）

**关键改动**:
```python
from core.postprocess import RewritePostProcessor

# 初始化
postprocessor = RewritePostProcessor()

# 在改写后添加后处理步骤
parsed = parse_rewrite_result(result_text)
processed = postprocessor.process(
    parsed['title'], 
    parsed['lead'], 
    parsed['body_text'],
    column_info['id']
)
```

#### 1.3 样本快速分析（1小时）

**目标**: 收集5-10篇东方烟草报文章，快速提取关键模式

**采样策略**:
```
栏目分布：
├── 要闻 (3篇) - 会议、活动类
├── 经济运行 (3篇) - 月度、季度数据
├── 政策解读 (2篇) - 通知、办法类
└── 案例 (2篇) - 典型企业、先进个人
```

**分析重点**:
- 标题句式模式（数字位置、动词选择）
- 导语常用结构（时间+地点+主体+动作+结果）
- 数据表述习惯（单位、小数点、同比用词）
- 高频专业表述（"推进"vs"提升"、"成效"vs"成绩"）

**输出**: 更新提示词模板，补充到 `api_main.py` 的prompt中

#### 1.4 补充API审计字段（30分钟）

**完善 audit 返回**:
```python
audit = {
    'entities_locked': [e['text'] for e in entities],
    'new_numbers_detected': audit_info.get('new_numbers', []),
    'evidence': [
        {'snippet': e['snippet'], 'score': e['score']} 
        for e in evidence
    ],
    'retries': retries,
    'needs_review': not is_valid,
    'leakage_detected': '{{' in restored_title  # 占位符泄漏
}
```

---

### Day 2-3: Streamlit前端开发（6小时）

#### 2.1 核心界面实现（4小时）

**文件位置**: `frontend/app.py`

**技术栈**:
- Streamlit (快速Web框架)
- 自定义CSS（渐变按钮、卡片布局）

**界面布局**:
```
┌──────────────────────────────────────────────────┐
│ 🍃 烟草报改写工作台（MVP）          [今日3篇][4.2⭐] │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌─ 📝 原文输入 ───┐  │  ┌─ ✨ 改写结果 ───────┐ │
│ │ [文本框]        │  │  │ 📌 标题             │ │
│ │                 │  │  │ 📄 导语             │ │
│ │ 栏目: [下拉框]  │  │  │ 📝 正文             │ │
│ │ ☑ 严格模式      │  │  │ ⭐ 质量评分         │ │
│ │ [🚀 开始改写]   │  │  │ 🔍 审计信息         │ │
│ │                 │  │  │ [📥 下载] [📋 复制] │ │
│ └─────────────────┘  │  └─────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

**核心代码结构**:
```python
import streamlit as st
import requests

# 页面配置
st.set_page_config(page_title="🍃 烟草报改写工作台", layout="wide")

# 自定义CSS
st.markdown("""<style>
  .stButton>button {
    background: linear-gradient(135deg,#10b981,#059669);
    color:#fff; border-radius:10px; padding:10px 18px;
  }
  .card {
    background:#fff; border:1px solid #eef2f7;
    border-radius:12px; padding:16px; margin-bottom:12px;
    box-shadow:0 2px 8px rgba(16,24,40,.04);
  }
</style>""", unsafe_allow_html=True)

# 左右分栏布局
left, right = st.columns([1,1])

with left:
    # 输入区域
    text = st.text_area("📝 原文输入", height=360)
    column = st.selectbox("📚 栏目", options)
    strict = st.checkbox("严格模式", value=True)
    if st.button("🚀 开始改写"):
        # 调用API
        result = requests.post("http://localhost:8081/rewrite", ...)
        st.session_state['result'] = result.json()

with right:
    # 结果展示
    if 'result' in st.session_state:
        # 标题、导语、正文展示
        # 质量评分展示
        # 审计信息展示
        # 下载按钮
```

#### 2.2 功能优化（2小时）

**增强体验**:
1. **实时字数统计**: `st.caption(f"当前字数：{len(text)} 字")`
2. **栏目智能提示**: 显示图标 + 中文名称
3. **证据卡片展示**: 显示BM25检索的3条相关证据
4. **错误友好提示**: API失败时显示降级结果
5. **复制功能**: 一键复制改写结果到剪贴板

**响应结构完整展示**:
- 标题、导语、正文（卡片布局）
- 质量评分（总体/事实/风格）
- 审计信息（entities_locked、new_numbers、evidence）
- 元数据（模型、延迟、重试次数）

---

### Day 4: 联调测试（2小时）

#### 4.1 测试用例扩展（1小时）

**扩展测试集**:
```bash
tests/
├── smoke_economic.json      # 经济数据类
├── smoke_meeting.json       # 会议报道类
├── smoke_policy.json        # 政策解读类
├── smoke_personnel.json     # 人事任免类
└── smoke_activity.json      # 活动报道类
```

**质量基准**:
- 事实一致性 ≥ 0.95
- 风格一致性 ≥ 0.88
- 总体评分 ≥ 0.90
- 响应时间 < 15秒

#### 4.2 端到端验证（1小时）

**验证清单**:
- ✅ 启动脚本运行正常
- ✅ 前后端通信无误
- ✅ 5个测试用例全部通过
- ✅ 审计字段完整展示
- ✅ 下载/复制功能正常
- ✅ 缓存命中率 > 50%

---

### Day 5: 打包部署（2小时）

#### 5.1 一键启动脚本（1小时）

**文件位置**: `run_system.bat`

```bat
@echo off
title 烟草报改写系统

echo ========================================
echo 🍃 烟草报改写系统 v1.0 MVP
echo ========================================
echo.

cd /d %USERPROFILE%\tobacco-writing-pipeline

echo [1/3] 🔍 检查依赖...
.venv\Scripts\python.exe -c "import streamlit" 2>nul
if errorlevel 1 (
    echo    安装 Streamlit...
    .venv\Scripts\pip install streamlit -q
)

echo [2/3] 🚀 启动后端服务...
start "API Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn api_main:app --host 0.0.0.0 --port 8081 --log-level info"

timeout /t 3 >nul

echo [3/3] 🎨 启动前端界面...
start "Web Frontend" cmd /k ".venv\Scripts\streamlit run frontend\app.py --server.port 3000"

timeout /t 5 >nul

echo.
echo ✅ 系统启动完成！
echo 📱 访问地址: http://localhost:3000
echo.
echo 提示: 关闭此窗口不会停止服务
echo       需要手动关闭后端和前端窗口
echo.

start http://localhost:3000

pause
```

#### 5.2 用户文档（1小时）

**文件位置**: `docs/USER_GUIDE.md`

**内容**:
```markdown
# 烟草报改写系统使用指南

## 快速开始

1. **启动系统**
   - 双击 `run_system.bat`
   - 等待浏览器自动打开（约5秒）

2. **改写文章**
   - 在左侧粘贴原文
   - 选择栏目类型（可选）
   - 勾选"严格模式"（推荐）
   - 点击"🚀 开始改写"

3. **查看结果**
   - 右侧显示改写后的标题、导语、正文
   - 查看质量评分和审计信息
   - 点击"📥 下载"或"📋 复制"

## 功能说明

### 栏目类型
- **经济运行**: 数据报告、统计分析
- **要闻**: 会议报道、活动新闻
- **政策解读**: 通知公告、政策文件
- **案例**: 典型企业、先进个人

### 严格模式
- 开启后使用更保守的改写策略
- 降低创造性，提高准确性
- 推荐日常使用

### 质量指标
- **事实一致性**: 数字、日期、机构名准确性
- **风格一致性**: 符合烟草报文体程度
- **总体评分**: 综合质量评价

### 审计信息
- **entities_locked**: 保护的关键实体
- **new_numbers_detected**: 是否引入新数字
- **evidence**: 参考的知识证据
- **needs_review**: 是否需要人工复审

## 注意事项

1. **输入限制**
   - 单篇文章不超过2000字
   - 确保原文包含完整信息

2. **质量保证**
   - 系统自动保护数字、日期、机构名
   - 建议改写后人工复审一次

3. **常见问题**
   - 改写时间较长：正常现象，约10-15秒
   - 质量评分偏低：尝试调整栏目类型或开启严格模式

## 技术支持

- 项目地址: `C:\Users\qhc13\tobacco-writing-pipeline`
- 配置文件: `.env`
- 日志位置: `logs/api.err`
```

---

## 📊 技术架构

### 后端（FastAPI）
```
tobacco-writing-pipeline/
├── api_main.py              # 主API服务
├── core/
│   ├── constraint_decoder.py   # 实体约束解码器
│   ├── knowledge_retriever.py  # BM25知识检索
│   └── postprocess.py          # 改写后处理 [新增]
├── config/
│   └── column_rules.yaml    # 栏目规则配置
├── data/
│   ├── knowledge/           # 知识库
│   └── test_datasets/       # 测试数据集
└── .env                     # 环境配置
```

### 前端（Streamlit）
```
frontend/
└── app.py                   # Web界面 [新增]
```

### 部署脚本
```
run_system.bat               # 一键启动 [新增]
```

---

## 🎯 质量目标

### 改写质量提升
| 指标 | Phase 1 | Phase 2 目标 | 提升方式 |
|------|---------|-------------|---------|
| 事实一致性 | 1.0 | 1.0 | 保持（已完美） |
| 风格一致性 | 0.9 | 0.94 | 样本分析+后处理 |
| 合规性 | 0.95 | 0.96 | 白名单扩充 |
| **总体评分** | **0.92** | **0.94+** | 综合优化 |

### 性能指标
- **响应时间**: < 15秒
- **BM25缓存命中率**: > 50%
- **内存占用**: < 500MB
- **启动时间**: < 10秒

---

## 🔄 Phase 2.5 规划（未来扩展）

当前MVP完成后，可选择性添加以下功能：

### 高级功能
- [ ] 批量处理（上传多个文件）
- [ ] 历史记录管理（SQLite存储）
- [ ] 改写结果对比（原文vs改写）
- [ ] 自定义模板系统
- [ ] 质量趋势分析

### 技术升级
- [ ] React前端（替代Streamlit）
- [ ] Docker容器化部署
- [ ] RESTful API文档（OpenAPI）
- [ ] 多模型支持（Claude + DeepSeek）

### 用户体验
- [ ] 快捷键支持（Ctrl+Enter改写）
- [ ] 实时改写预览
- [ ] 拖拽上传文件
- [ ] 移动端适配

---

## 📝 开发检查清单

### Day 1
- [ ] 创建 `core/postprocess.py`
- [ ] 实现标题/导语/正文后处理
- [ ] 更新 `api_main.py` 集成后处理
- [ ] 收集5-10篇样本文章
- [ ] 分析样本提取关键模式
- [ ] 更新提示词模板
- [ ] 补充API审计字段

### Day 2-3
- [ ] 创建 `frontend/app.py`
- [ ] 实现两栏布局
- [ ] 添加自定义CSS样式
- [ ] 实现输入区（文本框+选项）
- [ ] 实现结果展示区（卡片布局）
- [ ] 添加质量评分展示
- [ ] 添加审计信息展示
- [ ] 实现下载/复制功能
- [ ] 添加实时字数统计
- [ ] 优化证据卡片展示

### Day 4
- [ ] 创建5个测试用例
- [ ] 执行端到端测试
- [ ] 验证质量基准达标
- [ ] 测试缓存功能
- [ ] 压力测试（响应时间）

### Day 5
- [ ] 创建 `run_system.bat`
- [ ] 测试一键启动
- [ ] 编写用户文档
- [ ] 创建故障排查指南
- [ ] 准备演示脚本

---

## 🎉 预期成果

**1周后你将拥有**：

✅ **专业改写质量**
- 事实一致性 100%（数字/日期/机构名绝对准确）
- 风格一致性 94%+（贴近东方烟草报标准）
- 后处理规范化（标题数字前置、导语字数达标）

✅ **美观用户界面**
- Streamlit专业主题
- 卡片式布局设计
- 渐变色按钮和动画
- 响应式适配

✅ **流畅操作体验**
- 3步完成改写（粘贴→改写→下载）
- 实时反馈（字数统计、进度提示）
- 智能缓存（重复文本秒回）
- 一键启动（双击脚本）

✅ **完整审计信息**
- 锁定实体可视化
- 新数字检测展示
- 知识证据溯源
- 质量评分详情

✅ **生产就绪**
- 可靠的降级策略
- 完善的错误处理
- 清晰的用户文档
- 简单的部署方式

---

## 📞 技术参考

### 关键依赖
```
Python 3.12+
FastAPI
Streamlit
DeepSeek API
```

### 重要配置
- **API端口**: 8081
- **前端端口**: 3000
- **DeepSeek模型**: deepseek-chat
- **温度参数**: 0.3（严格模式0.2）

### 文档链接
- [Phase 1 总结](./PROJECT_SUMMARY.md)
- [项目概述](./PROJECT_BRIEF.md)
- [运维手册](./RUNBOOK.md)

---

*📅 文档创建时间: 2025-11-07*  
*🎯 预计完成时间: 2025-11-14*  
*⏱️ 总开发工时: 约13.5小时*

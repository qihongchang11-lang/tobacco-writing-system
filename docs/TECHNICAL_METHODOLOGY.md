# 烟草报风格改写系统 - 技术方案与方法论

## 📚 文档说明

**目的**: 总结项目的技术方案设计、核心方法论和最佳实践，作为知识沉淀和后续类似项目的参考模板
**适用场景**: LLM驱动的风格迁移、Few-shot学习、文本改写类项目
**创建时间**: 2025-11-08
**文档类型**: 技术知识库

---

## 🎓 核心方法论

### 1. 学习驱动的文本风格迁移框架

#### 1.1 问题定义

**输入**:
- 原始文本（任意风格）
- 目标风格标签（如"要闻"、"案例"）

**输出**:
- 符合目标风格的改写文本
- 保持原文事实准确性

**核心挑战**:
1. 风格特征难以用规则精确定义
2. 不同栏目风格差异大
3. 必须保护关键事实信息（数字、日期、机构名）

#### 1.2 方法论：Few-shot Learning + 混合检索

```
┌─────────────────────────────────────────────┐
│              用户输入原文                    │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 1: 体裁分类（识别目标栏目）           │
│   - 关键词匹配                               │
│   - 返回栏目ID和置信度                       │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 2: 约束提取（保护关键信息）           │
│   - 提取数字、日期、机构名                   │
│   - 替换为占位符 [NUM_0], [ORG_0] 等        │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 3: 智能样本检索（找相似文章）         │
│   - BM25词法检索 (40%)                       │
│   - 语义相似度检索 (60%)                     │
│   - 返回Top-3样本                            │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 4: Few-shot改写（风格学习）           │
│   - 构建提示词：示例 + 规范 + 原文           │
│   - LLM生成改写                              │
│   - 包含标题、导语、正文                     │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 5: 后处理（恢复原始信息）             │
│   - 占位符替换回原始实体                     │
│   - 格式化输出                               │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│   Step 6: 质量评估（多维度打分）             │
│   - 事实一致性检查                           │
│   - 风格一致性评估                           │
│   - 合规性验证                               │
└───────────────┬─────────────────────────────┘
                │
                ▼
         返回改写结果
```

#### 1.3 关键创新点

**创新1: 混合检索策略**
- **问题**: 单一检索方法效果不佳
  - 纯BM25：语义理解差
  - 纯语义：忽略关键词
- **解决方案**: 加权混合
  ```python
  hybrid_score = 0.4 * bm25_score + 0.6 * semantic_score
  ```
- **效果**: 既保证关键词匹配，又考虑语义相似

**创新2: 约束解码保护机制**
- **问题**: LLM容易改变/幻觉数字
- **解决方案**: 占位符替换
  ```python
  原文: "销售45.2万箱，增长8.5%"
  → 处理: "销售[NUM_0]，增长[NUM_1]"
  → 改写后: 恢复为"销售45.2万箱，增长8.5%"
  ```
- **效果**: 100%保护关键数字和实体

**创新3: 分栏目风格指导**
- **问题**: 不同栏目风格差异大，统一提示词效果差
- **解决方案**: 动态加载栏目专用规范
  ```python
  # 要闻栏目
  "标题：主体+动作/成果，官方庄重"

  # 经济运行栏目
  "标题：数字前置突出亮点，如'45.2万箱：某地卷烟销售创新高'"
  ```
- **效果**: 改写风格精准匹配目标栏目

---

### 2. 系统架构设计

#### 2.1 整体架构

```
┌────────────────────────────────────────────────────┐
│                   用户层                            │
│  ┌──────────────┐          ┌──────────────┐       │
│  │ Web前端界面  │          │  RESTful API │       │
│  │ (Streamlit)  │          │  (直接调用)  │       │
│  └──────┬───────┘          └──────┬───────┘       │
└─────────┼──────────────────────────┼──────────────┘
          │                          │
          └──────────┬───────────────┘
                     │ HTTP Request
                     ▼
┌────────────────────────────────────────────────────┐
│                  API网关层                          │
│              FastAPI Backend                        │
│  ┌────────────────────────────────────────┐       │
│  │  /rewrite  -  改写接口                  │       │
│  │  /health   -  健康检查                  │       │
│  │  /docs     -  API文档                   │       │
│  └────────────────────────────────────────┘       │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│                  核心处理层                         │
│  ┌──────────────────────────────────────────┐     │
│  │  体裁分类器  →  约束解码器  →  检索器    │     │
│  │      ↓              ↓             ↓       │     │
│  │  Few-shot改写  →  后处理  →  质量评估   │     │
│  └──────────────────────────────────────────┘     │
└────────────────────┬───────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ 样本库   │  │ LLM服务  │  │ 向量库   │
│ (JSON)   │  │(DeepSeek)│  │(Embeddings)│
└──────────┘  └──────────┘  └──────────┘
   数据层        外部服务      缓存层
```

#### 2.2 模块化设计原则

**原则1: 单一职责**
- 每个Agent只负责一个功能
- `GenreClassifierAgent`: 体裁分类
- `FewShotRewriter`: 改写生成
- `ConstraintDecoder`: 约束保护

**原则2: 依赖注入**
```python
class FewShotRewriter:
    def __init__(self, retriever=None):
        self.retriever = retriever  # 注入检索器

# 使用时
retriever = IntelligentRetriever(samples_dir="...")
rewriter = FewShotRewriter(retriever=retriever)
```

**原则3: 配置外置**
```python
# ❌ 硬编码
timeout = 30

# ✅ 环境变量
timeout = int(os.getenv("REQUEST_TIMEOUT", "150"))
```

---

### 3. 核心技术组件

#### 3.1 Few-shot学习提示词工程

**设计思路**:
1. **示例展示**: 让LLM看到优秀范例
2. **特征分析**: 明确指出风格特征
3. **规范约束**: 给出明确的写作规范
4. **任务描述**: 清晰说明改写要求

**提示词模板结构**:

```python
prompt = f"""
【严格模式约束】（可选）
⚠️ CRITICAL: 绝对不能修改或删除原文中的任何数字、日期、机构名称

【风格学习示例】
以下是{target_column}栏目的优秀范例，请仔细学习其写作风格和结构特征：

示例1：
标题：{sample1_title}
导语：{sample1_lead}
正文片段：{sample1_body[:200]}...
风格特征：{describe_features(sample1)}

示例2：
...

【{target_column}栏目写作规范】
{get_column_guidance(target_column)}
- 标题：{title_guidance}
- 导语：{lead_guidance}
- 正文：{body_guidance}
- 语言：{language_guidance}

【改写任务】
请基于上述示例学习的风格特征，将以下文章改写为符合{target_column}栏目标准的稿件：

原文：
{input_text}

【输出要求】
严格按照以下格式输出，不要添加其他内容：

===标题===
[学习示例风格后的标题]

===导语===
[40-80字的导语]

===正文===
[改写后的正文内容]

===风格说明===
[说明从示例中学到的关键风格特征及应用]
"""
```

**关键点**:
- 使用`===分隔符===`确保结构化输出易解析
- 明确字数要求（导语40-80字）
- 要求输出风格说明，提升可解释性

#### 3.2 混合检索算法实现

**算法流程**:

```python
def retrieve_similar_samples(query_text, column_id, top_k=3):
    # 1. 过滤栏目
    candidate_samples = filter_by_column(column_id)

    # 2. 文本预处理
    query_tokens = jieba.cut(query_text)  # 中文分词

    # 3. BM25检索
    bm25_scores = bm25.get_scores(query_tokens)

    # 4. 语义检索
    query_embedding = sentence_bert.encode(query_text)
    sample_embeddings = [s['embedding'] for s in candidate_samples]
    semantic_scores = cosine_similarity(query_embedding, sample_embeddings)

    # 5. 归一化（重要！）
    bm25_scores_norm = normalize(bm25_scores)
    semantic_scores_norm = normalize(semantic_scores)

    # 6. 加权融合
    hybrid_scores = (
        BM25_WEIGHT * bm25_scores_norm +
        SEMANTIC_WEIGHT * semantic_scores_norm
    )

    # 7. 排序返回Top-K
    top_indices = np.argsort(hybrid_scores)[-top_k:]
    return [candidate_samples[i] for i in top_indices]
```

**技术细节**:

1. **归一化必要性**
   - 问题: BM25分数范围[0, ∞)，语义分数范围[-1, 1]
   - 解决: Min-Max归一化到[0, 1]
   ```python
   def normalize(scores):
       min_s, max_s = min(scores), max(scores)
       return [(s - min_s) / (max_s - min_s + 1e-8) for s in scores]
   ```

2. **权重调优策略**
   - 初始: BM25(50%) + 语义(50%)
   - 观察: 关键词匹配不足
   - 调整: BM25(40%) + 语义(60%)
   - 效果: 提升语义理解，保留关键词

3. **性能优化**
   - 预计算样本embeddings（启动时）
   - 缓存BM25索引
   - 避免重复计算

#### 3.3 约束解码器设计

**核心思想**: 占位符替换保护关键信息

**实现步骤**:

```python
class ConstraintDecoder:
    def extract_entities(self, text):
        """提取需要保护的实体"""
        entities = {
            'dates': [],      # 日期：2025年11月
            'numbers': [],    # 数字：45.2万箱、8.5%
            'orgs': []        # 机构：山东省烟草专卖局
        }

        # 正则提取日期
        date_pattern = r'\d{4}年\d{1,2}月|\d{1,2}月\d{1,2}日'
        entities['dates'] = re.findall(date_pattern, text)

        # 正则提取数字
        number_pattern = r'\d+\.?\d*(?:万|亿|千)?(?:箱|元|吨|%)'
        entities['numbers'] = re.findall(number_pattern, text)

        # 机构名识别（基于白名单）
        for org in org_whitelist:
            if org in text:
                entities['orgs'].append(org)

        return entities

    def to_placeholders(self, text, entities):
        """替换为占位符"""
        placeholder_map = {}

        for i, num in enumerate(entities['numbers']):
            placeholder = f"[NUM_{i}]"
            text = text.replace(num, placeholder, 1)
            placeholder_map[placeholder] = num

        # 同理处理日期和机构
        ...

        return text, placeholder_map

    def restore_entities(self, text, placeholder_map):
        """恢复原始实体"""
        for placeholder, entity in placeholder_map.items():
            text = text.replace(placeholder, entity)
        return text
```

**关键细节**:

1. **正则表达式设计**
   - 数字：`\d+\.?\d*(?:万|亿|千)?(?:箱|元|吨|%)`
   - 支持：45.2万箱、8.5%、123.6亿元

2. **机构名白名单**
   ```python
   org_whitelist = [
       "国家烟草专卖局",
       "中国烟草总公司",
       "各省级烟草专卖局",
       ...
   ]
   ```

3. **替换策略**
   - 使用`replace(old, new, 1)`一次替换一个
   - 避免重复替换（如"8.5%"和"5%"）

#### 3.4 超时配置最佳实践

**问题背景**:
- LLM生成耗时长（15-20秒）
- 网络波动可能更慢
- 默认超时（30秒）不够用

**解决方案**: 分层超时配置

**第一层: 前端请求超时**
```python
# frontend/app.py
response = requests.post(
    url,
    json=payload,
    timeout=(connect_timeout, read_timeout)  # 元组格式
)

# 推荐配置
timeout=(10, 150)  # 连接10秒，读取150秒
```

**第二层: 后端HTTP客户端超时**
```python
# agents/few_shot_rewriter.py
import httpx

timeout = httpx.Timeout(
    connect=10.0,   # 连接超时
    read=120.0,     # 读取超时（LLM生成时间）
    write=120.0,    # 写入超时
    pool=5.0        # 连接池超时
)

http_client = httpx.Client(timeout=timeout)
openai_client = OpenAI(http_client=http_client)
```

**配置原则**:
1. **前端 > 后端**: 前端超时要大于后端
   - 前端150秒 > 后端120秒
   - 确保后端有时间完成处理

2. **预留缓冲**:
   - 平均处理时间20秒
   - 配置120秒超时
   - 6倍缓冲应对波动

3. **分阶段超时**:
   - 连接: 10秒（网络建立）
   - 读取: 120秒（等待响应）
   - 写入: 120秒（发送大数据）

---

### 4. 前端开发最佳实践

#### 4.1 Streamlit UI设计

**原则1: 响应式布局**
```python
# 使用列布局
col1, col2 = st.columns([1, 1])  # 等宽两列

with col1:
    st.text_area("输入")

with col2:
    st.markdown("输出")
```

**原则2: 自定义CSS覆盖**
```python
st.markdown("""
<style>
    .result-container {
        border: 2px solid #E5E5E5;
        padding: 1.5rem;
        word-wrap: break-word;      /* 自动换行 */
        white-space: pre-wrap;       /* 保留格式 */
    }
</style>
""", unsafe_allow_html=True)
```

**原则3: Session State管理**
```python
# 存储结果，避免重新请求
if 'rewrite_result' not in st.session_state:
    st.session_state['rewrite_result'] = None

# 使用
st.session_state['rewrite_result'] = api_result
```

#### 4.2 长文本显示解决方案

**问题**: `st.write()`会截断长文本

**解决方案**: 使用HTML + CSS

```python
# ❌ 会截断
st.write(long_title)

# ✅ 完整显示
st.markdown(
    f'<div style="word-wrap: break-word; white-space: pre-wrap;">{long_title}</div>',
    unsafe_allow_html=True
)
```

**关键CSS属性**:
- `word-wrap: break-word`: 单词内断行
- `white-space: pre-wrap`: 保留空格和换行
- `overflow-wrap: break-word`: 备用属性

---

### 5. API设计规范

#### 5.1 RESTful接口设计

**健康检查端点**:
```python
GET /health
Response: {
    "ok": true,
    "version": "2.0.0",
    "components": {
        "decoder": true,
        "retriever": true,
        "rewriter": true
    },
    "learning_stats": {
        "total_articles": 34,
        "vocab_size": 1294
    }
}
```

**改写接口**:
```python
POST /rewrite
Request: {
    "text": "原始文本",
    "genres": ["会议报道", "行业新闻"],  # 体裁列表
    "strict_mode": false                  # 严格模式
}

Response: {
    "title": "改写后的标题",
    "lead": "改写后的导语",
    "body": {
        "text": "改写后的正文",
        "outline": ["背景", "举措", "成效"]
    },
    "column": {
        "id": "news_general",
        "name": "要闻",
        "route_confidence": 0.9
    },
    "scores": {
        "overall": 1.0,
        "factual_consistency": 1.0,
        "style_consistency": 1.0,
        "compliance": 0.95
    },
    "audit": {
        "entities_locked": {
            "numbers": ["45.2万箱", "8.5%"],
            "orgs": ["山东省烟草专卖局"]
        },
        "needs_review": false,
        "learning_mode": true
    },
    "meta": {
        "latency_ms": 21245,
        "model": "deepseek-chat",
        "pipeline_version": "learning-v2.0",
        "learning_stats": {
            "samples_used": 3,
            "max_similarity": 0.87
        }
    }
}
```

#### 5.2 错误处理规范

**HTTP状态码使用**:
- `200 OK`: 成功
- `400 Bad Request`: 参数错误
- `422 Unprocessable Entity`: 验证失败
- `500 Internal Server Error`: 服务器错误
- `503 Service Unavailable`: LLM服务不可用

**错误响应格式**:
```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "文本长度不能超过5000字",
        "details": {
            "field": "text",
            "current_length": 5234,
            "max_length": 5000
        }
    }
}
```

---

### 6. 数据管理与样本库设计

#### 6.1 样本文章格式

```json
{
    "id": "sample_001",
    "column_id": "news_general",
    "column_name": "要闻",
    "title": "山东省烟草专卖局召开营销工作会议",
    "lead": "近日，山东省烟草专卖局召开会议，研究部署全省卷烟营销工作。",
    "body": "会议强调，要深入贯彻落实行业高质量发展要求...",
    "metadata": {
        "publish_date": "2024-10-15",
        "author": "编辑部",
        "word_count": 580,
        "source": "东方烟草报"
    },
    "features": {
        "column_indicators": {
            "news_general": true,
            "economic_data": false,
            "policy_interpretation": false,
            "case_observation": false
        },
        "writing_style": {
            "opening_type": "time_indicator_start",
            "has_data": false,
            "tone": "formal"
        },
        "data_usage": {
            "data_density": 0,
            "numbers": []
        }
    }
}
```

#### 6.2 样本扩充策略

**方式1: 人工标注**
1. 从《东方烟草报》收集优质文章
2. 按栏目分类
3. 提取特征标注
4. 保存为JSON格式

**方式2: 半自动标注**
```python
def auto_extract_features(article_text):
    features = {
        'column_indicators': classify_column(article_text),
        'writing_style': analyze_style(article_text),
        'data_usage': extract_data_stats(article_text)
    }
    return features
```

**质量标准**:
- 每个栏目至少20篇样本
- 覆盖不同子类型（会议、活动、数据等）
- 文章质量高（官方发布）
- 标注准确率 > 95%

---

### 7. 测试与质量保证

#### 7.1 单元测试

**关键模块测试**:

```python
# 测试约束解码器
def test_constraint_decoder():
    decoder = ConstraintDecoder()
    text = "销售45.2万箱，增长8.5%"

    # 提取实体
    entities = decoder.extract_entities(text)
    assert len(entities['numbers']) == 2

    # 占位符替换
    encoded, mapping = decoder.to_placeholders(text, entities)
    assert "[NUM_0]" in encoded

    # 恢复
    decoded = decoder.restore_entities(encoded, mapping)
    assert decoded == text

# 测试检索器
def test_retriever():
    retriever = IntelligentRetriever()
    samples = retriever.retrieve_similar_samples(
        "召开会议部署工作",
        "news_general",
        top_k=3
    )
    assert len(samples) == 3
    assert samples[0]['column_id'] == "news_general"
```

#### 7.2 集成测试

**端到端测试**:
```python
def test_full_pipeline():
    # 1. 发送请求
    response = requests.post(
        "http://localhost:8081/rewrite",
        json={
            "text": test_article,
            "genres": ["会议报道"],
            "strict_mode": True
        }
    )

    # 2. 验证响应
    assert response.status_code == 200
    result = response.json()

    # 3. 验证结果
    assert result['title'] != ""
    assert len(result['lead']) >= 40
    assert result['scores']['overall'] > 0.8
```

#### 7.3 性能测试

**关键指标**:
1. **响应时间**: P95 < 30秒
2. **吞吐量**: > 10 req/min
3. **成功率**: > 99%

**压测脚本**:
```python
import concurrent.futures

def stress_test(num_requests=100):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(call_api, test_data) for _ in range(num_requests)]
        results = [f.result() for f in futures]

    success_rate = sum(1 for r in results if r['success']) / len(results)
    avg_latency = sum(r['latency'] for r in results) / len(results)

    print(f"成功率: {success_rate:.2%}")
    print(f"平均延迟: {avg_latency:.2f}ms")
```

---

## 🛠️ 开发工具链

### 1. Python环境管理

**推荐: venv虚拟环境**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Windows）
.venv\Scripts\activate

# 激活（Linux/Mac）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 冻结依赖
pip freeze > requirements.txt
```

### 2. 依赖管理

**核心依赖**:
```txt
# Web框架
fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.0

# LLM客户端
openai==1.3.0

# NLP
jieba==0.42.1
rank-bm25==0.2.2
sentence-transformers==2.2.2

# 工具库
requests==2.31.0
httpx==0.25.0
pydantic==2.5.0
```

### 3. 版本控制

**Git最佳实践**:
```bash
# 分支策略
main          # 生产版本
dev           # 开发版本
feature/*     # 功能分支

# 提交规范
feat: 新增Few-shot学习引擎
fix: 修复超时问题
docs: 更新技术文档
refactor: 重构检索模块
```

### 4. 日志管理

**配置示例**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用
logger.info("检索到3个样本")
logger.error(f"LLM调用失败: {error}")
```

---

## 📊 性能优化方法

### 1. 缓存策略

**场景1: 嵌入向量缓存**
```python
class IntelligentRetriever:
    def __init__(self):
        self._embedding_cache = {}

    def get_embedding(self, text):
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        embedding = self.model.encode(text)
        self._embedding_cache[text] = embedding
        return embedding
```

**场景2: 检索结果缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def retrieve_similar_samples(query_hash, column_id, top_k):
    # 使用query的hash作为缓存key
    ...
```

### 2. 异步处理

**并发检索**:
```python
import asyncio

async def parallel_retrieve(queries, retriever):
    tasks = [
        asyncio.create_task(retriever.retrieve(q))
        for q in queries
    ]
    return await asyncio.gather(*tasks)
```

### 3. 批处理优化

**批量编码**:
```python
# ❌ 逐个编码（慢）
embeddings = [model.encode(text) for text in texts]

# ✅ 批量编码（快）
embeddings = model.encode(texts, batch_size=32)
```

---

## 🔐 安全与合规

### 1. API密钥保护

```python
# ❌ 硬编码（危险）
api_key = "sk-abc123..."

# ✅ 环境变量
api_key = os.getenv("OPENAI_API_KEY")

# ✅ 配置文件（不提交到Git）
# .gitignore
.env
config/secrets.yaml
```

### 2. 输入验证

```python
from pydantic import BaseModel, Field, validator

class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000)
    genres: List[str] = Field(..., min_items=1, max_items=5)
    strict_mode: bool = False

    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("文本不能为空")
        return v.strip()
```

### 3. 敏感信息脱敏

```python
def mask_sensitive_info(text):
    # 脱敏手机号
    text = re.sub(r'1[3-9]\d{9}', '***********', text)

    # 脱敏身份证
    text = re.sub(r'\d{17}[\dXx]', '******************', text)

    return text
```

---

## 📈 监控与运维

### 1. 关键指标监控

**业务指标**:
- 改写成功率
- 平均处理时间
- 用户满意度评分

**技术指标**:
- API响应时间（P50, P95, P99）
- 错误率
- LLM调用成功率
- 服务可用性（SLA 99.9%）

### 2. 告警配置

```python
# 响应时间超过阈值
if latency_ms > 30000:
    send_alert("处理超时", f"耗时{latency_ms}ms")

# 错误率超过阈值
if error_rate > 0.05:  # 5%
    send_alert("错误率过高", f"当前{error_rate:.2%}")
```

### 3. 日志分析

**ELK Stack集成**:
```python
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# 结构化日志
logger.info("改写完成", extra={
    "latency_ms": 21245,
    "samples_used": 3,
    "column": "要闻",
    "user_id": "user123"
})
```

---

## 🌟 最佳实践总结

### 1. 代码质量

✅ **遵循PEP 8规范**
✅ **函数单一职责**
✅ **添加类型提示**
```python
def retrieve_samples(
    query: str,
    column_id: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    ...
```

### 2. 错误处理

✅ **具体的异常捕获**
```python
try:
    result = llm_call()
except requests.Timeout:
    logger.error("LLM调用超时")
except requests.RequestException as e:
    logger.error(f"网络请求失败: {e}")
except Exception as e:
    logger.error(f"未知错误: {e}")
```

### 3. 配置管理

✅ **环境变量优先**
✅ **分环境配置**
```python
# config.py
class Config:
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "150"))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

### 4. 文档规范

✅ **代码注释**
```python
def hybrid_retrieve(query: str) -> List[Sample]:
    """
    混合检索策略：BM25 + 语义相似度

    Args:
        query: 查询文本

    Returns:
        Top-K相似样本列表

    Example:
        >>> samples = hybrid_retrieve("召开会议")
        >>> len(samples)
        3
    """
```

✅ **API文档**
- 使用FastAPI自动生成：`/docs`
- 编写README说明启动步骤
- 维护CHANGELOG记录版本变更

---

## 🎯 项目复用指南

### 适用场景

本项目方法论可复用于：

1. **文本风格迁移**
   - 公文写作规范化
   - 新闻稿改写
   - 学术论文润色

2. **Few-shot学习应用**
   - 少样本分类
   - 文本生成
   - 代码生成

3. **LLM应用开发**
   - 提示词工程
   - RAG检索增强
   - Agent系统

### 快速启动新项目

**步骤1: 克隆模板**
```bash
git clone tobacco-writing-pipeline new-project
cd new-project
```

**步骤2: 修改核心组件**
1. 替换样本库（`knowledge_base/samples/`）
2. 调整栏目映射（`agents/few_shot_rewriter.py`）
3. 修改提示词模板（`_build_few_shot_prompt`）

**步骤3: 配置环境**
```bash
cp .env.example .env
# 编辑.env填入API密钥
```

**步骤4: 测试运行**
```bash
python -m pytest tests/
```

### 关键改动点

| 组件 | 文件路径 | 需要修改的内容 |
|------|---------|--------------|
| 样本库 | `knowledge_base/samples/*.json` | 替换为新领域样本 |
| 栏目定义 | `agents/few_shot_rewriter.py` | 修改`column_mapping`和`column_guidance` |
| 约束规则 | `core/constraint_decoder.py` | 调整实体提取正则和白名单 |
| API接口 | `api_main.py` | 修改请求/响应模型 |
| 前端界面 | `frontend/app.py` | 调整UI布局和文案 |

---

## 📚 参考资料

### 学术论文

1. **Few-shot Learning**
   - "Language Models are Few-Shot Learners" (GPT-3 Paper)
   - "Making Pre-trained Language Models Better Few-shot Learners"

2. **混合检索**
   - "Dense Passage Retrieval for Open-Domain Question Answering"
   - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"

### 开源项目

1. **LangChain**: LLM应用开发框架
2. **Haystack**: NLP检索框架
3. **Sentence-Transformers**: 句子嵌入库

### 工具文档

1. [FastAPI官方文档](https://fastapi.tiangolo.com/)
2. [Streamlit文档](https://docs.streamlit.io/)
3. [OpenAI API文档](https://platform.openai.com/docs/)

---

**文档维护**: 请在每次重大技术更新后同步更新本文档
**最后更新**: 2025-11-08
**下次审查**: 根据技术演进定期审查

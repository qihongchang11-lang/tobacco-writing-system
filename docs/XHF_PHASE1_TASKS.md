# 新华财经风格改写系统 - Phase 1开发任务书

## 项目背景
基于tobacco-writing-pipeline架构，开发新华财经风格改写系统MVP版本。

## 核心要求
- 95%复用tobacco代码
- 开发周期：1-2天
- 质量目标：一次通过率≥70%

---

## 任务1: core/xhf_style_injector.py

### 功能描述
风格注入器：构建Prompt + 调用LLM + 解析结果

### 输入
- `original_text`: str - 待改写原文
- `samples`: List[Dict] - 检索到的Top-2样本
- `strict_mode`: bool - 是否启用约束解码

### 输出
```python
{
    "title": str,  # 15-30字
    "lead": str,   # 60-120字
    "body": str    # 5段左右
}
```

### 核心实现要点

#### 1. 加载配置
```python
import yaml

# 加载YAML配置
with open('conf/xhf_style_guide.yaml', 'r', encoding='utf-8') as f:
    style_guide = yaml.safe_load(f)

# 加载禁用词表
with open('conf/xhf_negative_phrases.txt', 'r', encoding='utf-8') as f:
    negative_phrases = [line.strip() for line in f if line.strip() and not line.startswith('#')]
```

#### 2. 语篇线索提取（轻量）
```python
def extract_discourse_cues(text: str, cue_dict: Dict) -> Dict[str, List[str]]:
    """
    从原文提取语篇线索
    返回: {"background": [...], "action": [...], "result": [...], ...}
    """
    cues_found = {category: [] for category in cue_dict.keys()}

    for category, keywords in cue_dict.items():
        for keyword in keywords:
            # 简单正则匹配含该关键词的句子片段
            pattern = f'[^。！？]*{re.escape(keyword)}[^。！？]*[。！？]'
            matches = re.findall(pattern, text)
            cues_found[category].extend(matches[:2])  # 每类最多2个

    return cues_found
```

#### 3. 样本智能截断
```python
def truncate_sample_by_paragraph(sample: Dict, max_chars: int = 400) -> str:
    """
    按段落截断样本，优先保留含数据+归因的段落
    """
    body = sample['body']
    paragraphs = [p.strip() for p in body.split('\n') if p.strip()]

    # 优先级：含数字 > 含引号(归因) > 段落靠前
    scored_paras = []
    for i, para in enumerate(paragraphs):
        score = 0
        if re.search(r'\d+[.%]', para):  # 含数字
            score += 10
        if '"' in para or '"' in para:  # 含引语
            score += 5
        score -= i * 0.5  # 靠前加分
        scored_paras.append((score, para))

    scored_paras.sort(reverse=True, key=lambda x: x[0])

    # 拼接到max_chars
    result = []
    total_len = 0
    for _, para in scored_paras:
        if total_len + len(para) > max_chars:
            break
        result.append(para)
        total_len += len(para)

    return '\n'.join(result)
```

#### 4. Prompt构建
```python
def build_prompt(original_text, samples, style_guide, negative_phrases, discourse_cues):
    """
    构建Few-shot Prompt
    """
    # 系统角色
    system_prompt = """你是新华财经的资深编辑，专门负责烟草工业企业报道的改写和润色。"""

    # 风格规范（从YAML）
    style_rules = f"""
【写作规范】
1. 标题：{style_guide['structure_rules']['title']['recommended_length']}字左右
   - 模式：{', '.join(style_guide['structure_rules']['title']['patterns'][:2])}
   - 风格：{style_guide['structure_rules']['title']['style']}

2. 导语：{style_guide['structure_rules']['lead']['recommended_length']}字左右
   - 结构：{style_guide['structure_rules']['lead']['structure']}
   - 要求：{', '.join(style_guide['structure_rules']['lead']['requirements'][:2])}

3. 正文：{style_guide['structure_rules']['body']['paragraph_count']}段左右
   - 结构：{' → '.join(style_guide['structure_rules']['body']['structure'])}
   - 要求：数据支撑、适当引语、逻辑清晰

4. 语言风格：{style_guide['language_style']['tone']}
   - 原则：{', '.join(style_guide['language_style']['key_principles'][:3])}
"""

    # 负例约束
    negative_examples = f"""
【严格禁止使用】
{', '.join(negative_phrases[:10])}
以及其他空洞官腔表述。

【推荐使用】
{', '.join(style_guide['terminology']['positive_alternatives'][:5])}
"""

    # 语篇线索（如果提取到）
    discourse_hints = ""
    if any(discourse_cues.values()):
        discourse_hints = "\n【原文结构线索】\n"
        for category, cues in discourse_cues.items():
            if cues:
                discourse_hints += f"- {category}: {cues[0][:50]}...\n"

    # Few-shot样本
    few_shot_examples = ""
    for i, sample_data in enumerate(samples[:2], 1):
        sample = sample_data['article']
        truncated_body = truncate_sample_by_paragraph(sample)

        few_shot_examples += f"""
【示例{i}】
标题：{sample['title']}
导语：{sample['lead']}
正文片段：
{truncated_body}
"""

    # 组装最终Prompt
    user_prompt = f"""{system_prompt}

{style_rules}

{negative_examples}

{discourse_hints}

{few_shot_examples}

【待改写原文】
{original_text}

【输出要求】
严格按照以下JSON格式输出（不要包含markdown代码块标记）：
{{
  "title": "...",
  "lead": "...",
  "body": "..."
}}

注意：
1. 禁止新增原文中不存在的事实、数据
2. 保持所有数字、时间、机构名的准确性
3. 正文按"背景→举措→结果→意义"组织
4. 标题15-30字，导语60-120字
"""

    return user_prompt
```

#### 5. LLM调用
```python
import os
from openai import OpenAI

async def call_llm(prompt: str) -> str:
    """
    调用LLM API
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # 更稳定
        max_tokens=2000
    )

    return response.choices[0].message.content
```

#### 6. 约束解码集成
```python
from core.constraint_decoder import ConstraintDecoder

def protect_and_rewrite(original_text: str, strict_mode: bool) -> tuple:
    """
    保护实体+改写+恢复
    """
    if not strict_mode:
        return original_text, {}

    decoder = ConstraintDecoder()
    protected_text, entity_map = decoder.protect_entities(
        original_text,
        protect_numbers=True,
        protect_dates=True,
        protect_orgs=True
    )

    # TODO: 调用LLM改写protected_text
    # rewritten = await call_llm(...)

    # 恢复实体
    # final_text = decoder.restore_entities(rewritten, entity_map)

    return protected_text, entity_map
```

### 完整类结构
```python
class XHFStyleInjector:
    def __init__(
        self,
        style_yaml="conf/xhf_style_guide.yaml",
        negative_phrases_file="conf/xhf_negative_phrases.txt"
    ):
        self.style_guide = self._load_yaml(style_yaml)
        self.negative_phrases = self._load_negative_phrases(negative_phrases_file)
        self.decoder = ConstraintDecoder()

    async def rewrite(
        self,
        original_text: str,
        samples: List[Dict],
        strict_mode: bool = False
    ) -> Dict:
        """
        主入口：改写原文
        """
        # 1. 提取语篇线索
        discourse_cues = self.extract_discourse_cues(
            original_text,
            self.style_guide.get('discourse_cues', {})
        )

        # 2. 约束解码保护（如果开启）
        if strict_mode:
            original_text, entity_map = self.decoder.protect_entities(
                original_text,
                protect_numbers=True,
                protect_dates=True,
                protect_orgs=True
            )

        # 3. 构建Prompt
        prompt = self.build_prompt(
            original_text,
            samples,
            self.style_guide,
            self.negative_phrases,
            discourse_cues
        )

        # 4. 调用LLM
        response_text = await self.call_llm(prompt)

        # 5. 解析JSON
        result = self.parse_json_response(response_text)

        # 6. 恢复实体（如果开启了约束解码）
        if strict_mode:
            result['title'] = self.decoder.restore_entities(result['title'], entity_map)
            result['lead'] = self.decoder.restore_entities(result['lead'], entity_map)
            result['body'] = self.decoder.restore_entities(result['body'], entity_map)

        return result
```

---

## 任务2: core/xhf_quality_checker.py

### 功能描述
质量检查器：3维评分 + 事实一致性校验

### 输入
```python
{
    "title": str,
    "lead": str,
    "body": str
},
original_text: str  # 原文（用于比对）
```

### 输出
```python
{
    "overall": float,  # 0-1
    "details": {
        "consistency": {
            "score": float,
            "issues": List[str],
            "numbers_match": bool,
            "entities_match": bool
        },
        "style": {
            "score": float,
            "title_length": int,
            "lead_length": int,
            "terminology_count": int,
            "negative_phrases_count": int
        },
        "structure": {
            "score": float,
            "paragraph_count": int,
            "has_background": bool,
            "has_action": bool,
            "has_result": bool
        }
    }
}
```

### 核心实现

#### 1. 事实一致性检查
```python
def check_factual_consistency(original: str, rewritten: Dict) -> Dict:
    """
    逐项比对数字、实体
    """
    # 提取数字
    orig_numbers = set(re.findall(r'\d+[.%万亿]?\d*', original))
    rewritten_text = f"{rewritten['title']} {rewritten['lead']} {rewritten['body']}"
    rewritten_numbers = set(re.findall(r'\d+[.%万亿]?\d*', rewritten_text))

    # 检查数字是否一致
    missing_numbers = orig_numbers - rewritten_numbers
    new_numbers = rewritten_numbers - orig_numbers

    # 提取机构名（简单NER）
    org_pattern = r'([\u4e00-\u9fa5]{2,10}(公司|企业|集团|局|厅|部|工厂|中心))'
    orig_orgs = set(re.findall(org_pattern, original))
    rewritten_orgs = set(re.findall(org_pattern, rewritten_text))

    missing_orgs = orig_orgs - rewritten_orgs

    issues = []
    if missing_numbers:
        issues.append(f"遗漏数字: {', '.join(list(missing_numbers)[:3])}")
    if new_numbers:
        issues.append(f"新增数字: {', '.join(list(new_numbers)[:3])}")
    if missing_orgs:
        issues.append(f"遗漏机构: {', '.join([o[0] for o in list(missing_orgs)[:2]])}")

    score = 1.0
    if missing_numbers or new_numbers:
        score -= 0.3
    if missing_orgs:
        score -= 0.2

    return {
        "score": max(0, score),
        "issues": issues,
        "numbers_match": len(missing_numbers) == 0 and len(new_numbers) == 0,
        "entities_match": len(missing_orgs) == 0
    }
```

#### 2. 风格检查
```python
def check_style_compliance(rewritten: Dict, style_guide: Dict, negative_phrases: List) -> Dict:
    """
    风格符合度检查
    """
    title_len = len(rewritten['title'])
    lead_len = len(rewritten['lead'])

    # 标题长度评分
    title_score = 1.0
    if title_len < 15 or title_len > 30:
        title_score = 0.5

    # 导语长度评分
    lead_score = 1.0
    if lead_len < 60 or lead_len > 120:
        lead_score = 0.7

    # 财经术语覆盖
    full_text = f"{rewritten['title']} {rewritten['lead']} {rewritten['body']}"
    terminology = style_guide['terminology']['financial_terms']
    term_count = sum(1 for term in terminology if term in full_text)
    term_score = min(1.0, term_count / 3)  # 至少3个术语

    # 禁用词检查
    negative_count = sum(1 for phrase in negative_phrases if phrase in full_text)
    negative_score = max(0, 1.0 - negative_count * 0.1)

    overall_style_score = (
        0.3 * title_score +
        0.3 * lead_score +
        0.3 * term_score +
        0.1 * negative_score
    )

    return {
        "score": overall_style_score,
        "title_length": title_len,
        "lead_length": lead_len,
        "terminology_count": term_count,
        "negative_phrases_count": negative_count
    }
```

#### 3. 结构检查
```python
def check_structure(rewritten: Dict, discourse_cues: Dict) -> Dict:
    """
    结构完整度检查
    """
    body = rewritten['body']
    paragraphs = [p.strip() for p in body.split('\n') if p.strip()]

    # 检查是否包含各类线索
    has_background = any(
        any(kw in body for kw in discourse_cues.get('background', []))
    )
    has_action = any(
        any(kw in body for kw in discourse_cues.get('action', []))
    )
    has_result = any(
        any(kw in body for kw in discourse_cues.get('result', []))
    )

    coverage = sum([has_background, has_action, has_result])
    structure_score = coverage / 3.0

    # 段落数检查
    para_count = len(paragraphs)
    if para_count < 3 or para_count > 8:
        structure_score *= 0.8

    return {
        "score": structure_score,
        "paragraph_count": para_count,
        "has_background": has_background,
        "has_action": has_action,
        "has_result": has_result
    }
```

#### 4. 完整类结构
```python
class XHFQualityChecker:
    def __init__(
        self,
        style_yaml="conf/xhf_style_guide.yaml",
        negative_phrases_file="conf/xhf_negative_phrases.txt"
    ):
        self.style_guide = self._load_yaml(style_yaml)
        self.negative_phrases = self._load_negative_phrases(negative_phrases_file)

    def check(self, rewritten: Dict, original_text: str) -> Dict:
        """
        主入口：质量检查
        """
        # 1. 事实一致性
        consistency = self.check_factual_consistency(original_text, rewritten)

        # 2. 风格符合度
        style = self.check_style_compliance(
            rewritten,
            self.style_guide,
            self.negative_phrases
        )

        # 3. 结构完整度
        structure = self.check_structure(
            rewritten,
            self.style_guide.get('discourse_cues', {})
        )

        # 4. 综合评分
        overall = (
            0.4 * consistency['score'] +
            0.35 * style['score'] +
            0.25 * structure['score']
        )

        return {
            "overall": round(overall, 2),
            "details": {
                "consistency": consistency,
                "style": style,
                "structure": structure
            }
        }
```

---

## 任务3: 修改api_main.py

### 新增endpoint

```python
from core.xhf_style_injector import XHFStyleInjector
from core.xhf_quality_checker import XHFQualityChecker
from knowledge_base.intelligent_retriever import IntelligentRetriever

# 初始化（全局单例）
xhf_retriever = IntelligentRetriever(
    data_file="data/xhf_samples/structured_articles.json"
)
xhf_injector = XHFStyleInjector()
xhf_checker = XHFQualityChecker()


class XHFRewriteRequest(BaseModel):
    text: str
    article_type: Optional[str] = "tech_innovation"
    strict_mode: bool = False


@app.post("/rewrite/xinhua_caijing")
async def rewrite_xinhua_caijing(request: XHFRewriteRequest):
    """
    新华财经风格改写
    """
    start_time = time.time()

    try:
        # 1. 检索相似样本（Top-2）
        samples = xhf_retriever.retrieve(
            query_text=request.text,
            top_k=2,
            genre_filter=request.article_type
        )

        # 2. 风格注入+LLM改写
        result = await xhf_injector.rewrite(
            original_text=request.text,
            samples=samples,
            strict_mode=request.strict_mode
        )

        # 3. 质量检查
        scores = xhf_checker.check(result, request.text)

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "title": result['title'],
            "lead": result['lead'],
            "body": result['body'],
            "scores": scores,
            "meta": {
                "latency_ms": latency_ms,
                "samples_used": [s.get('id', '') for s in samples],
                "article_type": request.article_type
            }
        }

    except Exception as e:
        logger.error(f"新华财经改写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 验收标准

### 功能测试
1. API能正常响应
2. 返回包含title/lead/body
3. 评分包含3个维度

### 质量测试
1. 标题15-30字通过率≥90%
2. 导语60-120字通过率≥90%
3. 事实一致性检查无误

### 性能测试
1. 响应时间≤25秒
2. 并发5请求不报错

---

## 注意事项

1. **复用tobacco代码**
   - ConstraintDecoder
   - IntelligentRetriever
   - 环境变量配置

2. **错误处理**
   - JSON解析失败降级处理
   - LLM超时重试机制

3. **日志记录**
   - 关键步骤打log
   - 便于调试

---

## 开发检查清单

- [ ] conf/xhf_negative_phrases.txt 已创建
- [ ] conf/xhf_style_guide.yaml 已更新
- [ ] core/xhf_style_injector.py 完整实现
- [ ] core/xhf_quality_checker.py 完整实现
- [ ] api_main.py 新增endpoint
- [ ] 本地测试通过
- [ ] 文档注释完整

# -*- coding: utf-8 -*-
"""
新华财经风格注入器
核心功能：构建Few-shot Prompt + 调用LLM + 解析结果
"""
import json
import os
import re
import yaml
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
from openai import OpenAI

from core.constraint_decoder import ConstraintDecoder


class XHFStyleInjector:
    """新华财经风格注入器"""

    def __init__(
        self,
        style_yaml: str = "conf/xhf_style_guide.yaml",
        negative_phrases_file: str = "conf/xhf_negative_phrases.txt"
    ):
        """
        初始化风格注入器

        Args:
            style_yaml: 风格指导配置文件路径
            negative_phrases_file: 禁用词表文件路径
        """
        self.style_guide = self._load_yaml(style_yaml)
        self.negative_phrases = self._load_negative_phrases(negative_phrases_file)
        self.decoder = ConstraintDecoder()

        logger.info(f"XHFStyleInjector initialized")
        logger.info(f"  - Loaded {len(self.negative_phrases)} negative phrases")
        logger.info(f"  - Style guide version: {self.style_guide.get('meta', {}).get('version', 'unknown')}")

    def _load_yaml(self, yaml_path: str) -> Dict:
        """加载YAML配置文件"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load YAML config: {e}")
            return {}

    def _load_negative_phrases(self, txt_path: str) -> List[str]:
        """加载禁用词表"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                phrases = []
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if line and not line.startswith('#'):
                        phrases.append(line)
                return phrases
        except Exception as e:
            logger.error(f"Failed to load negative phrases: {e}")
            return []

    def extract_discourse_cues(self, text: str, cue_dict: Dict) -> Dict[str, List[str]]:
        """
        从原文提取语篇线索（轻量级）

        Args:
            text: 原文
            cue_dict: 线索词字典

        Returns:
            Dict[str, List[str]]: {category: [matched_fragments]}
        """
        cues_found = {category: [] for category in cue_dict.keys()}

        for category, keywords in cue_dict.items():
            for keyword in keywords:
                # 简单正则匹配含该关键词的句子片段
                pattern = f'[^。！？]*{re.escape(keyword)}[^。！？]*[。！？]'
                matches = re.findall(pattern, text)
                cues_found[category].extend(matches[:2])  # 每类最多2个

        logger.debug(f"Extracted discourse cues: {sum(len(v) for v in cues_found.values())} total")
        return cues_found

    def truncate_sample_by_paragraph(self, sample: Dict, max_chars: int = 400) -> str:
        """
        按段落智能截断样本，优先保留含数据+归因的段落

        Args:
            sample: 样本文章字典
            max_chars: 最大字符数

        Returns:
            str: 截断后的正文片段
        """
        body = sample.get('body', '')
        paragraphs = [p.strip() for p in body.split('\n') if p.strip()]

        if not paragraphs:
            return body[:max_chars]

        # 优先级打分：含数字 > 含引号(归因) > 段落靠前
        scored_paras = []
        for i, para in enumerate(paragraphs):
            score = 0
            # 含数字（财经数据）
            if re.search(r'\d+[.%]', para):
                score += 10
            # 含引语（归因）
            if '"' in para or '"' in para or '表示' in para:
                score += 5
            # 位置加分（靠前的段落更重要）
            score -= i * 0.5

            scored_paras.append((score, para))

        # 按分数降序排序
        scored_paras.sort(reverse=True, key=lambda x: x[0])

        # 拼接到max_chars
        result = []
        total_len = 0
        for _, para in scored_paras:
            if total_len + len(para) > max_chars:
                break
            result.append(para)
            total_len += len(para)

        return '\n'.join(result) if result else paragraphs[0][:max_chars]

    def build_prompt(
        self,
        original_text: str,
        samples: List[Dict],
        discourse_cues: Dict[str, List[str]]
    ) -> str:
        """
        构建Few-shot Prompt

        Args:
            original_text: 待改写的原文
            samples: 检索到的Top-K样本
            discourse_cues: 提取的语篇线索

        Returns:
            str: 完整的Prompt文本
        """
        # 系统角色
        system_prompt = "你是新华财经的资深编辑，专门负责烟草工业企业报道的改写和润色。"

        # 风格规范（从YAML）
        structure_rules = self.style_guide.get('structure_rules', {})
        language_style = self.style_guide.get('language_style', {})
        terminology = self.style_guide.get('terminology', {})

        style_rules = f"""
【写作规范】
1. 标题：{structure_rules.get('title', {}).get('recommended_length', 20)}字左右
   - 模式：{', '.join(structure_rules.get('title', {}).get('patterns', [])[:2])}
   - 风格：{structure_rules.get('title', {}).get('style', '')}

2. 导语：{structure_rules.get('lead', {}).get('recommended_length', 88)}字左右
   - 结构：{structure_rules.get('lead', {}).get('structure', '')}
   - 要求：{', '.join(structure_rules.get('lead', {}).get('requirements', [])[:2])}

3. 正文：{structure_rules.get('body', {}).get('paragraph_count', 5)}段左右
   - 结构：{' → '.join(structure_rules.get('body', {}).get('structure', []))}
   - 要求：数据支撑、适当引语、逻辑清晰

4. 语言风格：{language_style.get('tone', '')}
   - 原则：{', '.join(language_style.get('key_principles', [])[:3])}

【P0级写作技巧增强 - CRITICAL】

1. 诗意化开篇技巧（MUST EXECUTE）：
   - 【地域意象开篇】必须以地理文化意象开篇，格式：\"XX叠翠，XX潮涌\"或\"XX如画，XX如歌\"
   - 【时代背景】第二句接入时代宏观背景：\"在XX的时代浪潮中\"、\"在XX发展的关键节点上\"
   - 【主体行动】第三句点出主体及其行动：\"XX单位锚定航向、破局前行\"
   - 【禁止平铺直叙】严禁直接\"近日，XX单位...\"等枯燥开篇

2. 三层架构强制执行（MUST EXECUTE）：
   - 【第一层-破冰篇】占30%篇幅
     * 小标题格式：\"XX：以XX谋XX\"（如\"破冰：以小切口谋篇大棋局\"）
     * 内容要求：问题诊断→战略选择→理念阐释
   - 【第二层-深耕篇】占40%篇幅
     * 小标题格式：\"XX：以XX激发XX\"（如\"深耕：以聚合力激发新生态\"）
     * 内容要求：机制设计→典型案例→人才培养
   - 【第三层-跃升篇】占30%篇幅
     * 小标题格式：\"XX：以XX实现XX\"（如\"跃升：以低门槛实现高效能\"）
     * 内容要求：多领域成效→观念转变→未来愿景

3. 案例深度强制处理（MUST EXECUTE）：
   - 【四步完整链条】每个案例必须包含：
     * 步骤1-痛点场景化（30-50字）：\"XX（具体地点/部门）曾为XX（具体问题）而犯难\"
     * 步骤2-技术方案详解（60-100字）：\"XX团队依托XX技术，开发XX系统。系统运用XX算法/模型，通过XX方式...\"
     * 步骤3-技术原理（30-50字）：简要说明核心实现逻辑或创新点
     * 步骤4-量化效果（20-40字）：\"应用后，XX指标提升X%，XX指标增长X%，XX效率提升X倍\"
   - 【禁止浅描】严禁\"XX开发了XX系统，有效提升了效率\"等一句话带过

4. 金句提炼强制执行（MUST EXECUTE）：
   - 【对称哲学表达】每个重要观点必须用以下模式之一：
     * \"不是...而是...\"：\"数字化转型不是选择题，而是必答题\"
     * \"从...到...\"：\"从被动应对转向主动创造\"
     * \"让...成为...\"：\"让数据看得见也用得上\"
   - 【并列韵律短语】关键行动用四字短语并列：\"锚定航向、破局前行\"、\"聚智共创、深扎业务\"

5. 修辞技法强制应用（MUST EXECUTE）：
   - 【比喻】至少2处：\"低代码平台成为多层贯通的神经中枢\"
   - 【对偶】至少1处：\"数据看得见 也 用得上\"
   - 【排比】至少1处：\"用数据说话、用数据决策、用数据管理、用数据创新\"

6. 数据精确性强制保护（MUST EXECUTE）：
   - 【精确数字】必须保留原文所有具体数字（52名、20%、100余项等）
   - 【严禁模糊】绝对禁止用\"显著\"、\"有效\"、\"大幅\"、\"明显\"等模糊词汇
   - 【渐进展示】多个数据要层层递进：\"50余项流程→100余项审核点→效率提升20%\"

【质量检查点】
- 开篇必须有地域意象 ✓
- 必须有3层结构+小标题 ✓
- 案例必须有完整四步链条 ✓
- 数据必须精确无模糊表述 ✓
- 必须有金句和修辞手法 ✓
"""

        # 负例约束
        negative_examples = f"""
【严格禁止使用】
{', '.join(self.negative_phrases[:10])}
以及其他空洞官腔表述。

【推荐使用】
{', '.join(terminology.get('positive_alternatives', [])[:5])}
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
            sample = sample_data.get('article', sample_data)
            # 黄金样本(quality_score >= 0.9)完整展示,普通样本截断
            quality_score = sample.get('quality_score', 0)
            if quality_score >= 0.9:
                # 黄金样本完整展示前3000字,保留完整的风格示范
                truncated_body = sample.get('body', '')[:3000]
                logger.info(f"Golden sample detected (score={quality_score}), displaying full content (3000 chars)")
            else:
                # 普通样本智能截断
                truncated_body = self.truncate_sample_by_paragraph(sample, max_chars=1000)

            few_shot_examples += f"""
【示例{i}】
标题：{sample.get('title', '')}
导语：{sample.get('lead', '')}
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

【P0级案例深化处理 - CRITICAL】

**案例识别与强制深化规则**：
当原文出现以下模式时，必须按四步链条深化：
- "XX开发了XX系统"
- "XX实施XX项目"
- "XX建设XX平台"
- "XX推出XX功能"

**四步强制链条（每个案例必须完整执行）**：

1. **步骤1-痛点场景化**（30-50字）：
   - 格式："XX（具体地点/部门）曾为XX（具体问题）而犯难"
   - 示例："丹阳市乐飞生活便利店曾为上千种商品如何精准打折而犯难"
   - 禁止：一般性描述，必须具体到场景

2. **步骤2-技术方案详解**（60-100字）：
   - 格式："XX团队依托XX技术，开发XX系统。系统运用XX算法/模型，通过XX方式..."
   - 必须包含：技术手段+实现方式+功能机制
   - 禁止：简单的"开发了XX系统"

3. **步骤3-技术原理**（30-50字）：
   - 简要说明核心实现逻辑或创新点
   - 示例："运用多维度动态测算模型，精准输出收益预期、市场响应等分析"

4. **步骤4-量化效果**（20-40字）：
   - 格式："应用后，XX指标提升X%，XX指标增长X%，XX效率提升X倍"
   - 必须：精确数据，禁止"显著提升"、"有效改善"等模糊表述

**强制执行检查点**：
- 每个技术案例必须包含上述4个步骤
- 总字数不少于140字
- 数据必须精确到具体数值

【关键要求】
1. 信息完整性（CRITICAL）：
   - 必须保留原文中的所有关键信息点、重要举措、数据成效
   - 不得删减原文的核心内容，改写是对表达的优化而非内容的压缩
   - 改写后总字数应与原文相当（允许±20%浮动）
   - 原文800字以上的，改写后正文至少600字
   - 原文1000字以上的，改写后正文至少800字

2. 事实准确性：
   - 禁止新增原文中不存在的事实、数据
   - 保持所有数字、时间、机构名的准确性
   - 所有数据必须来源于原文，不得虚构

3. 结构与长度：
   - 正文按"背景→举措→结果→意义"组织
   - 标题15-30字，导语60-120字
   - 正文3-8段，每段80-200字，段落间用空行分隔
   - 较长的原文（1000字以上）应组织为5-8段

4. 语言风格：
   - 保持新华财经专业、客观、准确的基调
   - 语言自然流畅，避免生硬的模板化表达
   - 适当使用过渡词和连接词，保持行文连贯
   - 避免机械堆砌数据，注重叙事流畅性
"""

        logger.debug(f"Built prompt with {len(user_prompt)} characters")
        return user_prompt

    async def call_llm(self, prompt: str) -> str:
        """
        调用LLM API

        Args:
            prompt: 输入Prompt

        Returns:
            str: LLM返回的文本
        """
        try:
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL")
            )

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,  # 略微提高温度以增加自然度
                max_tokens=4000  # 增加到4000以支持较长文章的完整改写
            )

            result = response.choices[0].message.content
            logger.info(f"LLM response received: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def parse_json_response(self, response_text: str) -> Dict:
        """
        解析LLM返回的JSON响应

        Args:
            response_text: LLM返回的文本

        Returns:
            Dict: {title, lead, body}
        """
        try:
            # 移除可能的markdown代码块标记
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                # 去除开头的```json或```
                cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
                # 去除结尾的```
                cleaned = re.sub(r'\n```\s*$', '', cleaned)

            # 解析JSON
            result = json.loads(cleaned)

            # 验证必需字段
            required_fields = ['title', 'lead', 'body']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            logger.info("JSON response parsed successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {response_text[:500]}")

            # 降级处理：尝试手动提取
            return self._fallback_parse(response_text)

    def _fallback_parse(self, text: str) -> Dict:
        """
        降级解析：当JSON解析失败时，尝试手动提取

        Args:
            text: 响应文本

        Returns:
            Dict: {title, lead, body}
        """
        logger.warning("Using fallback parser")

        result = {
            "title": "",
            "lead": "",
            "body": ""
        }

        # 尝试提取标题
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', text)
        if title_match:
            result['title'] = title_match.group(1)

        # 尝试提取导语
        lead_match = re.search(r'"lead"\s*:\s*"([^"]+)"', text)
        if lead_match:
            result['lead'] = lead_match.group(1)

        # 尝试提取正文
        body_match = re.search(r'"body"\s*:\s*"([^"]+)"', text, re.DOTALL)
        if body_match:
            result['body'] = body_match.group(1)

        return result

    async def rewrite(
        self,
        original_text: str,
        samples: List[Dict],
        strict_mode: bool = False
    ) -> Dict:
        """
        主入口：改写原文

        Args:
            original_text: 待改写的原文
            samples: 检索到的Top-K样本
            strict_mode: 是否启用约束解码（实体保护）

        Returns:
            Dict: {title, lead, body}
        """
        logger.info(f"Starting rewrite (strict_mode={strict_mode})")

        # 1. 提取语篇线索
        discourse_cues = self.extract_discourse_cues(
            original_text,
            self.style_guide.get('discourse_cues', {})
        )

        # 2. 约束解码保护（如果开启）
        entity_map = {}
        if strict_mode:
            logger.info("Applying constraint decoding...")
            entities = self.decoder.extract_entities(original_text)
            original_text, entity_map = self.decoder.to_placeholders(original_text, entities)
            logger.info(f"Protected {len(entity_map)} entities")

        # 3. 构建Prompt
        prompt = self.build_prompt(
            original_text,
            samples,
            discourse_cues
        )

        # 4. 调用LLM
        response_text = await self.call_llm(prompt)

        # 5. 解析JSON
        result = self.parse_json_response(response_text)

        # 6. 恢复实体（如果开启了约束解码）
        if strict_mode and entity_map:
            logger.info("Restoring entities...")
            result['title'] = self.decoder.restore(result['title'], entity_map)
            result['lead'] = self.decoder.restore(result['lead'], entity_map)
            result['body'] = self.decoder.restore(result['body'], entity_map)

        logger.info("Rewrite completed successfully")
        return result


# 测试代码
if __name__ == '__main__':
    import asyncio
    from knowledge_base.intelligent_retriever import IntelligentRetriever

    async def test_injector():
        # 初始化组件
        retriever = IntelligentRetriever(
            data_file="data/xhf_samples/structured_articles.json"
        )
        injector = XHFStyleInjector()

        # 测试原文
        test_text = """
        近日，山东省烟草专卖局召开全省数字化转型推进会议，
        深入贯彻落实行业高质量发展要求，推动智能制造和数字化管理全面升级。
        今年以来，全省累计投入资金5000万元用于智能化改造项目。
        会议要求各地烟草企业要全力以赴推进数字化转型工作。
        """

        print("=" * 60)
        print("测试新华财经风格注入器")
        print("=" * 60)

        # 1. 检索样本
        print("\n[1/3] 检索相似样本...")
        samples = retriever.retrieve(test_text, top_k=2)
        print(f"  检索到 {len(samples)} 个样本")

        # 2. 改写
        print("\n[2/3] 执行改写...")
        result = await injector.rewrite(test_text, samples, strict_mode=False)

        # 3. 输出结果
        print("\n[3/3] 改写结果：")
        print(f"\n标题: {result['title']}")
        print(f"\n导语: {result['lead']}")
        print(f"\n正文:\n{result['body']}")

        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

    # 运行测试
    asyncio.run(test_injector())

# -*- coding: utf-8 -*-
"""
新华财经样稿蒸馏脚本
功能：从结构化样稿中提取可复用的原句原型和风格规则
输出：
1. data/xhf_prototypes/sentence_prototypes.json - 原句原型库
2. conf/xhf_style_guide.yaml - 风格指导配置
"""
import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter


def load_structured_articles(json_path: str) -> List[Dict]:
    """加载结构化文章"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_sentence_prototypes(articles: List[Dict]) -> Dict[str, List[str]]:
    """
    提取原句原型
    分类：title_templates, lead_templates, opening_sentences, transition_phrases
    """
    prototypes = {
        "title_templates": [],
        "lead_templates": [],
        "opening_sentences": [],
        "transition_phrases": [],
        "conclusion_sentences": []
    }

    for article in articles:
        # 标题原型（抽象化处理）
        title = article['title']
        title_proto = _abstract_title(title)
        if title_proto and title_proto not in prototypes['title_templates']:
            prototypes['title_templates'].append(title_proto)

        # 导语原型
        lead = article['lead']
        lead_proto = _abstract_lead(lead)
        if lead_proto and lead_proto not in prototypes['lead_templates']:
            prototypes['lead_templates'].append(lead_proto)

        # 正文首句（背景引入）
        body = article['body']
        opening = _extract_opening_sentence(body)
        if opening and opening not in prototypes['opening_sentences']:
            prototypes['opening_sentences'].append(opening)

        # 过渡短语
        transitions = _extract_transition_phrases(body)
        for t in transitions:
            if t not in prototypes['transition_phrases']:
                prototypes['transition_phrases'].append(t)

        # 结尾句
        conclusion = _extract_conclusion_sentence(body)
        if conclusion and conclusion not in prototypes['conclusion_sentences']:
            prototypes['conclusion_sentences'].append(conclusion)

    return prototypes


def _abstract_title(title: str) -> str:
    """
    抽象化标题结构
    保留模式，用[X]替换具体内容
    """
    # 保留引号和冒号结构
    if '：' in title or ':' in title:
        parts = re.split(r'[：:]', title)
        if len(parts) == 2:
            return f"[主题]：[行动+效果]"

    # 检测动宾结构
    if any(kw in title for kw in ['激活', '书写', '织网', '解难题', '巧解']):
        return "[动作][对象]"

    # 长叙事式
    if len(title) > 20:
        return "[企业/部门]+[创新举措]+[成效关键词]"

    return title


def _abstract_lead(lead: str) -> str:
    """
    抽象化导语结构
    提取通用模式
    """
    # 检测常见模式
    if lead.startswith('近日') or lead.startswith('近年来'):
        return "[时间]，[企业名]以[方法]为[目标]，[具体举措]，[成效]。"

    if lead.startswith('今年') or '年前' in lead[:10]:
        return "[时间段]，[企业名]通过[技术/方法]，实现[成效]，为[意义]提供[支撑/样本]。"

    # 通用模式
    if '通过' in lead and '实现' in lead:
        return "[企业名]通过[方法/技术]，实现[成效]，[更高层意义]。"

    return lead[:50] + "..."  # 保留前50字作为参考


def _extract_opening_sentence(body: str) -> str:
    """提取正文首句（通常是背景或问题引入）"""
    sentences = re.split(r'[。！？]', body)
    if sentences and len(sentences[0]) > 20:
        return sentences[0][:100]
    return ""


def _extract_transition_phrases(body: str) -> List[str]:
    """提取过渡短语"""
    transition_patterns = [
        r'针对.*?痛点',
        r'聚焦.*?需求',
        r'通过.*?实现',
        r'作为.*?缩影',
        r'近年来.*?持续',
        r'在.*?背景下',
        r'围绕.*?开展',
        r'深化.*?建设'
    ]

    transitions = []
    for pattern in transition_patterns:
        matches = re.findall(pattern, body)
        transitions.extend(matches[:2])  # 每个模式最多取2个

    return transitions[:10]  # 总共最多10个


def _extract_conclusion_sentence(body: str) -> str:
    """提取结尾句（通常总结意义或展望）"""
    sentences = re.split(r'[。！？]', body)
    # 取倒数第二句（最后一句可能是空的）
    for i in range(len(sentences) - 1, max(len(sentences) - 4, -1), -1):
        sent = sentences[i].strip()
        if len(sent) > 30 and any(kw in sent for kw in ['提供', '推动', '为', '实现', '贡献', '示范']):
            return sent
    return ""


def extract_key_terminology(articles: List[Dict]) -> Dict[str, List[str]]:
    """提取关键术语和高频词汇"""
    all_text = ' '.join([
        a['title'] + ' ' + a['lead'] + ' ' + a['body']
        for a in articles
    ])

    # 财经/行业术语
    financial_terms = re.findall(
        r'(高质量发展|数字化转型|智能制造|供应链|协同创新|精益化|标准化|'
        r'绿色低碳|节能增效|系统性|动态平衡|风险防控|质量体系|产业升级|'
        r'创新驱动|资源配置|优化升级|效能提升)',
        all_text
    )

    # 动作词汇
    action_verbs = re.findall(
        r'(构建|推动|实现|提升|优化|深化|创新|突破|融合|赋能|激发|释放|'
        r'助力|促进|强化|夯实|筑牢)',
        all_text
    )

    # 修饰词
    modifiers = re.findall(
        r'(全面|深入|持续|系统|精准|高效|智能|协同|精益|柔性|'
        r'集成|一体化|可复制|可持续)',
        all_text
    )

    return {
        "financial_terms": list(set(financial_terms)),
        "action_verbs": list(set(action_verbs)),
        "modifiers": list(set(modifiers))
    }


def generate_style_guide(articles: List[Dict], terminology: Dict) -> Dict:
    """生成风格指导配置"""

    # 计算平均长度
    avg_title_len = sum(len(a['title']) for a in articles) // len(articles)
    avg_lead_len = sum(len(a['lead']) for a in articles) // len(articles)

    # 统计段落数
    para_counts = [len(a['body'].split('\n')) for a in articles]
    avg_para_count = sum(para_counts) // len(para_counts)

    guide = {
        "meta": {
            "source": "新华财经",
            "sample_count": len(articles),
            "article_types": ["tech_innovation"],
            "version": "1.0"
        },

        "structure_rules": {
            "title": {
                "length_range": [15, 30],
                "recommended_length": avg_title_len,
                "patterns": [
                    "主副标题结构（用冒号分隔）",
                    "动宾结构+引号修饰",
                    "长叙事式（20字以上）"
                ],
                "style": "简洁有力，突出创新点和成效"
            },

            "lead": {
                "length_range": [60, 120],
                "recommended_length": avg_lead_len,
                "structure": "企业名+创新举措+核心成效+更高层意义",
                "requirements": [
                    "一句话概括全文核心",
                    "包含时间、主体、行动、成果",
                    "避免空泛表述，突出具体成效"
                ]
            },

            "body": {
                "paragraph_count": avg_para_count,
                "structure": [
                    "背景/问题引入（为什么要做）",
                    "创新举措详解（怎么做的）",
                    "实施效果展示（数据+引语）",
                    "更高层意义总结（行业价值）"
                ],
                "requirements": [
                    "每段3-5句，逻辑清晰",
                    "适当引用专家/员工发言",
                    "数据支撑，避免空谈",
                    "使用专业术语但保持可读性"
                ]
            }
        },

        "language_style": {
            "tone": "专业、客观、权威",
            "perspective": "第三人称叙述",
            "key_principles": [
                "数据驱动，避免夸张",
                "行业术语准确使用",
                "因果逻辑清晰",
                "成效可量化可验证"
            ],
            "avoid": [
                "过度官腔（如'全面贯彻落实'等）",
                "空洞口号",
                "主观评价",
                "冗长修饰"
            ]
        },

        "terminology": terminology,

        "quality_checks": {
            "title_length": {"min": 15, "max": 30},
            "lead_length": {"min": 60, "max": 120},
            "financial_term_coverage": {"min_ratio": 0.8},
            "data_presence": {"required": True},
            "quote_presence": {"recommended": True}
        }
    }

    return guide


def save_prototypes(prototypes: Dict, output_dir: Path):
    """保存原句原型"""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'sentence_prototypes.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prototypes, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已保存原句原型: {output_file}")
    print(f"  - 标题模板: {len(prototypes['title_templates'])} 个")
    print(f"  - 导语模板: {len(prototypes['lead_templates'])} 个")
    print(f"  - 开篇句式: {len(prototypes['opening_sentences'])} 个")
    print(f"  - 过渡短语: {len(prototypes['transition_phrases'])} 个")
    print(f"  - 结尾句式: {len(prototypes['conclusion_sentences'])} 个")


def save_style_guide(guide: Dict, output_file: Path):
    """保存风格指导配置"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(guide, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"\n[OK] 已保存风格指导: {output_file}")
    print(f"  - 结构规范: 标题/导语/正文")
    print(f"  - 语言风格: {guide['language_style']['tone']}")
    print(f"  - 术语库: {len(guide['terminology']['financial_terms'])} 个财经术语")
    print(f"  - 质量检查: {len(guide['quality_checks'])} 项指标")


def main():
    # 输入输出路径
    input_json = Path('data/xhf_samples/structured_articles.json')
    proto_output = Path('data/xhf_prototypes')
    guide_output = Path('conf/xhf_style_guide.yaml')

    print("=" * 60)
    print("新华财经样稿蒸馏")
    print("=" * 60)

    # 加载文章
    print(f"\n[1/3] 加载结构化文章: {input_json}")
    articles = load_structured_articles(str(input_json))
    print(f"  已加载 {len(articles)} 篇文章")

    # 提取原句原型
    print(f"\n[2/3] 提取原句原型...")
    prototypes = extract_sentence_prototypes(articles)
    save_prototypes(prototypes, proto_output)

    # 提取术语和生成风格指导
    print(f"\n[3/3] 生成风格指导配置...")
    terminology = extract_key_terminology(articles)
    style_guide = generate_style_guide(articles, terminology)
    save_style_guide(style_guide, guide_output)

    print("\n" + "=" * 60)
    print("[SUCCESS] 蒸馏完成!")
    print("=" * 60)
    print("\n下一步:")
    print("1. 查看 data/xhf_prototypes/sentence_prototypes.json")
    print("2. 查看 conf/xhf_style_guide.yaml")
    print("3. 开发 core/xhf_sample_retriever.py（样本检索器）")


if __name__ == '__main__':
    main()

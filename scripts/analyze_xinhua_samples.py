# -*- coding: utf-8 -*-
"""
新华财经样稿分析脚本
功能：
1. 解析TXT文件中的样稿文章
2. 识别文章类型（企业新闻/技术创新/人才培养/经营管理等）
3. 提取风格特征（标题结构、导语特点、正文模式）
4. 生成结构化JSON供后续模块使用
"""
import os
import re
import json
from typing import List, Dict
from pathlib import Path


def parse_txt_articles(txt_path: str) -> List[Dict]:
    """解析TXT文件中的文章"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    articles = []
    # 通过标题标识分割文章
    pattern = r'(\d+\.\s*【新华财经】.*?)(?=\d+\.\s*【新华财经】|【新华财经】多元化企业|$)'
    matches = re.findall(pattern, content, re.DOTALL)

    for idx, match in enumerate(matches, 1):
        lines = [line.strip() for line in match.strip().split('\n') if line.strip()]
        if len(lines) < 3:
            continue

        # 提取标题（第一行）
        title_line = lines[0]
        title = re.sub(r'^\d+\.\s*【新华财经】', '', title_line).strip()

        # 提取元信息
        meta = {}
        body_start = 1
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('部门：'):
                meta['department'] = line.replace('部门：', '').strip()
            elif line.startswith('投稿人：'):
                meta['author'] = line.replace('投稿人：', '').strip()
            elif line.startswith('发布日期：'):
                meta['publish_date'] = line.replace('发布日期：', '').strip()
                body_start = i + 1
                break

        # 提取导语和正文
        body_lines = lines[body_start:]
        lead = body_lines[0] if body_lines else ""
        body = '\n'.join(body_lines[1:]) if len(body_lines) > 1 else ""

        articles.append({
            "id": f"xhf_{idx:03d}",
            "title": title,
            "lead": lead,
            "body": body,
            "meta": meta,
            "source": "新华财经"
        })

    return articles


def classify_article_type(article: Dict) -> str:
    """
    根据标题和内容关键词分类文章类型
    分类：
    - enterprise_news: 企业新闻（会议、活动、成就）
    - tech_innovation: 技术创新（智能化、数字化改造）
    - talent_development: 人才培养（培训、竞赛、成长）
    - operation_management: 经营管理（供应链、质量、风控）
    - green_practice: 绿色实践（节能、环保）
    - case_study: 典型案例（具体做法和成效）
    """
    title = article['title']
    lead = article['lead']
    body = article['body']
    text = f"{title} {lead} {body}"

    # 技术创新关键词
    if any(kw in text for kw in ['智能', '数字化', '智慧', '系统', '技术', '自动化', '智控', 'LoRa', 'PLC', '可视化']):
        return 'tech_innovation'

    # 人才培养关键词
    if any(kw in text for kw in ['培训', '竞赛', '人才', '青年', '技能', '学习', '双训', '成长']):
        return 'talent_development'

    # 绿色实践关键词
    if any(kw in text for kw in ['节能', '绿色', '环保', '降耗', '碳', 'PUE', '能耗']):
        return 'green_practice'

    # 经营管理关键词
    if any(kw in text for kw in ['供应链', '管理', '风控', '协同', '质量', '备件', '库存', '排班']):
        return 'operation_management'

    # 典型案例关键词（问题+解决方案）
    if any(kw in text for kw in ['解决', '优化', '改进', '攻关', '突破', '创新实践']):
        return 'case_study'

    # 默认为企业新闻
    return 'enterprise_news'


def extract_style_features(article: Dict) -> Dict:
    """提取文章的风格特征"""
    title = article['title']
    lead = article['lead']
    body = article['body']

    features = {
        # 标题特征
        'title_features': {
            'has_quote_marks': '「' in title or '」' in title or '"' in title,
            'has_colon': '：' in title or ':' in title,
            'has_metaphor': any(kw in title for kw in ['比武', '闯关', '织网', '码上', '硬核']),
            'word_count': len(title),
            'structure': _analyze_title_structure(title)
        },

        # 导语特征
        'lead_features': {
            'word_count': len(lead),
            'starts_with_date': lead.startswith('近日') or lead.startswith('今年') or lead.startswith('近年来'),
            'has_data': bool(re.search(r'\d+[.%]|[一二三四五六七八九十百千万亿]+', lead)),
            'sentence_count': len(re.split(r'[。！？]', lead)) - 1
        },

        # 正文特征
        'body_features': {
            'paragraph_count': len([p for p in body.split('\n') if p.strip()]),
            'has_quote': '"' in body or '"' in body or '「' in body,
            'has_data': bool(re.search(r'\d+[.%]|[一二三四五六七八九十百千万亿]+', body)),
            'key_phrases': _extract_key_phrases(body)
        }
    }

    return features


def _analyze_title_structure(title: str) -> str:
    """分析标题结构模式"""
    if '：' in title or ':' in title:
        return 'main_sub'  # 主副标题
    elif any(kw in title for kw in ['如何', '怎样', '为何']):
        return 'question'  # 疑问式
    elif len(title) > 20:
        return 'long_narrative'  # 长叙事式
    else:
        return 'short_summary'  # 短概括式


def _extract_key_phrases(text: str) -> List[str]:
    """提取正文中的关键短语（财经/行业术语）"""
    key_patterns = [
        r'高质量发展', r'数字化转型', r'智能制造', r'协同创新',
        r'供应链', r'一体化', r'精益化', r'标准化',
        r'风险防控', r'质量体系', r'动态平衡', r'系统性',
        r'创新驱动', r'产业升级', r'绿色低碳', r'节能增效'
    ]

    found_phrases = []
    for pattern in key_patterns:
        if re.search(pattern, text):
            found_phrases.append(pattern)

    return found_phrases[:10]  # 最多返回10个


def generate_analysis_summary(articles: List[Dict]) -> Dict:
    """生成分析摘要"""
    type_counts = {}
    total_titles_length = 0
    total_leads_length = 0

    for article in articles:
        article_type = article.get('type', 'unknown')
        type_counts[article_type] = type_counts.get(article_type, 0) + 1
        total_titles_length += len(article['title'])
        total_leads_length += len(article['lead'])

    return {
        'total_articles': len(articles),
        'type_distribution': type_counts,
        'avg_title_length': total_titles_length // len(articles) if articles else 0,
        'avg_lead_length': total_leads_length // len(articles) if articles else 0,
        'source': '新华财经',
        'categories': list(type_counts.keys())
    }


def main():
    # 输入输出路径
    txt_path = Path('C:/Users/qhc13/tobacco-writing-pipeline/新华财经样稿.txt')
    output_dir = Path('data/xhf_samples')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 解析文章
    print(f"正在解析样稿文件: {txt_path}")
    articles = parse_txt_articles(str(txt_path))
    print(f"成功解析 {len(articles)} 篇文章\n")

    # 分类和特征提取
    print("正在分析文章类型和风格特征...")
    for article in articles:
        article['type'] = classify_article_type(article)
        article['style_features'] = extract_style_features(article)

    # 生成摘要
    summary = generate_analysis_summary(articles)

    # 保存结构化文章
    structured_output = output_dir / 'structured_articles.json'
    with open(structured_output, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已保存结构化文章: {structured_output}")

    # 保存分析摘要
    summary_output = output_dir / 'analysis_summary.json'
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已保存分析摘要: {summary_output}")

    # 打印统计信息
    print("\n" + "="*60)
    print("[Analysis Summary]")
    print("="*60)
    print(f"总文章数: {summary['total_articles']}")
    print(f"平均标题长度: {summary['avg_title_length']} 字")
    print(f"平均导语长度: {summary['avg_lead_length']} 字")
    print("\n文章类型分布:")
    for type_name, count in summary['type_distribution'].items():
        print(f"  - {type_name}: {count} 篇")

    # 展示样例
    print("\n" + "="*60)
    print("[Sample Display - First 2 Articles]")
    print("="*60)
    for i, article in enumerate(articles[:2], 1):
        print(f"\n[Article {i}]")
        print(f"ID: {article['id']}")
        print(f"标题: {article['title']}")
        print(f"类型: {article['type']}")
        print(f"导语: {article['lead'][:100]}...")
        print(f"标题特征: {article['style_features']['title_features']['structure']}")


if __name__ == '__main__':
    main()

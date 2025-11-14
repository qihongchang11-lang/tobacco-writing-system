#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解析并存储黄金样本文章
从东方烟草报样稿.txt中提取文章并按类型分类存储
"""

import json
import re
from pathlib import Path
from typing import List, Dict

# 文章类型映射
CATEGORY_MAPPING = {
    "技术创新": "技术创新类",
    "人物报道": "人物报道类",
    "管理创新": "管理创新类",
    "深度观察": "深度观察类",
    "政策学习": "政策学习类"
}

def extract_articles_from_sample_file(file_path: str) -> List[Dict]:
    """从样稿文件中提取所有文章"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按标题分割文章(标题格式: 【东方烟草报】xxx)
    article_pattern = r'【东方烟草报】(.*?)\n部门：(.*?)\n投稿人：(.*?)\n发布日期：(.*?)\n\n(.*?)(?=\n\n【东方烟草报】|\n\n国家局党组|\Z)'
    matches = re.findall(article_pattern, content, re.DOTALL)

    articles = []
    for i, match in enumerate(matches, 1):
        title, department, author, date, body = match
        article = {
            "id": f"golden_sample_{i:03d}",
            "title": title.strip(),
            "department": department.strip(),
            "author": author.strip(),
            "date": date.strip(),
            "body": body.strip(),
            "word_count": len(body.strip())
        }
        articles.append(article)

    return articles

def categorize_article(title: str, body: str) -> str:
    """根据标题和内容判断文章类型"""
    # 技术创新类关键词
    if any(kw in title or kw in body[:200] for kw in [
        "3D打印", "AI", "智能", "数字化", "技术", "创新", "设备", "系统",
        "超高速", "自动化", "机组", "平台", "备件管理", "看板"
    ]):
        return "技术创新类"

    # 人物报道类关键词
    if any(kw in title for kw in [
        "劳模", "技能竞赛", "火种", "成长", "新员工", "青年", "人物", "工匠"
    ]) or ("：" in title and any(kw in body[:200] for kw in ["坚守", "传承", "精神"])):
        return "人物报道类"

    # 深度观察类关键词
    if any(kw in title for kw in [
        "两山", "绿色", "物流", "安全", "转型", "观察", "深读", "低碳", "循环"
    ]) or len(body) > 3000:
        return "深度观察类"

    # 政策学习类关键词
    if any(kw in title or kw in body[:200] for kw in [
        "全会", "党组", "会议", "精神", "学习", "贯彻", "社论", "时代"
    ]):
        return "政策学习类"

    # 默认归类为管理创新类
    return "管理创新类"

def detect_features(title: str, body: str) -> Dict:
    """检测文章的写作特征"""
    features = {
        "literary_opening": False,
        "three_layer_structure": False,
        "philosophical_subtitles": 0,
        "deep_cases": 0,
        "precise_data": 0,
        "rhetoric_techniques": [],
        "golden_sentences": [],
        "parallel_phrases": []
    }

    # 检测诗意化开篇(前100字)
    opening = body[:100]
    if any(pattern in opening for pattern in ["潮涌", "叠翠", "浪潮", "春风", "锦绣"]):
        features["literary_opening"] = True

    # 检测三层结构(查找小标题)
    subtitle_pattern = r'\n[^\n]{2,20}\n'
    subtitles = re.findall(subtitle_pattern, body)
    features["philosophical_subtitles"] = len([s for s in subtitles if len(s.strip()) < 20])
    if features["philosophical_subtitles"] >= 3:
        features["three_layer_structure"] = True

    # 检测深度案例(包含"痛点"、"问题"、"解决"、"提升"等关键词的段落)
    case_indicators = ["痛点", "难题", "问题", "解决", "开发", "应用", "提升", "增长", "%"]
    paragraphs = body.split('\n\n')
    features["deep_cases"] = sum(1 for p in paragraphs if sum(1 for kw in case_indicators if kw in p) >= 3)

    # 检测精确数据(数字+单位/百分比)
    data_pattern = r'\d+\.?\d*(%|个|名|项|倍|万|千|百)'
    features["precise_data"] = len(re.findall(data_pattern, body))

    # 检测修辞手法
    if re.search(r'像.*一样|如同|犹如|宛如|恰似', body):
        features["rhetoric_techniques"].append("比喻")
    if re.search(r'不是.*而是|既.*又|一方面.*另一方面', body):
        features["rhetoric_techniques"].append("对偶")
    if re.search(r'([\u4e00-\u9fa5]{2,6}、){2,}[\u4e00-\u9fa5]{2,6}', body):
        features["rhetoric_techniques"].append("排比")

    # 提取金句(包含"不是...而是..."、"从...到..."等句式)
    golden_sentence_patterns = [
        r'[^。]{10,40}不是[^。]{5,20}而是[^。]{5,20}[。"]',
        r'[^。]{10,40}从[^。]{5,20}到[^。]{5,20}[。"]',
        r'[^。]{10,40}让[^。]{5,20}成为[^。]{5,20}[。"]'
    ]
    for pattern in golden_sentence_patterns:
        matches = re.findall(pattern, body)
        features["golden_sentences"].extend([m.strip('。"') for m in matches[:2]])

    # 提取并列短语(顿号连接的动词短语)
    parallel_pattern = r'([\u4e00-\u9fa5]{2,4}、[\u4e00-\u9fa5]{2,4}(?:、[\u4e00-\u9fa5]{2,4})?)'
    features["parallel_phrases"] = list(set(re.findall(parallel_pattern, body)))[:5]

    return features

def calculate_quality_score(features: Dict, word_count: int) -> float:
    """计算文章质量得分"""
    score = 0.5  # 基础分

    # 字数得分(3000+字: +0.1)
    if word_count >= 3000:
        score += 0.1

    # 文学性开篇: +0.1
    if features["literary_opening"]:
        score += 0.1

    # 三层结构: +0.15
    if features["three_layer_structure"]:
        score += 0.15

    # 深度案例: 每个+0.02,最多+0.1
    score += min(features["deep_cases"] * 0.02, 0.1)

    # 精确数据: 10个以上+0.05
    if features["precise_data"] >= 10:
        score += 0.05

    # 修辞技巧: 每种+0.02,最多+0.08
    score += min(len(features["rhetoric_techniques"]) * 0.02, 0.08)

    return min(score, 1.0)  # 最高1.0分

def main():
    # 输入输出路径
    sample_file = Path("D:/Users/qhc13/Desktop/东方烟草报专属Maker/东方烟草报样稿.txt")
    output_dir = Path("C:/Users/qhc13/tobacco-writing-pipeline/data/xhf_samples/golden")

    # 提取所有文章
    print("正在解析样稿文件...")
    articles = extract_articles_from_sample_file(str(sample_file))
    print(f"共提取 {len(articles)} 篇文章")

    # 处理每篇文章
    stats = {cat: 0 for cat in CATEGORY_MAPPING.values()}

    for article in articles:
        # 判断类型
        category = categorize_article(article["title"], article["body"])
        article["category"] = category
        stats[category] += 1

        # 提取导语(第一段)
        first_para = article["body"].split('\n\n')[0] if '\n\n' in article["body"] else article["body"][:100]
        article["lead"] = first_para[:150] + "..." if len(first_para) > 150 else first_para

        # 检测特征
        features = detect_features(article["title"], article["body"])
        article["features"] = features

        # 计算质量得分
        quality_score = calculate_quality_score(features, article["word_count"])
        article["quality_score"] = quality_score
        article["source"] = "东方烟草报"

        # 保存到对应类别文件夹
        category_dir = output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # 文件名: 移除特殊字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', article["title"])
        filename = f"{article['id']}_{safe_title}.json"
        output_path = category_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        print(f"[{category}] {article['title']} (字数:{article['word_count']}, 得分:{quality_score:.2f})")

    # 输出统计
    print("\n" + "="*60)
    print("文章分类统计:")
    for category, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count} 篇")
    print("="*60)
    print(f"\n所有黄金样本已保存到: {output_dir}")

if __name__ == "__main__":
    main()

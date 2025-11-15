# -*- coding: utf-8 -*-
"""
新华财经质量检查器
核心功能：3维评分 + 事实一致性校验
"""
import re
import yaml
from typing import Dict, List, Tuple
from pathlib import Path
from loguru import logger


class XHFQualityChecker:
    """新华财经质量检查器"""

    def __init__(
        self,
        style_yaml: str = "conf/xhf_style_guide.yaml",
        negative_phrases_file: str = "conf/xhf_negative_phrases.txt"
    ):
        """
        初始化质量检查器

        Args:
            style_yaml: 风格指导配置文件路径
            negative_phrases_file: 禁用词表文件路径
        """
        self.style_guide = self._load_yaml(style_yaml)
        self.negative_phrases = self._load_negative_phrases(negative_phrases_file)

        logger.info(f"XHFQualityChecker initialized")
        logger.info(f"  - Loaded {len(self.negative_phrases)} negative phrases for checking")

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
                    if line and not line.startswith('#'):
                        phrases.append(line)
                return phrases
        except Exception as e:
            logger.error(f"Failed to load negative phrases: {e}")
            return []

    def check_factual_consistency(
        self,
        original: str,
        rewritten: Dict
    ) -> Dict:
        """
        事实一致性检查：逐项比对数字、实体

        Args:
            original: 原文
            rewritten: 改写后的文章 {title, lead, body}

        Returns:
            Dict: {
                score: float,
                issues: List[str],
                numbers_match: bool,
                entities_match: bool
            }
        """
        # 合并改写后的所有文本
        rewritten_text = f"{rewritten['title']} {rewritten['lead']} {rewritten['body']}"

        # 1. 提取和比对数字
        orig_numbers = set(re.findall(r'\d+[.%万亿千百]?\d*', original))
        rewritten_numbers = set(re.findall(r'\d+[.%万亿千百]?\d*', rewritten_text))

        missing_numbers = orig_numbers - rewritten_numbers
        new_numbers = rewritten_numbers - orig_numbers

        # 2. 提取和比对机构名（简单NER）
        org_pattern = r'([\u4e00-\u9fa5]{2,10}(公司|企业|集团|局|厅|部|工厂|中心|专卖局))'
        orig_orgs = set(match[0] for match in re.findall(org_pattern, original))
        rewritten_orgs = set(match[0] for match in re.findall(org_pattern, rewritten_text))

        missing_orgs = orig_orgs - rewritten_orgs

        # 3. 生成问题列表
        issues = []
        if missing_numbers:
            issues.append(f"遗漏数字: {', '.join(list(missing_numbers)[:3])}")
        if new_numbers:
            issues.append(f"新增数字: {', '.join(list(new_numbers)[:3])}")
        if missing_orgs:
            issues.append(f"遗漏机构: {', '.join(list(missing_orgs)[:2])}")

        # 4. 计算一致性分数
        score = 1.0
        if missing_numbers or new_numbers:
            score -= 0.3
        if missing_orgs:
            score -= 0.2

        result = {
            "score": max(0, score),
            "issues": issues,
            "numbers_match": len(missing_numbers) == 0 and len(new_numbers) == 0,
            "entities_match": len(missing_orgs) == 0
        }

        logger.debug(f"Consistency check: score={result['score']}, issues={len(issues)}")
        return result

    def check_style_compliance(
        self,
        rewritten: Dict
    ) -> Dict:
        """
        风格符合度检查

        Args:
            rewritten: 改写后的文章 {title, lead, body}

        Returns:
            Dict: {
                score: float,
                title_length: int,
                lead_length: int,
                terminology_count: int,
                negative_phrases_count: int
            }
        """
        title = rewritten.get('title', '')
        lead = rewritten.get('lead', '')
        body = rewritten.get('body', '')

        title_len = len(title)
        lead_len = len(lead)

        # 1. 标题长度评分 (软失败：线性惩罚)
        # 理想区间 15-30字，偏离越多分数越低
        title_score = 1.0
        if title_len < 15:
            # 少于15字，每少1字扣0.02分，最多扣0.3分
            deviation = 15 - title_len
            title_score = max(0.7, 1.0 - deviation * 0.02)
        elif title_len > 30:
            # 超过30字，每多1字扣0.02分，最多扣0.3分
            deviation = title_len - 30
            title_score = max(0.7, 1.0 - deviation * 0.02)

        # 2. 导语长度评分 (软失败：线性惩罚)
        # 理想区间 60-120字，偏离越多分数越低
        lead_score = 1.0
        if lead_len < 60:
            # 少于60字，每少1字扣0.02分，最多扣0.3分
            deviation = 60 - lead_len
            lead_score = max(0.7, 1.0 - deviation * 0.02)
        elif lead_len > 120:
            # 超过120字，每多1字扣0.02分，最多扣0.3分
            deviation = lead_len - 120
            lead_score = max(0.7, 1.0 - deviation * 0.02)

        # 3. 财经术语覆盖度
        full_text = f"{title} {lead} {body}"
        terminology = self.style_guide.get('terminology', {}).get('financial_terms', [])
        term_count = sum(1 for term in terminology if term in full_text)
        term_score = min(1.0, term_count / 3)  # 至少3个术语

        # 4. 禁用词检查
        negative_count = sum(1 for phrase in self.negative_phrases if phrase in full_text)
        negative_score = max(0, 1.0 - negative_count * 0.1)

        # 5. 综合风格分数
        overall_style_score = (
            0.3 * title_score +
            0.3 * lead_score +
            0.3 * term_score +
            0.1 * negative_score
        )

        result = {
            "score": overall_style_score,
            "title_length": title_len,
            "lead_length": lead_len,
            "terminology_count": term_count,
            "negative_phrases_count": negative_count
        }

        logger.debug(f"Style check: score={result['score']}, title={title_len}, lead={lead_len}")
        return result

    def check_structure(
        self,
        rewritten: Dict
    ) -> Dict:
        """
        结构完整度检查

        Args:
            rewritten: 改写后的文章 {title, lead, body}

        Returns:
            Dict: {
                score: float,
                paragraph_count: int,
                has_background: bool,
                has_action: bool,
                has_result: bool
            }
        """
        body = rewritten.get('body', '')
        paragraphs = [p.strip() for p in body.split('\n') if p.strip()]

        # 获取语篇线索词
        discourse_cues = self.style_guide.get('discourse_cues', {})

        # 检查是否包含各类结构线索
        has_background = any(kw in body for kw in discourse_cues.get('background', []))
        has_action = any(kw in body for kw in discourse_cues.get('action', []))
        has_result = any(kw in body for kw in discourse_cues.get('result', []))

        # 计算结构覆盖度
        coverage = sum([has_background, has_action, has_result])
        structure_score = coverage / 3.0

        # 段落数检查
        para_count = len(paragraphs)
        if para_count < 3 or para_count > 8:
            structure_score *= 0.8

        result = {
            "score": structure_score,
            "paragraph_count": para_count,
            "has_background": has_background,
            "has_action": has_action,
            "has_result": has_result
        }

        logger.debug(f"Structure check: score={result['score']}, paragraphs={para_count}")
        return result

    def check(
        self,
        rewritten: Dict,
        original_text: str
    ) -> Dict:
        """
        主入口：质量检查

        Args:
            rewritten: 改写后的文章 {title, lead, body}
            original_text: 原文

        Returns:
            Dict: {
                overall: float,
                details: {
                    consistency: {...},
                    style: {...},
                    structure: {...}
                }
            }
        """
        logger.info("Starting quality check...")

        # 1. 事实一致性检查
        consistency = self.check_factual_consistency(original_text, rewritten)

        # 2. 风格符合度检查
        style = self.check_style_compliance(rewritten)

        # 3. 结构完整度检查
        structure = self.check_structure(rewritten)

        # 4. 综合评分 (权重：一致性40% + 风格35% + 结构25%)
        overall = (
            0.4 * consistency['score'] +
            0.35 * style['score'] +
            0.25 * structure['score']
        )

        result = {
            "overall": round(overall, 2),
            "details": {
                "consistency": consistency,
                "style": style,
                "structure": structure
            }
        }

        logger.info(f"Quality check completed: overall={result['overall']}")
        return result


# 测试代码
if __name__ == '__main__':
    # 初始化检查器
    checker = XHFQualityChecker()

    # 测试原文
    original_text = """
    近日，山东省烟草专卖局召开全省数字化转型推进会议，
    深入贯彻落实行业高质量发展要求，推动智能制造和数字化管理全面升级。
    今年以来，全省累计投入资金5000万元用于智能化改造项目。
    山东省烟草公司相关负责人表示，数字化转型取得显著成效。
    """

    # 测试改写结果
    rewritten = {
        "title": "山东烟草：5000万元投入推动数字化转型",
        "lead": "今年以来，山东省烟草专卖局以智能制造为抓手，累计投入5000万元推进数字化改造，为行业高质量发展提供有力支撑。",
        "body": """近年来，山东烟草聚焦行业数字化转型需求，持续加大投入力度。

今年推出的智能化改造项目涵盖生产、管理等多个环节，通过引入先进技术实现效能提升。

数据显示，改造后生产效率提升15%，管理成本降低20%。

山东省烟草公司负责人表示，数字化转型为企业发展注入新动能。

下一步，将继续深化数字化应用，推动行业高质量发展。"""
    }

    print("=" * 60)
    print("测试新华财经质量检查器")
    print("=" * 60)

    # 执行检查
    print("\n[1/1] 执行质量检查...")
    scores = checker.check(rewritten, original_text)

    # 输出结果
    print("\n[检查结果]")
    print(f"\n综合得分: {scores['overall']}")

    print("\n1. 事实一致性 (权重40%):")
    cons = scores['details']['consistency']
    print(f"   - 得分: {cons['score']}")
    print(f"   - 数字匹配: {'是' if cons['numbers_match'] else '否'}")
    print(f"   - 实体匹配: {'是' if cons['entities_match'] else '否'}")
    if cons['issues']:
        print(f"   - 问题: {', '.join(cons['issues'])}")

    print("\n2. 风格符合度 (权重35%):")
    style = scores['details']['style']
    print(f"   - 得分: {style['score']:.2f}")
    print(f"   - 标题长度: {style['title_length']} 字")
    print(f"   - 导语长度: {style['lead_length']} 字")
    print(f"   - 术语数量: {style['terminology_count']} 个")
    print(f"   - 禁用词: {style['negative_phrases_count']} 个")

    print("\n3. 结构完整度 (权重25%):")
    struct = scores['details']['structure']
    print(f"   - 得分: {struct['score']:.2f}")
    print(f"   - 段落数: {struct['paragraph_count']} 段")
    print(f"   - 含背景: {'是' if struct['has_background'] else '否'}")
    print(f"   - 含举措: {'是' if struct['has_action'] else '否'}")
    print(f"   - 含结果: {'是' if struct['has_result'] else '否'}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

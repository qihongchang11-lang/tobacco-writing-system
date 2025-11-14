"""
ConstraintDecoder - 约束解码器
实现占位符替换、实体锁定、新数字检查等核心功能
"""

import re
import yaml
from typing import Dict, List, Tuple, Set, Optional
from pathlib import Path
from loguru import logger


class ConstraintDecoder:
    """
    约束解码器 - 确保改写过程中关键信息不变

    核心功能:
    1. 占位符替换 (数字/日期/机构名等)
    2. 白名单实体锁定
    3. 新数字检查
    4. 占位符泄漏检测和修复
    """

    def __init__(self, config_path: str = "config/column_rules.yaml"):
        """初始化解码器"""
        self.config = self._load_config(config_path)

        # 编译正则表达式（性能优化）
        self.patterns = {
            # 数字模式（包括金额、百分比等）
            'NUMBER': re.compile(
                r'\d+(?:\.\d+)?(?:[万亿千百]?元|%|万|亿|千|百|个|项|条|人|次)?'
            ),
            # 日期模式
            'DATE': re.compile(
                r'\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|\d{4}年'
            ),
            # 机构名模式（基于配置）
            'ORG': self._build_org_pattern(),
            # 地名模式
            'LOC': re.compile(r'(?:[\u4e00-\u9fa5]{2,7})(?:省|市|县|区)'),
        }

        # 白名单实体
        self.whitelist_orgs = set(
            self.config.get('whitelists', {}).get('orgs', [])
        )

        # 格式规范化白名单（不算作新数字）
        self.normalize_whitelist = [
            re.compile(pattern)
            for pattern in self.config.get('global', {})
                .get('numeric', {})
                .get('whitelist_patterns', [])
        ]

        logger.info(f"ConstraintDecoder initialized with {len(self.whitelist_orgs)} org whitelist entries")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return {}

    def _build_org_pattern(self) -> re.Pattern:
        """构建机构名正则模式"""
        patterns = self.config.get('whitelists', {}).get('orgs_regex', [])
        if patterns:
            combined = '|'.join(f'({p})' for p in patterns)
            return re.compile(combined)
        # 默认模式
        return re.compile(
            r'[\u4e00-\u9fa5A-Za-z0-9]{2,20}(?:烟草(?:专卖)?局|烟草公司|烟草总公司)'
        )

    def extract_entities(self, text: str) -> List[Tuple[str, str, str]]:
        """
        提取关键实体

        Returns:
            List of (entity_type, value, placeholder_key)
        """
        entities = []

        # 1. 提取日期（优先级最高，避免被数字模式匹配）
        for match in self.patterns['DATE'].finditer(text):
            value = match.group()
            key = f"DATE_{len([e for e in entities if e[0] == 'DATE']) + 1}"
            entities.append(('DATE', value, key))
            logger.debug(f"Extracted date: {value}")

        # 2. 提取数字（排除已被日期匹配的部分）
        extracted_dates = {e[1] for e in entities if e[0] == 'DATE'}
        for match in self.patterns['NUMBER'].finditer(text):
            value = match.group()
            if value not in extracted_dates:
                key = f"NUM_{len([e for e in entities if e[0] == 'NUM']) + 1}"
                entities.append(('NUM', value, key))
                logger.debug(f"Extracted number: {value}")

        # 3. 提取白名单机构名（精确匹配）
        for org in self.whitelist_orgs:
            if org in text:
                key = f"ORG_{len([e for e in entities if e[0] == 'ORG']) + 1}"
                entities.append(('ORG', org, key))
                logger.debug(f"Extracted org (whitelist): {org}")

        # 4. 提取机构名（正则匹配，排除白名单已匹配的）
        extracted_orgs = {e[1] for e in entities if e[0] == 'ORG'}
        for match in self.patterns['ORG'].finditer(text):
            value = match.group()
            if value not in extracted_orgs:
                key = f"ORG_{len([e for e in entities if e[0] == 'ORG']) + 1}"
                entities.append(('ORG', value, key))
                extracted_orgs.add(value)
                logger.debug(f"Extracted org (regex): {value}")

        logger.info(f"Extracted {len(entities)} entities total")
        return entities

    def to_placeholders(
        self,
        text: str,
        entities: List[Tuple[str, str, str]]
    ) -> Tuple[str, Dict[str, str]]:
        """
        将实体替换为占位符

        Returns:
            (text_with_placeholders, mapping)
        """
        result = text
        mapping = {}

        # 按长度降序排序，避免短字符串先被替换导致长字符串匹配失败
        sorted_entities = sorted(entities, key=lambda e: len(e[1]), reverse=True)

        for entity_type, value, key in sorted_entities:
            placeholder = f"{{{{{key}}}}}"
            # 只替换第一次出现（避免重复替换）
            result = result.replace(value, placeholder, 1)
            mapping[key] = value

        logger.info(f"Created {len(mapping)} placeholders")
        return result, mapping

    def restore(self, text: str, mapping: Dict[str, str]) -> str:
        """
        恢复占位符为原始值

        Args:
            text: 包含占位符的文本
            mapping: 占位符到原值的映射

        Returns:
            恢复后的文本
        """
        result = text

        for key, value in mapping.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, value)

        # 检测占位符泄漏
        leak_check = self.detect_placeholder_leak(result)
        if leak_check['has_leak']:
            logger.warning(f"Placeholder leak detected: {leak_check['leaked_placeholders']}")

        return result

    def detect_placeholder_leak(self, text: str) -> Dict:
        """
        检测占位符是否泄漏到输出中

        Returns:
            {
                'has_leak': bool,
                'leaked_placeholders': List[str]
            }
        """
        # 查找所有 {{...}} 模式
        pattern = re.compile(r'\{\{([A-Z_0-9]+)\}\}')
        matches = pattern.findall(text)

        return {
            'has_leak': len(matches) > 0,
            'leaked_placeholders': matches
        }

    def check_new_numbers(
        self,
        original_text: str,
        rewritten_text: str
    ) -> Tuple[bool, List[str]]:
        """
        检查改写后是否引入了新的数字

        Returns:
            (is_valid, new_numbers)
        """
        # 提取原文中的所有数字
        original_numbers = set()
        for match in self.patterns['NUMBER'].finditer(original_text):
            num = match.group()
            original_numbers.add(num)
            # 同时添加规范化版本
            original_numbers.add(num.replace(',', ''))

        # 提取改写后的所有数字
        rewritten_numbers = set()
        for match in self.patterns['NUMBER'].finditer(rewritten_text):
            num = match.group()
            rewritten_numbers.add(num)

        # 检查新数字
        new_numbers = []
        for num in rewritten_numbers:
            # 如果数字不在原文中
            if num not in original_numbers:
                # 检查是否在格式规范化白名单中
                is_normalized = False
                for pattern in self.normalize_whitelist:
                    if pattern.match(num):
                        is_normalized = True
                        break

                if not is_normalized:
                    new_numbers.append(num)

        is_valid = len(new_numbers) == 0

        if not is_valid:
            logger.warning(f"New numbers detected: {new_numbers}")

        return is_valid, new_numbers

    def verify_entities(
        self,
        original_text: str,
        rewritten_text: str,
        mapping: Dict[str, str]
    ) -> Tuple[bool, List[str], Dict]:
        """
        综合验证：检查关键实体是否完整保留

        Returns:
            (is_valid, missing_entities, audit_info)
        """
        missing = []

        # 1. 检查映射中的实体是否都在改写后文本中
        for key, value in mapping.items():
            if value not in rewritten_text:
                missing.append(value)
                logger.warning(f"Missing entity: {value}")

        # 2. 检查新数字
        has_no_new_numbers, new_numbers = self.check_new_numbers(
            original_text,
            rewritten_text
        )

        # 3. 检查占位符泄漏
        leak_info = self.detect_placeholder_leak(rewritten_text)

        audit_info = {
            'entities_locked': {
                'dates': [v for k, v in mapping.items() if k.startswith('DATE')],
                'numbers': [v for k, v in mapping.items() if k.startswith('NUM')],
                'orgs': [v for k, v in mapping.items() if k.startswith('ORG')],
            },
            'missing_entities': missing,
            'new_numbers_detected': new_numbers,
            'placeholder_leak': leak_info,
            'placeholder_leak_fixed': leak_info['has_leak']
        }

        is_valid = (
            len(missing) == 0 and
            has_no_new_numbers and
            not leak_info['has_leak']
        )

        return is_valid, missing, audit_info


if __name__ == "__main__":
    # 测试代码
    from loguru import logger

    decoder = ConstraintDecoder()

    test_text = """
    2024年10月15日,国家烟草专卖局在北京召开工作会议。会议指出,
    前三季度行业销售额达到15.6亿元,同比增长8.5%,完成全年目标的75%。
    某省烟草公司推进数字化改造,投入资金1.2万元,取得显著成效。
    """

    print("="*50)
    print("原文:")
    print(test_text)
    print("\n" + "="*50)

    # 提取实体
    entities = decoder.extract_entities(test_text)
    print(f"\n提取的实体 ({len(entities)} 个):")
    for etype, value, key in entities:
        print(f"  [{etype}] {value} -> {key}")

    # 转换为占位符
    text_ph, mapping = decoder.to_placeholders(test_text, entities)
    print("\n" + "="*50)
    print("占位符文本:")
    print(text_ph)

    # 恢复
    restored = decoder.restore(text_ph, mapping)
    print("\n" + "="*50)
    print("恢复后:")
    print(restored)

    # 验证
    is_valid, missing, audit = decoder.verify_entities(test_text, restored, mapping)
    print("\n" + "="*50)
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    print(f"审计信息: {audit}")
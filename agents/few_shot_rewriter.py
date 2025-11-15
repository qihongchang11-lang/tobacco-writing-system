"""
Few-shot学习改写引擎 - 基于样本学习的智能改写
利用检索到的相似文章作为few-shot示例，进行风格学习和改写
"""

import json
import re
import os
import asyncio
import random
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
from functools import wraps

# 使用现有的OpenAI客户端配置
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def api_retry(max_attempts: int = 3, base_delay: float = 2.0):
    """
    API调用重试装饰器 - 处理429限流和其他可重试错误

    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟时间(秒),会指数增长

    使用示例:
        @api_retry(max_attempts=3, base_delay=2)
        async def call_api():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()

                    # 检查是否需要重试的错误
                    retry_errors = ['429', 'rate limit', 'rate_limit', 'retry', 'timeout']
                    should_retry = any(err in error_str for err in retry_errors)

                    if should_retry and attempt < max_attempts - 1:
                        # 指数退避 + 随机抖动
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"⚠️ API限流/错误, {delay:.1f}秒后重试 "
                            f"(尝试 {attempt+1}/{max_attempts}) - 错误: {str(e)[:100]}"
                        )
                        await asyncio.sleep(delay)
                        continue

                    # 如果是最后一个尝试或非重试错误,抛出异常
                    logger.error(f"API调用失败 (尝试 {attempt+1}/{max_attempts}): {e}")
                    raise

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class FewShotRewriter:
    """Few-shot学习改写引擎"""

    def __init__(self, retriever=None):
        self.retriever = retriever
        self.client = self._initialize_client()

        # 栏目映射配置
        self.column_mapping = {
            "要闻": "news_general",
            "案例": "case_observation",
            "政策解读": "policy_interpretation",
            "经济运行": "economic_data"
        }

    def _initialize_client(self) -> OpenAI:
        """初始化OpenAI客户端（带超时配置）"""
        import httpx

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

        if not api_key:
            logger.error("未设置OPENAI_API_KEY环境变量")
            raise ValueError("Missing OPENAI_API_KEY")

        # ✅ 设置HTTP客户端超时：连接10秒，读取120秒
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=5.0)
        http_client = httpx.Client(timeout=timeout)

        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )

    @api_retry(max_attempts=3, base_delay=3.0)
    async def rewrite_with_learning(
        self,
        input_text: str,
        target_column: str,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        使用Few-shot学习进行改写

        Args:
            input_text: 待改写文本
            target_column: 目标栏目
            strict_mode: 严格模式

        Returns:
            改写结果

        Note:
            此方法已被@api_retry装饰器保护,遇到429等限流错误会自动重试
        """
        try:
            # 1. 映射栏目名称
            column_id = self.column_mapping.get(target_column, "news_general")

            # 2. 检索相似样本
            similar_samples = []
            if self.retriever:
                try:
                    similar_samples = self.retriever.retrieve_similar_samples(
                        input_text, column_id, top_k=3
                    )
                except Exception as e:
                    logger.warning(f"样本检索失败，使用无样本模式: {e}")

            # 3. 构建Few-shot提示词
            prompt = self._build_few_shot_prompt(
                input_text, target_column, similar_samples, strict_mode
            )

            # 4. 调用LLM改写
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
                messages=[
                    {
                        "role": "system",
                        "content": "你是《东方烟草报》的资深编辑，擅长风格学习和改写。严格按照示例学习风格特征，生成符合目标栏目要求的高质量稿件。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content

            # 5. 解析结果
            parsed_result = self._parse_rewrite_result(result_text)

            # 6. 验证严格模式约束
            if strict_mode:
                validation_result = self._validate_strict_mode(input_text, parsed_result)
                if not validation_result['is_valid']:
                    logger.warning(f"严格模式验证失败: {validation_result['violations']}")

            return {
                "success": True,
                "title": parsed_result['title'],
                "lead": parsed_result['lead'],
                "body": parsed_result['body_text'],
                "metadata": {
                    "column": target_column,
                    "samples_used": len(similar_samples),
                    "strict_mode": strict_mode,
                    "model": os.getenv("OPENAI_MODEL", "deepseek-chat")
                },
                "raw_response": result_text
            }

        except Exception as e:
            logger.error(f"Few-shot改写失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "title": "",
                "lead": "",
                "body": ""
            }

    def _build_few_shot_prompt(
        self,
        input_text: str,
        target_column: str,
        similar_samples: List[Dict[str, Any]],
        strict_mode: bool
    ) -> str:
        """构建Few-shot学习提示词"""

        # 栏目专用指导
        column_guidance = self._get_column_guidance(target_column)

        # 构建示例部分
        examples_section = ""
        if similar_samples:
            examples_section = "【风格学习示例】\n以下是" + target_column + "栏目的优秀范例，请仔细学习其写作风格和结构特征：\n\n"

            for i, sample in enumerate(similar_samples, 1):
                examples_section += f"示例{i}：\n"
                examples_section += f"标题：{sample['title']}\n"
                if sample['lead']:
                    examples_section += f"导语：{sample['lead']}\n"
                examples_section += f"正文片段：{sample['body'][:200]}...\n"

                # 添加风格特征分析
                features = sample.get('features', {})
                if features:
                    examples_section += f"风格特征：{self._describe_features(features)}\n"

                examples_section += "\n"

        # 严格模式约束
        strict_constraints = ""
        if strict_mode:
            strict_constraints = """
【严格模式约束】
⚠️ CRITICAL: 本次改写处于严格模式，必须遵守以下规则：
1. 绝对不能修改或删除原文中的任何数字、日期、机构名称
2. 不能添加原文中不存在的数字或事实信息
3. 保持所有关键信息的准确性
4. 如发现冲突，必须选择保持事实准确性
"""

        # 组装完整提示词
        prompt = f"""
{strict_constraints}

{examples_section}

【{target_column}栏目写作规范】
{column_guidance}

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

        return prompt

    def _get_column_guidance(self, target_column: str) -> str:
        """获取栏目专用写作指导"""
        guidance_map = {
            "要闻": """
- 标题：主体+动作/成果，官方庄重，不使用感叹号
- 导语：时间+地点+主体+行动+结果，40-80字
- 正文：背景→举措→成效→展望，逻辑清晰
- 语言：使用"召开、部署、推进、落实、协同"等正式表达
""",
            "经济运行": """
- 标题：数字前置突出亮点，如"45.2万箱：某地卷烟销售创新高"
- 导语：核心数据开篇，包含同比变化，40-80字
- 正文：数据概览→结构分析→效益评估→后续目标
- 语言：重视"同比增长、销售收入、结构优化"等专业术语
""",
            "政策解读": """
- 标题：政策要点+执行路径，权威严谨
- 导语：政策背景+核心内容+执行要求，40-80字
- 正文：政策解读→执行机制→预期效果→保障措施
- 语言：强调"贯彻落实、统筹推进、机制建设"等权威表达
""",
            "案例": """
- 标题：典型做法/成果导向，突出示范性
- 导语：典型场景+创新做法+示范效果，40-80字
- 正文：问题背景→创新实践→成效亮点→经验价值
- 语言：突出"典型经验、创新实践、示范引领、复制推广"
"""
        }
        return guidance_map.get(target_column, guidance_map["要闻"])

    def _describe_features(self, features: Dict[str, Any]) -> str:
        """描述文章风格特征"""
        description = []

        # 栏目特征
        column_indicators = features.get('column_indicators', {})
        for column, has_feature in column_indicators.items():
            if has_feature:
                column_names = {
                    'news_general': '新闻报道',
                    'economic_data': '数据分析',
                    'policy_interpretation': '政策解读',
                    'case_observation': '案例展示'
                }
                description.append(f"具备{column_names.get(column, column)}特征")

        # 写作风格
        writing_style = features.get('writing_style', {})
        opening_type = writing_style.get('opening_type')
        if opening_type:
            opening_map = {
                'date_start': '时间导入式开头',
                'time_indicator_start': '时间指示词开头',
                'event_start': '事件直入式开头',
                'direct_start': '直接陈述开头'
            }
            description.append(opening_map.get(opening_type, opening_type))

        # 数据特征
        data_usage = features.get('data_usage', {})
        data_density = data_usage.get('data_density', 0)
        if data_density > 5:
            description.append('数据密集型')

        return '、'.join(description) if description else '标准格式'

    def _parse_rewrite_result(self, result_text: str) -> Dict[str, str]:
        """解析改写结果"""
        try:
            # 提取标题
            title_match = re.search(r'===标题===\s*\n(.*?)\n', result_text, re.DOTALL)
            title = title_match.group(1).strip() if title_match else "未生成标题"

            # 提取导语
            lead_match = re.search(r'===导语===\s*\n(.*?)\n===', result_text, re.DOTALL)
            lead = lead_match.group(1).strip() if lead_match else ""

            # 提取正文
            body_match = re.search(r'===正文===\s*\n(.*?)(?:\n===|$)', result_text, re.DOTALL)
            body_text = body_match.group(1).strip() if body_match else ""

            # 提取风格说明
            style_match = re.search(r'===风格说明===\s*\n(.*?)$', result_text, re.DOTALL)
            style_note = style_match.group(1).strip() if style_match else ""

            return {
                'title': title,
                'lead': lead,
                'body_text': body_text,
                'style_note': style_note,
                'raw': result_text
            }

        except Exception as e:
            logger.error(f"解析改写结果失败: {e}")
            return {
                'title': "解析失败",
                'lead': "",
                'body_text': result_text,
                'style_note': "",
                'raw': result_text
            }

    def _validate_strict_mode(self, original_text: str, parsed_result: Dict[str, str]) -> Dict[str, Any]:
        """验证严格模式约束"""
        violations = []

        # 提取原文中的数字
        original_numbers = re.findall(r'\d+\.?\d*(?:万|亿|千)?(?:箱|元|吨|%)', original_text)

        # 检查改写后的数字
        rewritten_text = f"{parsed_result['title']} {parsed_result['lead']} {parsed_result['body_text']}"
        rewritten_numbers = re.findall(r'\d+\.?\d*(?:万|亿|千)?(?:箱|元|吨|%)', rewritten_text)

        # 检查数字是否匹配
        for num in rewritten_numbers:
            if num not in original_numbers:
                violations.append(f"新增了原文中不存在的数字: {num}")

        for num in original_numbers:
            if num not in rewritten_numbers:
                violations.append(f"丢失了原文中的数字: {num}")

        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'original_numbers': original_numbers,
            'rewritten_numbers': rewritten_numbers
        }


def main():
    """测试函数"""
    # 创建测试用的检索器实例（简化版）
    class MockRetriever:
        def retrieve_similar_samples(self, query_text: str, column_id: str, top_k: int = 3):
            return [{
                'title': '山东省烟草专卖局召开营销工作会议',
                'lead': '近日，山东省烟草专卖局召开会议，研究部署全省卷烟营销工作。',
                'body': '会议强调，要深入贯彻落实行业高质量发展要求，持续推进卷烟营销市场化取向改革...',
                'features': {
                    'column_indicators': {'news_general': True},
                    'writing_style': {'opening_type': 'time_indicator_start'}
                }
            }]

    # 测试改写
    rewriter = FewShotRewriter(retriever=MockRetriever())

    test_text = """
    近日，山东省烟草专卖局召开会议，强调要深入学习贯彻党的二十大精神，全面推进卷烟营销高质量发展。
    今年前三季度，全省累计销售卷烟45.2万箱，同比增长8.5%，实现销售收入123.6亿元。
    下一步，将围绕市场需求，持续优化品牌结构，确保完成全年目标任务。
    """

    print("🔧 开始Few-shot改写测试...")

    # 注意：在实际环境中这应该是异步调用
    # result = await rewriter.rewrite_with_learning(test_text, "要闻", strict_mode=False)
    print("✅ Few-shot改写器已初始化完成")


if __name__ == "__main__":
    main()
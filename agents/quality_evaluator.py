"""
质量评估Agent
评估最终稿件的质量，提供评分和改进建议
"""

import re
from typing import Dict, Any
from utils import QualityMetrics, QualityEvaluation, AgentResponse, count_words
from .base_agent import LLMAgent

class QualityEvaluatorAgent(LLMAgent):
    """质量评估Agent"""
    
    def __init__(self):
        super().__init__(
            name="QualityEvaluator",
            description="评估稿件质量，提供多维度评分和改进建议"
        )
    
    def get_system_prompt(self) -> str:
        return """你是专业的新闻稿件质量评估专家，负责从多个维度评估文章质量。
        
评估维度：
1. 标题完整性（是否简洁明了、突出重点）
2. 导语质量（是否概括全文、回答关键问题）
3. 内容连贯性（逻辑是否清晰、过渡是否自然）
4. 风格一致性（是否符合官方媒体风格）
5. 事实准确性（信息是否准确、表述是否规范）
6. 格式规范性（结构是否标准、格式是否统一）

请客观评估，给出0-1之间的评分。"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理质量评估"""
        try:
            export_info = input_data.get("export_info")
            fact_check_result = input_data.get("fact_check_result")
            
            if not fact_check_result:
                return AgentResponse(
                    success=False,
                    message="缺少事实校对结果",
                    agent_name=self.name
                )
            
            content = fact_check_result.corrected_content
            
            # 执行质量评估
            metrics = await self._evaluate_quality(content, fact_check_result.issues)
            
            # 生成改进建议
            suggestions = self._generate_suggestions(metrics, fact_check_result.issues)
            
            # 判断是否通过质量检查
            passed = metrics.overall_score >= 0.7
            
            quality_evaluation = QualityEvaluation(
                metrics=metrics,
                suggestions=suggestions,
                passed=passed
            )
            
            return AgentResponse(
                success=True,
                message="质量评估完成",
                data={
                    "quality_evaluation": quality_evaluation,
                    "final_content": content
                },
                agent_name=self.name
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"质量评估失败: {str(e)}",
                agent_name=self.name
            )
    
    async def _evaluate_quality(self, content: str, issues: list) -> QualityMetrics:
        """评估文章质量"""
        
        # 解析文章结构
        lines = content.split('\n\n')
        title = lines[0].strip() if lines else ""
        lead = lines[1].strip() if len(lines) > 1 else ""
        body_paragraphs = lines[2:] if len(lines) > 2 else []
        
        # 评估标题完整性
        title_completeness = self._evaluate_title_completeness(title)
        
        # 评估导语质量
        lead_quality = self._evaluate_lead_quality(lead)
        
        # 评估内容连贯性
        content_coherence = self._evaluate_content_coherence(body_paragraphs)
        
        # 评估风格一致性
        style_consistency = await self._evaluate_style_consistency(content)
        
        # 评估事实准确性（基于校对结果）
        factual_accuracy = max(0.0, 1.0 - len([i for i in issues if i.severity == "high"]) * 0.2)
        
        # 评估格式规范性
        format_compliance = self._evaluate_format_compliance(title, lead, body_paragraphs)
        
        # 计算综合评分
        overall_score = (
            title_completeness * 0.15 +
            lead_quality * 0.20 +
            content_coherence * 0.20 +
            style_consistency * 0.20 +
            factual_accuracy * 0.15 +
            format_compliance * 0.10
        )
        
        return QualityMetrics(
            title_completeness=title_completeness,
            lead_quality=lead_quality,
            content_coherence=content_coherence,
            style_consistency=style_consistency,
            factual_accuracy=factual_accuracy,
            format_compliance=format_compliance,
            overall_score=overall_score
        )
    
    def _evaluate_title_completeness(self, title: str) -> float:
        """评估标题完整性"""
        if not title:
            return 0.0
        
        score = 0.7  # 基础分
        
        # 长度适中加分
        if 10 <= len(title) <= 25:
            score += 0.2
        
        # 包含主要信息加分
        if any(word in title for word in ["取得", "实现", "推进", "开展", "召开"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_lead_quality(self, lead: str) -> float:
        """评估导语质量"""
        if not lead:
            return 0.0
        
        score = 0.6  # 基础分
        
        # 长度适中
        if 50 <= len(lead) <= 120:
            score += 0.2
        
        # 包含关键信息
        if any(word in lead for word in ["日前", "记者", "获悉", "近日"]):
            score += 0.1
        
        # 概括性强
        if "。" in lead and len(lead.split("。")) <= 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_content_coherence(self, body_paragraphs: list) -> float:
        """评估内容连贯性"""
        if not body_paragraphs:
            return 0.5
        
        score = 0.7  # 基础分
        
        # 段落数量合理
        if 2 <= len(body_paragraphs) <= 6:
            score += 0.1
        
        # 段落长度适中
        appropriate_length = sum(1 for p in body_paragraphs if 30 <= len(p) <= 150)
        if appropriate_length >= len(body_paragraphs) * 0.8:
            score += 0.1
        
        # 过渡词使用
        transition_words = ["同时", "此外", "另外", "与此同时", "据了解"]
        has_transitions = any(word in " ".join(body_paragraphs) for word in transition_words)
        if has_transitions:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _evaluate_style_consistency(self, content: str) -> float:
        """评估风格一致性"""
        prompt = f"""请评估以下文章的语言风格是否符合中国烟草报等官方媒体的要求：

{content[:500]}...

评估要点：
1. 用词是否正式、规范
2. 语气是否客观、权威
3. 表达是否简洁、有力
4. 是否体现官方媒体特色

请给出0-10的评分，只返回数字。"""
        
        try:
            response = await self.process_with_llm(prompt)
            score_match = re.search(r'(\d+(?:\.\d+)?)', response)
            if score_match:
                score = float(score_match.group(1)) / 10
                return min(max(score, 0.0), 1.0)
        except:
            pass
        
        return 0.8  # 默认评分
    
    def _evaluate_format_compliance(self, title: str, lead: str, body_paragraphs: list) -> float:
        """评估格式规范性"""
        score = 0.0
        
        # 有标题
        if title:
            score += 0.3
        
        # 有导语
        if lead:
            score += 0.3
        
        # 有正文
        if body_paragraphs:
            score += 0.4
        
        return score
    
    def _generate_suggestions(self, metrics: QualityMetrics, issues: list) -> list:
        """生成改进建议"""
        suggestions = []
        
        if metrics.title_completeness < 0.8:
            suggestions.append("建议优化标题，使其更加简洁明了，突出核心信息")
        
        if metrics.lead_quality < 0.8:
            suggestions.append("建议改进导语，确保概括全文要点，回答关键问题")
        
        if metrics.content_coherence < 0.8:
            suggestions.append("建议优化段落结构，增强逻辑连贯性")
        
        if metrics.style_consistency < 0.8:
            suggestions.append("建议调整语言风格，使其更符合官方媒体要求")
        
        if metrics.factual_accuracy < 0.9:
            suggestions.append("建议仔细核查事实信息，确保准确性")
        
        # 基于事实校对问题的建议
        high_issues = [i for i in issues if i.severity == "high"]
        if high_issues:
            suggestions.append(f"发现{len(high_issues)}个高优先级问题，建议优先处理")
        
        return suggestions
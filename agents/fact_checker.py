"""
事实校对Agent（简化版）
检查文章中的术语使用、数据一致性和禁用词
"""

import re
from typing import Dict, Any, List
from utils import FactCheckResult, FactCheckIssue, AgentResponse
from .base_agent import LLMAgent

class FactCheckerAgent(LLMAgent):
    """事实校对Agent"""
    
    def __init__(self):
        super().__init__(
            name="FactChecker",
            description="检查文章的事实准确性、术语规范和内容合规性"
        )
        
        # 禁用词列表
        self.forbidden_words = [
            "惊人", "震撼", "轰动", "爆炸性", "史无前例",
            "空前绝后", "绝无仅有", "万无一失", "百分之百"
        ]
        
        # 标准术语映射
        self.terminology_map = {
            "卷烟厂": "卷烟工业企业",
            "烟厂": "卷烟工业企业", 
            "专卖店": "烟草专卖零售店",
            "零售店": "零售客户",
            "烟草局": "烟草专卖局"
        }
    
    def get_system_prompt(self) -> str:
        return """你是专业的事实校对专家，负责检查文章的准确性和规范性。请仔细检查并指出问题。"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理事实校对"""
        try:
            style_result = input_data.get("style_rewrite_result")
            if not style_result:
                return AgentResponse(
                    success=False,
                    message="缺少风格改写结果",
                    agent_name=self.name
                )
            
            # 获取完整内容
            full_content = f"{style_result.rewritten_title}\n\n{style_result.rewritten_lead}\n\n"
            full_content += "\n\n".join(style_result.rewritten_body)
            if style_result.rewritten_conclusion:
                full_content += f"\n\n{style_result.rewritten_conclusion}"
            
            # 执行各种检查
            issues = []
            issues.extend(self._check_forbidden_words(full_content))
            issues.extend(self._check_terminology(full_content))
            issues.extend(await self._check_with_llm(full_content))
            
            # 生成校对后内容（简化处理）
            corrected_content = self._apply_corrections(full_content, issues)
            
            # 计算整体评分
            overall_score = max(0.0, 1.0 - len(issues) * 0.1)
            
            fact_check_result = FactCheckResult(
                issues=issues,
                corrected_content=corrected_content,
                overall_score=overall_score
            )
            
            return AgentResponse(
                success=True,
                message="事实校对完成",
                data={"fact_check_result": fact_check_result},
                agent_name=self.name
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"事实校对失败: {str(e)}",
                agent_name=self.name
            )
    
    def _check_forbidden_words(self, content: str) -> List[FactCheckIssue]:
        """检查禁用词"""
        issues = []
        for word in self.forbidden_words:
            if word in content:
                issues.append(FactCheckIssue(
                    issue_type="forbidden_words",
                    location=f"包含禁用词: {word}",
                    original_text=word,
                    suggested_correction="删除或替换为合适的表达",
                    severity="medium",
                    explanation=f"'{word}'属于夸张表述，不符合客观报道要求"
                ))
        return issues
    
    def _check_terminology(self, content: str) -> List[FactCheckIssue]:
        """检查术语规范"""
        issues = []
        for incorrect, correct in self.terminology_map.items():
            if incorrect in content:
                issues.append(FactCheckIssue(
                    issue_type="terminology",
                    location=f"术语使用: {incorrect}",
                    original_text=incorrect,
                    suggested_correction=correct,
                    severity="high",
                    explanation=f"应使用标准术语'{correct}'"
                ))
        return issues
    
    async def _check_with_llm(self, content: str) -> List[FactCheckIssue]:
        """使用LLM进行深度检查"""
        prompt = f"""请检查以下文章内容是否存在事实性错误、逻辑不一致或表述不当的问题：

{content}

请重点关注：
1. 数据的一致性
2. 时间逻辑的合理性  
3. 因果关系的正确性
4. 专业表述的准确性

如发现问题，请指出具体位置和修改建议。如无明显问题，回复"未发现明显问题"。"""
        
        try:
            response = await self.process_with_llm(prompt)
            
            if "未发现明显问题" in response:
                return []
            
            # 简化处理LLM响应
            return [FactCheckIssue(
                issue_type="consistency",
                location="LLM检查发现",
                original_text="见详细说明",
                suggested_correction="根据LLM建议修改",
                severity="low",
                explanation=response[:200] + "..." if len(response) > 200 else response
            )]
            
        except Exception as e:
            self.logger.warning(f"LLM事实检查失败: {e}")
            return []
    
    def _apply_corrections(self, content: str, issues: List[FactCheckIssue]) -> str:
        """应用修正建议"""
        corrected = content
        
        for issue in issues:
            if issue.issue_type == "terminology" and issue.suggested_correction:
                corrected = corrected.replace(issue.original_text, issue.suggested_correction)
        
        return corrected
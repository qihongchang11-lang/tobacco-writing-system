"""
风格改写Agent
将文章改写为符合中国烟草报风格的专业稿件
这是系统的核心组件，负责语言风格的转换和润色
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from utils import ArticleGenre, StructureInfo, StyleRewriteResult, AgentResponse
from .base_agent import LLMAgent

class StyleRewriterAgent(LLMAgent):
    """风格改写Agent"""
    
    def __init__(self):
        super().__init__(
            name="StyleRewriter",
            description="将文章改写为符合中国烟草报风格的专业稿件，包括用词、句式、表达方式的全面优化"
        )
        
        # 中国烟草报语言风格特征
        self.style_characteristics = {
            "formal_tone": "正式、严谨、权威",
            "sentence_structure": "以陈述句为主，适当使用排比、对偶",
            "vocabulary": "准确、规范、专业",
            "expression_style": "客观、平实、有力",
            "paragraph_transition": "自然、流畅、逻辑清晰"
        }
        
        # 常用表达转换规则
        self.expression_conversions = {
            # 时间表达
            "最近": "近期", "不久前": "日前", "刚刚": "近日",
            # 程度表达
            "非常": "十分", "特别": "尤其", "很多": "大量",
            # 动作表达
            "做好": "抓好", "搞好": "做好", "弄清": "搞清",
            # 结果表达
            "效果好": "成效显著", "进展快": "进展顺利", "变化大": "变化明显"
        }
        
        # 标准句式模板
        self.sentence_templates = {
            "achievement": [
                "{主体}在{方面}取得{成果}",
                "{主体}的{工作}呈现{特点}",
                "通过{措施}，{主体}实现了{目标}"
            ],
            "process": [
                "{主体}坚持{原则}，{具体做法}",
                "围绕{目标}，{主体}{具体行动}",
                "为{目的}，{主体}采取{措施}"
            ],
            "evaluation": [
                "{事件}标志着{意义}",
                "{成果}体现了{价值}",
                "{做法}展现了{精神}"
            ]
        }
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是中国烟草报的资深编辑，专门负责稿件的风格改写和语言润色。

你的任务是将提供的文章改写为符合中国烟草报风格的专业稿件。

中国烟草报的语言风格特点：

1. 用词特征：
   - 准确规范：使用标准的新闻用语和行业术语
   - 庄重正式：避免口语化表达，采用书面语
   - 简洁有力：字句精炼，表达准确

2. 句式特征：
   - 以陈述句为主，语气肯定
   - 适当使用排比、对偶增强语势
   - 句长适中，结构清晰

3. 表达方式：
   - 客观平实：以事实为准，避免过度修饰
   - 逻辑清晰：层次分明，前后呼应
   - 积极向上：突出成就和进步

4. 段落特点：
   - 主题突出，一段一意
   - 过渡自然，逻辑连贯
   - 长短搭配，节奏明快

5. 行业特色：
   - 熟悉烟草行业术语和表达习惯
   - 体现国有企业的责任担当
   - 符合官方媒体的表达规范

改写要求：
1. 保持原文核心信息和事实准确性
2. 优化语言表达，提升文章质量
3. 统一文风，符合媒体标准
4. 增强可读性和感染力

请逐段进行改写，并说明主要修改内容。"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理风格改写"""
        try:
            structure_info = input_data.get("structure_info")
            genre = input_data.get("genre", ArticleGenre.NEWS)
            
            if not structure_info:
                return AgentResponse(
                    success=False,
                    message="缺少文章结构信息",
                    agent_name=self.name
                )
            
            # 执行风格改写
            rewrite_result = await self._rewrite_article_style(structure_info, genre)
            
            return AgentResponse(
                success=True,
                message="风格改写完成",
                data={
                    "style_rewrite_result": rewrite_result,
                    "original_structure": structure_info
                },
                agent_name=self.name
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"风格改写失败: {str(e)}",
                agent_name=self.name
            )
    
    async def _rewrite_article_style(self, structure_info: StructureInfo, 
                                   genre: ArticleGenre) -> StyleRewriteResult:
        """执行文章风格改写"""
        
        # 改写标题
        rewritten_title = await self._rewrite_title(structure_info.title, genre)
        
        # 改写导语
        rewritten_lead = await self._rewrite_lead(structure_info.lead, genre)
        
        # 改写正文
        rewritten_body = await self._rewrite_body_paragraphs(structure_info.body_paragraphs, genre)
        
        # 改写结尾
        rewritten_conclusion = None
        if structure_info.conclusion:
            rewritten_conclusion = await self._rewrite_conclusion(structure_info.conclusion, genre)
        
        # 生成风格改写说明
        style_changes = self._generate_style_changes_summary(
            structure_info, rewritten_title, rewritten_lead, rewritten_body, rewritten_conclusion
        )
        
        return StyleRewriteResult(
            rewritten_title=rewritten_title,
            rewritten_lead=rewritten_lead,
            rewritten_body=rewritten_body,
            rewritten_conclusion=rewritten_conclusion,
            style_changes=style_changes
        )
    
    async def _rewrite_title(self, original_title: str, genre: ArticleGenre) -> str:
        """改写标题"""
        if not original_title or not original_title.strip():
            return original_title
        
        # 获取标题相关的知识库信息
        title_knowledge = await self.search_knowledge_base(
            query=f"标题写作 {genre.value} 风格",
            category="style_cards",
            n_results=2
        )
        
        knowledge_context = self.extract_knowledge_context(title_knowledge)
        
        prompt = f"""请改写以下标题，使其符合中国烟草报的风格标准：

原标题：{original_title}
文章体裁：{genre.value}

改写要求：
1. 简洁明了，突出核心信息
2. 用词准确，避免口语化
3. 长度适中（15-25字）
4. 符合{genre.value}体裁特点

参考知识：
{knowledge_context}

请只返回改写后的标题，不要包含其他解释。"""
        
        try:
            rewritten_title = await self.process_with_llm(prompt, knowledge_context)
            
            # 清理结果
            rewritten_title = rewritten_title.strip()
            
            # 如果改写结果不合理，返回原标题
            if not rewritten_title or len(rewritten_title) > 35 or len(rewritten_title) < 5:
                return original_title
            
            return rewritten_title
            
        except Exception as e:
            self.logger.warning(f"标题改写失败，保留原标题: {e}")
            return original_title
    
    async def _rewrite_lead(self, original_lead: str, genre: ArticleGenre) -> str:
        """改写导语"""
        if not original_lead or not original_lead.strip():
            return original_lead
        
        # 获取导语写作知识
        lead_knowledge = await self.search_knowledge_base(
            query=f"导语写作 {genre.value} 要求",
            category="style_cards",
            n_results=2
        )
        
        # 获取句式模板
        pattern_knowledge = await self.search_knowledge_base(
            query="导语 开头句式",
            category="sentence_patterns",
            n_results=3
        )
        
        combined_knowledge = lead_knowledge + pattern_knowledge
        knowledge_context = self.extract_knowledge_context(combined_knowledge)
        
        prompt = f"""请改写以下导语，使其符合中国烟草报的风格要求：

原导语：{original_lead}
文章体裁：{genre.value}

改写要求：
1. 开门见山，概括核心信息
2. 语言客观、准确、有力
3. 长度适中（60-120字）
4. 符合{genre.value}体裁的导语特点

参考知识：
{knowledge_context}

请只返回改写后的导语，保持简洁。"""
        
        try:
            rewritten_lead = await self.process_with_llm(prompt, knowledge_context)
            rewritten_lead = rewritten_lead.strip()
            
            # 应用表达转换规则
            rewritten_lead = self._apply_expression_conversion(rewritten_lead)
            
            if not rewritten_lead or len(rewritten_lead) < 20:
                return original_lead
            
            return rewritten_lead
            
        except Exception as e:
            self.logger.warning(f"导语改写失败，保留原导语: {e}")
            return original_lead
    
    async def _rewrite_body_paragraphs(self, original_paragraphs: List[str], 
                                      genre: ArticleGenre) -> List[str]:
        """改写正文段落"""
        if not original_paragraphs:
            return original_paragraphs
        
        rewritten_paragraphs = []
        
        for i, paragraph in enumerate(original_paragraphs):
            if not paragraph or not paragraph.strip():
                rewritten_paragraphs.append(paragraph)
                continue
            
            try:
                rewritten_paragraph = await self._rewrite_single_paragraph(
                    paragraph, i + 1, len(original_paragraphs), genre
                )
                rewritten_paragraphs.append(rewritten_paragraph)
                
            except Exception as e:
                self.logger.warning(f"第{i+1}段改写失败，保留原文: {e}")
                rewritten_paragraphs.append(paragraph)
        
        return rewritten_paragraphs
    
    async def _rewrite_single_paragraph(self, paragraph: str, paragraph_num: int, 
                                       total_paragraphs: int, genre: ArticleGenre) -> str:
        """改写单个段落"""
        
        # 获取句式和表达知识
        sentence_knowledge = await self.search_knowledge_base(
            query="句式 表达方式 过渡",
            category="sentence_patterns",
            n_results=2
        )
        
        knowledge_context = self.extract_knowledge_context(sentence_knowledge)
        
        # 确定段落在文章中的位置和功能
        position_context = self._get_paragraph_position_context(paragraph_num, total_paragraphs)
        
        prompt = f"""请改写以下段落，使其符合中国烟草报的语言风格：

原段落：{paragraph}
段落位置：{position_context}
文章体裁：{genre.value}

改写要求：
1. 保持原意，优化表达
2. 使用规范的书面语
3. 句式多样，长短搭配
4. 逻辑清晰，过渡自然
5. 体现官方媒体的庄重感

参考知识：
{knowledge_context}

请只返回改写后的段落内容。"""
        
        rewritten_paragraph = await self.process_with_llm(prompt, knowledge_context)
        rewritten_paragraph = rewritten_paragraph.strip()
        
        # 应用表达转换规则
        rewritten_paragraph = self._apply_expression_conversion(rewritten_paragraph)
        
        return rewritten_paragraph if rewritten_paragraph else paragraph
    
    async def _rewrite_conclusion(self, original_conclusion: str, genre: ArticleGenre) -> str:
        """改写结尾"""
        if not original_conclusion or not original_conclusion.strip():
            return original_conclusion
        
        # 获取结尾写作知识
        conclusion_knowledge = await self.search_knowledge_base(
            query=f"结尾 总结 {genre.value}",
            category="style_cards",
            n_results=2
        )
        
        knowledge_context = self.extract_knowledge_context(conclusion_knowledge)
        
        prompt = f"""请改写以下结尾段落，使其更有力和升华：

原结尾：{original_conclusion}
文章体裁：{genre.value}

改写要求：
1. 总结全文，升华主题
2. 语言有力，富有感染力
3. 体现积极向上的价值观
4. 符合{genre.value}体裁的结尾特点

参考知识：
{knowledge_context}

请只返回改写后的结尾内容。"""
        
        try:
            rewritten_conclusion = await self.process_with_llm(prompt, knowledge_context)
            rewritten_conclusion = rewritten_conclusion.strip()
            
            # 应用表达转换规则
            rewritten_conclusion = self._apply_expression_conversion(rewritten_conclusion)
            
            return rewritten_conclusion if rewritten_conclusion else original_conclusion
            
        except Exception as e:
            self.logger.warning(f"结尾改写失败，保留原结尾: {e}")
            return original_conclusion
    
    def _apply_expression_conversion(self, text: str) -> str:
        """应用表达转换规则"""
        for original, converted in self.expression_conversions.items():
            text = text.replace(original, converted)
        
        return text
    
    def _get_paragraph_position_context(self, paragraph_num: int, total_paragraphs: int) -> str:
        """获取段落位置上下文描述"""
        if paragraph_num == 1:
            return "首段（承接导语）"
        elif paragraph_num == total_paragraphs:
            return "末段（总结收束）"
        elif paragraph_num <= total_paragraphs // 2:
            return "前半部分（展开叙述）"
        else:
            return "后半部分（深入分析）"
    
    def _generate_style_changes_summary(self, original_structure: StructureInfo,
                                      rewritten_title: str, rewritten_lead: str,
                                      rewritten_body: List[str], 
                                      rewritten_conclusion: Optional[str]) -> List[str]:
        """生成风格改写说明"""
        changes = []
        
        # 标题变化
        if original_structure.title != rewritten_title:
            changes.append(f"标题优化：'{original_structure.title}' → '{rewritten_title}'")
        
        # 导语变化
        if original_structure.lead != rewritten_lead:
            lead_change_type = self._analyze_text_change_type(original_structure.lead, rewritten_lead)
            changes.append(f"导语{lead_change_type}")
        
        # 正文变化统计
        if len(original_structure.body_paragraphs) == len(rewritten_body):
            changed_paragraphs = 0
            for i, (orig, rewritten) in enumerate(zip(original_structure.body_paragraphs, rewritten_body)):
                if orig != rewritten:
                    changed_paragraphs += 1
            
            if changed_paragraphs > 0:
                changes.append(f"正文{changed_paragraphs}个段落进行了语言优化")
        
        # 结尾变化
        if original_structure.conclusion and rewritten_conclusion:
            if original_structure.conclusion != rewritten_conclusion:
                changes.append("结尾段落进行了升华处理")
        
        # 整体风格改进
        changes.extend([
            "统一使用规范的新闻用语",
            "优化句式结构，增强可读性",
            "调整表达方式，体现官方媒体风格"
        ])
        
        return changes
    
    def _analyze_text_change_type(self, original: str, rewritten: str) -> str:
        """分析文本变化类型"""
        if len(rewritten) > len(original) * 1.2:
            return "扩写优化"
        elif len(rewritten) < len(original) * 0.8:
            return "精简优化"
        else:
            return "语言润色"
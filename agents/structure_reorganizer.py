"""
结构重组Agent
根据体裁特征重新组织文章结构，使其符合中国烟草报的标准格式
"""

import json
import re
from typing import Dict, Any, List, Optional
from utils import ArticleGenre, StructureInfo, AgentResponse, split_into_paragraphs, extract_title_and_content
from .base_agent import LLMAgent

class StructureReorganizerAgent(LLMAgent):
    """结构重组Agent"""
    
    def __init__(self):
        super().__init__(
            name="StructureReorganizer", 
            description="根据体裁特征重组文章结构，优化标题、导语、正文的逻辑布局"
        )
        
        # 各体裁的标准结构模板
        self.structure_templates = {
            ArticleGenre.NEWS: {
                "title_pattern": "主体+动作+结果",
                "lead_requirements": ["何时", "何地", "何人", "何事", "结果"],
                "body_structure": ["导语展开", "背景信息", "详细过程", "相关影响"],
                "paragraph_length": "50-80字/段",
                "conclusion": "optional"
            },
            ArticleGenre.COMMENTARY: {
                "title_pattern": "观点+论题",
                "lead_requirements": ["提出问题", "明确观点"],
                "body_structure": ["现象分析", "原因剖析", "对策建议", "意义价值"],
                "paragraph_length": "80-120字/段", 
                "conclusion": "required"
            },
            ArticleGenre.FEATURE: {
                "title_pattern": "主题+特色",
                "lead_requirements": ["场景描述", "人物介绍", "核心事件"],
                "body_structure": ["详细叙述", "深度分析", "典型事例", "经验总结"],
                "paragraph_length": "100-150字/段",
                "conclusion": "required"
            }
        }
        
        # 段落功能识别模式
        self.paragraph_patterns = {
            "background": [r"据了解", r"背景", r"自.*以来", r"近年来"],
            "process": [r"首先", r"其次", r"然后", r"接下来", r"随后"],
            "result": [r"取得", r"实现", r"达到", r"成效", r"效果"],
            "significance": [r"意义", r"作用", r"价值", r"影响", r"推动"]
        }
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的文章结构重组专家，专门为中国烟草报等官方媒体优化文章结构。

你的任务是根据文章的体裁特征，重新组织文章结构，使其符合官方媒体的标准格式。

不同体裁的结构要求：

新闻类：
- 标题：简洁明了，突出核心事实
- 导语：回答5W1H，概括全文要点
- 正文：倒金字塔结构，重要信息前置
- 段落：50-80字，逻辑清晰

评论类：
- 标题：观点鲜明，吸引读者
- 导语：提出问题或观点
- 正文：论点-论据-论证，层层递进
- 结尾：总结升华，呼吁行动

通讯类：
- 标题：突出特色和亮点  
- 导语：生动的场景描述
- 正文：叙议结合，详略得当
- 结尾：深化主题，升华意义

请保持原文的核心信息和事实准确性，只调整结构和逻辑顺序。

请以JSON格式返回重组后的文章结构。"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理结构重组"""
        try:
            content = input_data.get("content", "")
            genre_info = input_data.get("genre_classification")
            
            if not genre_info:
                return AgentResponse(
                    success=False,
                    message="缺少体裁识别信息",
                    agent_name=self.name
                )
            
            genre = genre_info.genre
            title, main_content = extract_title_and_content(content)
            
            # 分析现有结构
            current_structure = self._analyze_current_structure(title, main_content)
            
            # 基于体裁重组结构
            reorganized_structure = await self._reorganize_structure(
                current_structure, genre, main_content
            )
            
            return AgentResponse(
                success=True,
                message="结构重组完成",
                data={
                    "structure_info": reorganized_structure,
                    "original_structure": current_structure,
                    "genre": genre
                },
                agent_name=self.name
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"结构重组失败: {str(e)}",
                agent_name=self.name
            )
    
    def _analyze_current_structure(self, title: Optional[str], content: str) -> Dict[str, Any]:
        """分析当前文章结构"""
        paragraphs = split_into_paragraphs(content)
        
        if not paragraphs:
            return {
                "title": title or "",
                "lead": "",
                "body_paragraphs": [],
                "conclusion": "",
                "paragraph_functions": [],
                "issues": ["文章内容为空"]
            }
        
        # 识别导语（通常是第一段）
        lead = paragraphs[0] if paragraphs else ""
        
        # 识别正文段落
        body_paragraphs = paragraphs[1:] if len(paragraphs) > 1 else []
        
        # 识别结尾（可能是最后一段）
        conclusion = ""
        if len(body_paragraphs) > 0:
            last_paragraph = body_paragraphs[-1]
            # 如果最后一段包含总结性词汇，视为结尾
            if any(word in last_paragraph for word in ["总之", "综上", "展望", "今后", "未来"]):
                conclusion = last_paragraph
                body_paragraphs = body_paragraphs[:-1]
        
        # 分析段落功能
        paragraph_functions = self._classify_paragraph_functions(body_paragraphs)
        
        # 识别结构问题
        issues = self._identify_structure_issues(title, lead, body_paragraphs, conclusion)
        
        return {
            "title": title or "",
            "lead": lead,
            "body_paragraphs": body_paragraphs,
            "conclusion": conclusion,
            "paragraph_functions": paragraph_functions,
            "issues": issues,
            "total_paragraphs": len(paragraphs)
        }
    
    def _classify_paragraph_functions(self, paragraphs: List[str]) -> List[str]:
        """识别段落功能"""
        functions = []
        
        for paragraph in paragraphs:
            paragraph_function = "content"  # 默认为内容段落
            
            for function_type, patterns in self.paragraph_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, paragraph):
                        paragraph_function = function_type
                        break
                if paragraph_function != "content":
                    break
            
            functions.append(paragraph_function)
        
        return functions
    
    def _identify_structure_issues(self, title: Optional[str], lead: str, 
                                 body_paragraphs: List[str], conclusion: str) -> List[str]:
        """识别结构问题"""
        issues = []
        
        # 标题问题
        if not title or len(title.strip()) == 0:
            issues.append("缺少标题")
        elif len(title) > 30:
            issues.append("标题过长")
        elif len(title) < 5:
            issues.append("标题过短")
        
        # 导语问题
        if not lead or len(lead.strip()) == 0:
            issues.append("缺少导语")
        elif len(lead) < 30:
            issues.append("导语过短")
        elif len(lead) > 150:
            issues.append("导语过长")
        
        # 正文问题
        if len(body_paragraphs) == 0:
            issues.append("缺少正文内容")
        elif len(body_paragraphs) == 1:
            issues.append("正文段落过少")
        
        # 段落长度问题
        for i, paragraph in enumerate(body_paragraphs):
            if len(paragraph) < 20:
                issues.append(f"第{i+2}段过短")
            elif len(paragraph) > 200:
                issues.append(f"第{i+2}段过长")
        
        return issues
    
    async def _reorganize_structure(self, current_structure: Dict[str, Any], 
                                   genre: ArticleGenre, content: str) -> StructureInfo:
        """基于体裁重组结构"""
        
        # 获取体裁相关的知识
        genre_knowledge = await self.search_knowledge_base(
            query=f"{genre.value} 文章结构 写作规范",
            category="style_cards",
            n_results=2
        )
        
        knowledge_context = self.extract_knowledge_context(genre_knowledge)
        
        # 构建重组提示词
        template_info = self.structure_templates.get(genre, self.structure_templates[ArticleGenre.NEWS])
        
        prompt = f"""请根据{genre.value}体裁的要求，重新组织以下文章结构：

当前文章结构分析：
- 标题：{current_structure['title']}
- 导语：{current_structure['lead']}
- 正文段落数：{len(current_structure['body_paragraphs'])}
- 结构问题：{', '.join(current_structure['issues']) if current_structure['issues'] else '无'}

体裁要求：
- 标题模式：{template_info['title_pattern']}
- 导语要求：{', '.join(template_info['lead_requirements'])}
- 正文结构：{', '.join(template_info['body_structure'])}
- 段落长度：{template_info['paragraph_length']}
- 结尾要求：{template_info['conclusion']}

原文内容：
{content}

知识库参考：
{knowledge_context}

请重新组织文章结构，生成优化后的标题、导语、正文段落和结尾。

要求：
1. 保持原文的核心信息和事实准确性
2. 优化逻辑结构和段落安排
3. 确保符合{genre.value}体裁的标准格式
4. 调整段落长度，保持适当的节奏

请以JSON格式返回：
{{
    "title": "重组后的标题",
    "lead": "重组后的导语",
    "body_paragraphs": ["正文段落1", "正文段落2", ...],
    "conclusion": "结尾段落（如需要）",
    "structure_notes": ["结构调整说明1", "说明2", ...]
}}"""
        
        try:
            response = await self.process_with_llm(prompt, knowledge_context)
            result = json.loads(response)
            
            # 验证和清理结果
            return self._validate_and_clean_result(result, current_structure)
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"LLM响应JSON解析失败: {e}")
            # 降级处理：基于规则重组
            return self._fallback_reorganize(current_structure, genre)
    
    def _validate_and_clean_result(self, result: Dict[str, Any], 
                                  current_structure: Dict[str, Any]) -> StructureInfo:
        """验证和清理重组结果"""
        
        # 确保必要字段存在
        title = result.get("title", current_structure.get("title", ""))
        lead = result.get("lead", current_structure.get("lead", ""))
        body_paragraphs = result.get("body_paragraphs", current_structure.get("body_paragraphs", []))
        conclusion = result.get("conclusion", current_structure.get("conclusion"))
        structure_notes = result.get("structure_notes", [])
        
        # 清理和验证标题
        if not title or len(title.strip()) == 0:
            title = current_structure.get("title", "")
            structure_notes.append("保留原标题")
        else:
            title = title.strip()
            if len(title) > 35:
                title = title[:32] + "..."
                structure_notes.append("标题长度已截断")
        
        # 清理和验证导语
        if not lead or len(lead.strip()) == 0:
            lead = current_structure.get("lead", "")
            structure_notes.append("保留原导语")
        else:
            lead = lead.strip()
        
        # 清理和验证正文段落
        if not body_paragraphs or len(body_paragraphs) == 0:
            body_paragraphs = current_structure.get("body_paragraphs", [])
            structure_notes.append("保留原正文结构")
        else:
            # 清理段落内容
            cleaned_paragraphs = []
            for paragraph in body_paragraphs:
                if paragraph and paragraph.strip():
                    cleaned_paragraphs.append(paragraph.strip())
            body_paragraphs = cleaned_paragraphs
        
        # 清理结尾
        if conclusion:
            conclusion = conclusion.strip()
        
        return StructureInfo(
            title=title,
            lead=lead,
            body_paragraphs=body_paragraphs,
            conclusion=conclusion,
            structure_notes=structure_notes
        )
    
    def _fallback_reorganize(self, current_structure: Dict[str, Any], 
                           genre: ArticleGenre) -> StructureInfo:
        """降级处理：基于规则的简单重组"""
        
        title = current_structure.get("title", "")
        lead = current_structure.get("lead", "")
        body_paragraphs = current_structure.get("body_paragraphs", [])
        conclusion = current_structure.get("conclusion", "")
        
        structure_notes = ["使用规则基础重组（LLM处理失败）"]
        
        # 根据体裁调整结构
        if genre == ArticleGenre.NEWS:
            # 新闻类：确保导语简洁，正文按重要性排序
            if len(lead) > 120:
                # 如果导语太长，尝试缩短
                lead = lead[:100] + "..."
                structure_notes.append("导语已缩短")
            
        elif genre == ArticleGenre.COMMENTARY:
            # 评论类：确保有结论
            if not conclusion and body_paragraphs:
                # 如果没有结论，将最后一段作为结论
                conclusion = body_paragraphs[-1]
                body_paragraphs = body_paragraphs[:-1]
                structure_notes.append("将最后段落设为结论")
        
        # 合并过短的段落
        if len(body_paragraphs) > 1:
            merged_paragraphs = []
            i = 0
            while i < len(body_paragraphs):
                current_para = body_paragraphs[i]
                
                # 如果当前段落很短且不是最后一个，尝试与下一段合并
                if len(current_para) < 40 and i < len(body_paragraphs) - 1:
                    next_para = body_paragraphs[i + 1]
                    if len(current_para) + len(next_para) < 150:
                        merged_paragraphs.append(current_para + " " + next_para)
                        structure_notes.append(f"合并第{i+2}和第{i+3}段")
                        i += 2
                        continue
                
                merged_paragraphs.append(current_para)
                i += 1
            
            body_paragraphs = merged_paragraphs
        
        return StructureInfo(
            title=title,
            lead=lead,
            body_paragraphs=body_paragraphs,
            conclusion=conclusion,
            structure_notes=structure_notes
        )
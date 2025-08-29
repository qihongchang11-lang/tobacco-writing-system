"""
体裁识别Agent
自动识别文章的体裁类型（新闻、评论、通讯等）
"""

import json
import re
from typing import Dict, Any, List
from utils import ArticleGenre, GenreClassification, AgentResponse, extract_title_and_content, count_words
from .base_agent import LLMAgent

class GenreClassifierAgent(LLMAgent):
    """体裁识别Agent"""
    
    def __init__(self):
        super().__init__(
            name="GenreClassifier",
            description="识别文章的体裁类型，如新闻、评论、通讯、报告等"
        )
        
        # 体裁特征关键词
        self.genre_keywords = {
            ArticleGenre.NEWS: [
                "日前", "记者", "获悉", "报道", "消息", "通讯员", "本报讯",
                "据了解", "据悉", "会议", "活动", "启动", "举行", "召开"
            ],
            ArticleGenre.COMMENTARY: [
                "观点", "认为", "应该", "必须", "需要", "关键在于", "重要的是",
                "我们要", "让我们", "值得", "反思", "思考", "启示"
            ],
            ArticleGenre.FEATURE: [
                "走进", "深入", "探访", "见闻", "纪实", "故事", "人物", "侧记",
                "现场", "亲历", "目睹", "感受", "体验"
            ],
            ArticleGenre.REPORT: [
                "调研", "调查", "分析", "研究", "报告", "数据", "统计", "比较",
                "对比", "趋势", "现状", "问题", "建议", "措施"
            ],
            ArticleGenre.INTERVIEW: [
                "访谈", "专访", "对话", "采访", "问答", "谈到", "表示", "介绍",
                "回答", "问及", "谈及", "记者问"
            ],
            ArticleGenre.EDITORIAL: [
                "社论", "本报评论员", "评论员文章", "重要论述", "深刻认识",
                "全面贯彻", "坚决", "务必", "一定要"
            ],
            ArticleGenre.NOTICE: [
                "通知", "公告", "声明", "启事", "通告", "布告", "公示",
                "决定", "规定", "办法", "细则"
            ]
        }
        
        # 结构特征模式
        self.structure_patterns = {
            ArticleGenre.NEWS: [
                r"(日前|近日|昨日|今日).*(记者|获悉|消息)",
                r"本报讯.*记者.*报道",
                r".*(会议|活动|仪式).*(举行|召开|启动)"
            ],
            ArticleGenre.COMMENTARY: [
                r".*应该.*",
                r".*必须.*", 
                r".*需要.*",
                r"让我们.*",
                r".*关键在于.*"
            ],
            ArticleGenre.FEATURE: [
                r"走进.*",
                r"在.*现场",
                r".*的故事",
                r".*见闻"
            ]
        }
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的文章体裁识别专家，专门识别中国烟草报等官方媒体的文章体裁。

你的任务是分析给定的文章内容，准确识别其体裁类型。可能的体裁包括：

1. news（新闻）：报道客观事实，具有时效性，通常包含导语
2. commentary（评论）：表达观点看法，具有主观性和论证性
3. feature（通讯/特写）：深度报道，注重细节描写和现场感
4. report（调研报告）：基于调研数据的分析性文章
5. interview（访谈）：对话形式，包含问答内容
6. editorial（社论）：官方立场和观点的权威表达
7. notice（通知公告）：官方发布的正式通知

请从标题、开头、语言风格、结构特征等多个维度进行综合分析，给出准确的体裁判断。

注意中国烟草报的语言特色：
- 新闻类：客观平实，导语概括，倒金字塔结构
- 评论类：观点鲜明，逻辑清晰，语言有力
- 通讯类：现场感强，细节丰富，叙述生动

请始终以JSON格式返回结果。"""
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """处理体裁识别"""
        try:
            content = input_data.get("content", "")
            title, main_content = extract_title_and_content(content)
            
            # 结合规则和LLM进行识别
            rule_result = self._rule_based_classification(title or "", main_content)
            llm_result = await self._llm_based_classification(content)
            
            # 融合两种结果
            final_result = self._merge_results(rule_result, llm_result)
            
            return AgentResponse(
                success=True,
                message="体裁识别完成",
                data={
                    "genre_classification": final_result,
                    "title": title,
                    "content": main_content,
                    "word_count": count_words(content)
                },
                agent_name=self.name
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"体裁识别失败: {str(e)}",
                agent_name=self.name
            )
    
    def _rule_based_classification(self, title: str, content: str) -> Dict[str, Any]:
        """基于规则的体裁识别"""
        text = f"{title} {content}".lower()
        
        # 计算每个体裁的匹配分数
        genre_scores = {}
        
        for genre, keywords in self.genre_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1
                    matched_keywords.append(keyword)
            
            # 结构模式额外加分
            if genre in self.structure_patterns:
                for pattern in self.structure_patterns[genre]:
                    if re.search(pattern, text):
                        score += 2
            
            genre_scores[genre] = {
                "score": score,
                "matched_keywords": matched_keywords
            }
        
        # 找到得分最高的体裁
        best_genre = max(genre_scores.keys(), key=lambda g: genre_scores[g]["score"])
        best_score = genre_scores[best_genre]["score"]
        
        # 计算置信度
        total_score = sum(item["score"] for item in genre_scores.values())
        confidence = best_score / max(total_score, 1)
        
        return {
            "genre": best_genre,
            "confidence": confidence,
            "method": "rule_based",
            "scores": genre_scores
        }
    
    async def _llm_based_classification(self, content: str) -> Dict[str, Any]:
        """基于LLM的体裁识别"""
        
        # 搜索相关的风格卡
        style_knowledge = await self.search_knowledge_base(
            query="文章体裁 风格特征",
            category="style_cards",
            n_results=3
        )
        
        knowledge_context = self.extract_knowledge_context(style_knowledge)
        
        prompt = f"""请分析以下文章的体裁类型：

文章内容：
{content}

参考知识：
{knowledge_context}

请从以下方面分析：
1. 标题特征（是否有明确的新闻性、观点性等）
2. 开头方式（导语、议论开头、叙述开头等）
3. 语言风格（客观陈述、主观评议、生动描述等）
4. 内容结构（倒金字塔、总分总、叙事结构等）
5. 文章意图（报道事实、表达观点、深度挖掘等）

请以JSON格式返回分析结果：
{{
    "genre": "识别的体裁类型（news/commentary/feature/report/interview/editorial/notice）",
    "confidence": 置信度(0-1),
    "reasoning": "详细的识别理由",
    "key_features": ["关键特征1", "关键特征2", ...],
    "alternative_genres": [
        {{"genre": "备选体裁1", "confidence": 置信度}},
        {{"genre": "备选体裁2", "confidence": 置信度}}
    ]
}}"""
        
        try:
            response = await self.process_with_llm(prompt, knowledge_context)
            
            # 解析JSON响应
            result = json.loads(response)
            result["method"] = "llm_based"
            return result
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"LLM响应JSON解析失败: {e}, 响应内容: {response[:200]}...")
            
            # 降级处理：从响应文本中提取信息
            return self._parse_llm_response_fallback(response)
    
    def _parse_llm_response_fallback(self, response: str) -> Dict[str, Any]:
        """LLM响应解析失败时的降级处理"""
        
        # 尝试从响应中提取体裁信息
        genre_mapping = {
            "新闻": ArticleGenre.NEWS,
            "评论": ArticleGenre.COMMENTARY, 
            "通讯": ArticleGenre.FEATURE,
            "特写": ArticleGenre.FEATURE,
            "报告": ArticleGenre.REPORT,
            "访谈": ArticleGenre.INTERVIEW,
            "社论": ArticleGenre.EDITORIAL,
            "通知": ArticleGenre.NOTICE
        }
        
        identified_genre = ArticleGenre.NEWS  # 默认值
        confidence = 0.5  # 降低置信度
        
        response_lower = response.lower()
        for chinese_name, genre_enum in genre_mapping.items():
            if chinese_name in response_lower or genre_enum.value in response_lower:
                identified_genre = genre_enum
                confidence = 0.6
                break
        
        return {
            "genre": identified_genre,
            "confidence": confidence,
            "reasoning": "基于响应文本的模糊匹配",
            "method": "llm_fallback",
            "raw_response": response[:500]
        }
    
    def _merge_results(self, rule_result: Dict[str, Any], llm_result: Dict[str, Any]) -> GenreClassification:
        """融合规则和LLM的识别结果"""
        
        # 权重分配
        rule_weight = 0.3
        llm_weight = 0.7
        
        # 如果两种方法识别的体裁一致，提高置信度
        if rule_result["genre"] == llm_result["genre"]:
            final_genre = rule_result["genre"]
            final_confidence = min(
                rule_result["confidence"] * rule_weight + llm_result["confidence"] * llm_weight + 0.1,
                0.95
            )
            reasoning = f"规则和LLM识别结果一致：{final_genre}"
        else:
            # 选择置信度更高的结果
            if llm_result["confidence"] > rule_result["confidence"]:
                final_genre = llm_result["genre"]
                final_confidence = llm_result["confidence"] * llm_weight
                reasoning = f"LLM识别结果：{llm_result.get('reasoning', '基于语言模型分析')}"
            else:
                final_genre = rule_result["genre"]
                final_confidence = rule_result["confidence"] * rule_weight
                reasoning = f"规则识别结果：匹配到{len(rule_result.get('scores', {}).get(final_genre, {}).get('matched_keywords', []))}个关键特征"
        
        # 生成备选体裁
        alternative_genres = []
        
        # 从LLM结果中提取备选项
        if "alternative_genres" in llm_result:
            for alt in llm_result["alternative_genres"][:2]:
                if alt["genre"] != final_genre:
                    alternative_genres.append({
                        "genre": alt["genre"],
                        "confidence": alt["confidence"]
                    })
        
        # 从规则结果中补充备选项
        rule_scores = rule_result.get("scores", {})
        sorted_rule_genres = sorted(
            rule_scores.keys(),
            key=lambda g: rule_scores[g]["score"],
            reverse=True
        )
        
        for genre in sorted_rule_genres:
            if genre != final_genre and len(alternative_genres) < 3:
                score = rule_scores[genre]["score"]
                if score > 0:
                    alternative_genres.append({
                        "genre": genre.value,
                        "confidence": min(score * 0.1, 0.5)
                    })
        
        return GenreClassification(
            genre=final_genre,
            confidence=final_confidence,
            reasoning=reasoning,
            alternative_genres=alternative_genres[:3]
        )
"""
知识库管理模块
管理风格卡、句式库、术语库等知识库组件
"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from utils import settings, get_agent_logger, KnowledgeBaseEntry, generate_id
from .vector_store import vector_store

logger = get_agent_logger("KnowledgeBase")

class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self):
        self.categories = {
            "style_cards": "风格卡",
            "sentence_patterns": "句式库", 
            "terminology": "术语库",
            "writing_rules": "写作规则",
            "templates": "模板库"
        }
    
    def load_style_cards(self) -> List[KnowledgeBaseEntry]:
        """加载风格卡数据"""
        style_cards = []
        
        # 新闻体裁风格卡
        news_style = {
            "title": "新闻体裁风格特征",
            "genre": "news",
            "characteristics": [
                "标题简洁明了，突出核心信息",
                "导语概括全文要点，回答5W1H",
                "倒金字塔结构，重要信息前置", 
                "语言客观平实，避免主观色彩",
                "时效性强，突出新鲜感",
                "数据准确，来源可靠"
            ],
            "title_patterns": [
                "某地某单位某措施取得某成效",
                "某项工作/活动圆满结束",
                "某领导到某地调研某工作", 
                "某会议在某地召开",
                "某项目正式启动/投产"
            ],
            "lead_templates": [
                "日前，{主体}在{地点}{动作}，{结果}。",
                "记者从{信息源}获悉，{事件}已于{时间}{结果}。",
                "{时间}，{主体}召开{会议}，{议题}。"
            ]
        }
        
        style_cards.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(news_style, ensure_ascii=False, indent=2),
            category="style_cards",
            tags=["新闻", "体裁", "风格"]
        ))
        
        # 评论体裁风格卡
        commentary_style = {
            "title": "评论体裁风格特征",
            "genre": "commentary", 
            "characteristics": [
                "观点鲜明，立场明确",
                "逻辑严密，论证充分",
                "语言有力，感情充沛",
                "结合实际，针对性强",
                "引用权威，增强说服力",
                "呼吁行动，产生共鸣"
            ],
            "structure_patterns": [
                "提出问题-分析问题-解决问题",
                "现象描述-深入分析-观点阐述",
                "正面典型-反面对比-经验总结"
            ],
            "language_features": [
                "多用反问句增强语气",
                "适当使用排比句式",
                "引用名言警句",
                "运用比喻论证"
            ]
        }
        
        style_cards.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(commentary_style, ensure_ascii=False, indent=2),
            category="style_cards", 
            tags=["评论", "体裁", "风格"]
        ))
        
        return style_cards
    
    def load_sentence_patterns(self) -> List[KnowledgeBaseEntry]:
        """加载句式库数据"""
        patterns = []
        
        # 开头句式
        opening_patterns = {
            "title": "文章开头常用句式",
            "category": "opening",
            "patterns": [
                "日前，{主语}在{地点}{动词}，标志着{意义}。",
                "记者从{来源}获悉，{事件}取得{成果}。",
                "随着{背景}，{主体}{动作}蔚然成风。",
                "近年来，{主体}坚持{方法}，{效果}日益显现。",
                "为{目的}，{主体}采取{措施}，{结果}。"
            ]
        }
        
        patterns.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(opening_patterns, ensure_ascii=False, indent=2),
            category="sentence_patterns",
            tags=["开头", "句式", "模板"]
        ))
        
        # 过渡句式
        transition_patterns = {
            "title": "段落过渡句式",
            "category": "transition",
            "patterns": [
                "与此同时，{内容}。",
                "不仅如此，{补充内容}。", 
                "在此基础上，{进一步动作}。",
                "值得一提的是，{特别内容}。",
                "据了解，{详细信息}。"
            ]
        }
        
        patterns.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(transition_patterns, ensure_ascii=False, indent=2),
            category="sentence_patterns",
            tags=["过渡", "句式", "模板"]
        ))
        
        return patterns
    
    def load_terminology(self) -> List[KnowledgeBaseEntry]:
        """加载术语库数据"""
        terms = []
        
        # 烟草行业专业术语
        tobacco_terms = {
            "title": "烟草行业标准术语",
            "category": "tobacco_industry",
            "terms": {
                "中国烟草总公司": "中国烟草总公司",
                "国家烟草专卖局": "国家烟草专卖局", 
                "烟草专卖": "烟草专卖",
                "卷烟工业": "卷烟工业",
                "烟叶生产": "烟叶生产",
                "专卖管理": "专卖管理",
                "现代烟草农业": "现代烟草农业",
                "两化融合": "信息化和工业化融合",
                "精益管理": "精益管理",
                "降焦减害": "降焦减害"
            }
        }
        
        terms.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(tobacco_terms, ensure_ascii=False, indent=2),
            category="terminology",
            tags=["烟草", "术语", "标准"]
        ))
        
        # 党政机关常用表述
        government_terms = {
            "title": "党政机关标准表述",
            "category": "government",
            "terms": {
                "深入学习贯彻": "深入学习贯彻",
                "坚决贯彻落实": "坚决贯彻落实",
                "统筹推进": "统筹推进",
                "扎实推进": "扎实推进",
                "持续深化": "持续深化",
                "全面提升": "全面提升",
                "高质量发展": "高质量发展",
                "新发展理念": "新发展理念"
            }
        }
        
        terms.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(government_terms, ensure_ascii=False, indent=2),
            category="terminology",
            tags=["党政", "表述", "标准"]
        ))
        
        return terms
    
    def load_writing_rules(self) -> List[KnowledgeBaseEntry]:
        """加载写作规则"""
        rules = []
        
        # 标题写作规则
        title_rules = {
            "title": "标题写作规范",
            "category": "title",
            "rules": [
                "标题字数一般控制在15-25字",
                "避免使用问号、感叹号等标点",
                "突出主要信息，省略次要修饰",
                "使用准确的动词，避免空泛表述",
                "数字用法要规范，统计数据要准确"
            ],
            "forbidden_words": [
                "惊人", "震撼", "轰动", "爆炸性"
            ],
            "preferred_words": [
                "显著", "明显", "大幅", "稳步"
            ]
        }
        
        rules.append(KnowledgeBaseEntry(
            id=generate_id(),
            content=json.dumps(title_rules, ensure_ascii=False, indent=2),
            category="writing_rules",
            tags=["标题", "规范", "写作"]
        ))
        
        return rules
    
    def initialize_knowledge_base(self) -> bool:
        """初始化知识库"""
        try:
            logger.info("开始初始化知识库")
            
            # 检查是否已有数据
            stats = vector_store.get_statistics()
            if stats.get("faiss_entries", 0) > 0:
                logger.info("知识库已存在数据，跳过初始化")
                return True
            
            # 加载各类知识库数据
            all_entries = []
            all_entries.extend(self.load_style_cards())
            all_entries.extend(self.load_sentence_patterns())
            all_entries.extend(self.load_terminology())
            all_entries.extend(self.load_writing_rules())
            
            # 批量添加到向量存储
            if all_entries:
                success = vector_store.add_entries(all_entries)
                if success:
                    logger.info(f"成功初始化知识库，共{len(all_entries)}条记录")
                    return True
                else:
                    logger.error("知识库初始化失败")
                    return False
            else:
                logger.warning("没有找到知识库数据")
                return False
                
        except Exception as e:
            logger.error(f"知识库初始化异常: {e}")
            return False
    
    def add_knowledge_entry(self, content: str, category: str, tags: List[str] = None) -> bool:
        """添加知识库条目"""
        try:
            if tags is None:
                tags = []
            
            entry = KnowledgeBaseEntry(
                id=generate_id(),
                content=content,
                category=category,
                tags=tags
            )
            
            success = vector_store.add_entries([entry])
            if success:
                logger.info(f"成功添加知识库条目: {category}")
                return True
            else:
                logger.error(f"添加知识库条目失败: {category}")
                return False
                
        except Exception as e:
            logger.error(f"添加知识库条目异常: {e}")
            return False
    
    def search_knowledge(self, query: str, category: Optional[str] = None, 
                        n_results: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库"""
        try:
            results = vector_store.search(
                query=query,
                n_results=n_results,
                category_filter=category
            )
            
            logger.info(f"知识库搜索: {query}, 找到{len(results)}条结果")
            return results
            
        except Exception as e:
            logger.error(f"知识库搜索异常: {e}")
            return []
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return vector_store.get_statistics()
    
    def export_knowledge_base(self, output_path: Path) -> bool:
        """导出知识库为JSON文件"""
        try:
            # 从FAISS元数据导出
            export_data = {
                "export_time": datetime.now().isoformat(),
                "categories": self.categories,
                "entries": list(vector_store.faiss_metadata.values())
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识库已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出知识库失败: {e}")
            return False

# 全局知识库管理实例
knowledge_manager = KnowledgeBaseManager()
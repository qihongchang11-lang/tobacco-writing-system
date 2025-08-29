"""
主流水线管理器
整合所有Agent，提供完整的改写流水线
"""

from typing import Dict, Any, Optional
from datetime import datetime
from utils import (
    ArticleInput, ProcessingRecord, ProcessingStage, 
    get_agent_logger, generate_id, validate_article_content, Timer
)
from agents import (
    AgentPipeline, GenreClassifierAgent, StructureReorganizerAgent,
    StyleRewriterAgent, FactCheckerAgent, FormatExporterAgent, QualityEvaluatorAgent
)
from knowledge_base import knowledge_manager

logger = get_agent_logger("MainPipeline")

class TobaccoWritingPipeline:
    """中国烟草报风格改写主流水线"""
    
    def __init__(self):
        self.pipeline = AgentPipeline("TobaccoWritingPipeline")
        self._initialize_pipeline()
        self.processing_records = {}
    
    def _initialize_pipeline(self):
        """初始化流水线"""
        # 按顺序添加所有Agent
        self.pipeline.add_agent(GenreClassifierAgent())
        self.pipeline.add_agent(StructureReorganizerAgent())
        self.pipeline.add_agent(StyleRewriterAgent())
        self.pipeline.add_agent(FactCheckerAgent())
        self.pipeline.add_agent(FormatExporterAgent())
        self.pipeline.add_agent(QualityEvaluatorAgent())
        
        logger.info("主流水线初始化完成")
    
    async def process_article(self, content: str, title: Optional[str] = None,
                            author: Optional[str] = None) -> ProcessingRecord:
        """处理单篇文章"""
        
        # 创建处理记录
        record_id = generate_id()
        
        article_input = ArticleInput(
            content=content,
            title=title,
            author=author
        )
        
        # 验证输入
        is_valid, error_msg = validate_article_content(content)
        if not is_valid:
            record = ProcessingRecord(
                id=record_id,
                input_article=article_input,
                current_stage=ProcessingStage.UPLOADED
            )
            logger.error(f"文章验证失败: {error_msg}")
            return record
        
        record = ProcessingRecord(
            id=record_id,
            input_article=article_input,
            current_stage=ProcessingStage.UPLOADED
        )
        
        self.processing_records[record_id] = record
        
        try:
            with Timer() as total_timer:
                logger.info(f"开始处理文章: {record_id}")
                
                # 准备初始数据
                input_data = {
                    "content": content,
                    "title": title,
                    "author": author,
                    "record_id": record_id
                }
                
                # 执行完整流水线
                pipeline_result = await self.pipeline.execute_pipeline(input_data)
                
                # 更新处理记录
                if pipeline_result["success"]:
                    await self._update_record_from_pipeline_result(record, pipeline_result)
                    record.current_stage = ProcessingStage.QUALITY_EVALUATED
                    
                    final_data = pipeline_result.get("final_data", {})
                    quality_result = final_data.get("quality_evaluation")
                    if quality_result:
                        record.final_content = final_data.get("final_content", content)
                        record.export_path = final_data.get("docx_path")
                    
                    logger.info(f"文章处理完成: {record_id}, 总耗时: {total_timer.get_elapsed():.2f}s")
                else:
                    logger.error(f"文章处理失败: {record_id}, 错误: {pipeline_result.get('error')}")
                
                record.processing_time["total"] = total_timer.get_elapsed()
                record.updated_at = datetime.now()
                
                return record
                
        except Exception as e:
            logger.error(f"文章处理异常: {record_id}, 错误: {e}", exc_info=True)
            record.updated_at = datetime.now()
            return record
    
    async def _update_record_from_pipeline_result(self, record: ProcessingRecord, 
                                                pipeline_result: Dict[str, Any]):
        """从流水线结果更新处理记录"""
        
        final_data = pipeline_result.get("final_data", {})
        agent_results = pipeline_result.get("agent_results", [])
        
        # 更新各阶段结果和处理时间
        for agent_result in agent_results:
            agent_name = agent_result["agent_name"]
            processing_time = agent_result["processing_time"]
            record.processing_time[agent_name] = processing_time
            
            # 根据Agent名称更新对应结果
            if agent_name == "GenreClassifier":
                record.genre_result = final_data.get("genre_classification")
                record.current_stage = ProcessingStage.GENRE_CLASSIFIED
                
            elif agent_name == "StructureReorganizer":
                record.structure_result = final_data.get("structure_info")
                record.current_stage = ProcessingStage.STRUCTURE_REORGANIZED
                
            elif agent_name == "StyleRewriter":
                record.style_result = final_data.get("style_rewrite_result")
                record.current_stage = ProcessingStage.STYLE_REWRITTEN
                
            elif agent_name == "FactChecker":
                record.fact_check_result = final_data.get("fact_check_result")
                record.current_stage = ProcessingStage.FACT_CHECKED
                
            elif agent_name == "FormatExporter":
                record.export_path = final_data.get("docx_path")
                record.current_stage = ProcessingStage.FORMAT_EXPORTED
                
            elif agent_name == "QualityEvaluator":
                record.quality_result = final_data.get("quality_evaluation")
                record.final_content = final_data.get("final_content")
                record.current_stage = ProcessingStage.QUALITY_EVALUATED
    
    def get_processing_record(self, record_id: str) -> Optional[ProcessingRecord]:
        """获取处理记录"""
        return self.processing_records.get(record_id)
    
    def list_processing_records(self) -> Dict[str, ProcessingRecord]:
        """列出所有处理记录"""
        return self.processing_records.copy()
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """获取流水线统计信息"""
        return self.pipeline.get_pipeline_stats()
    
    async def initialize_knowledge_base(self) -> bool:
        """初始化知识库"""
        logger.info("开始初始化知识库")
        
        try:
            success = knowledge_manager.initialize_knowledge_base()
            if success:
                logger.info("知识库初始化成功")
            else:
                logger.error("知识库初始化失败")
            return success
            
        except Exception as e:
            logger.error(f"知识库初始化异常: {e}")
            return False

# 全局主流水线实例
main_pipeline = TobaccoWritingPipeline()
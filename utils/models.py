"""
数据模型定义
定义系统中使用的所有数据结构
"""

from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# 文章体裁枚举
class ArticleGenre(str, Enum):
    """文章体裁枚举"""
    NEWS = "news"              # 新闻
    COMMENTARY = "commentary"  # 评论
    FEATURE = "feature"        # 通讯/特写
    REPORT = "report"          # 调研报告
    INTERVIEW = "interview"    # 访谈
    EDITORIAL = "editorial"    # 社论
    NOTICE = "notice"          # 通知公告

# 改写阶段枚举  
class ProcessingStage(str, Enum):
    """改写处理阶段"""
    UPLOADED = "uploaded"           # 已上传
    GENRE_CLASSIFIED = "genre_classified"  # 体裁识别完成
    STRUCTURE_REORGANIZED = "structure_reorganized"  # 结构重组完成
    STYLE_REWRITTEN = "style_rewritten"  # 风格改写完成
    FACT_CHECKED = "fact_checked"   # 事实校对完成
    FORMAT_EXPORTED = "format_exported"  # 格式导出完成
    QUALITY_EVALUATED = "quality_evaluated"  # 质量评估完成

class ArticleInput(BaseModel):
    """原始文章输入"""
    content: str = Field(..., description="原始文章内容")
    title: Optional[str] = Field(None, description="原始标题")
    author: Optional[str] = Field(None, description="作者")
    source: Optional[str] = Field(None, description="来源")
    upload_time: datetime = Field(default_factory=datetime.now)

class GenreClassification(BaseModel):
    """体裁识别结果"""
    genre: ArticleGenre = Field(..., description="识别的文章体裁")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    reasoning: str = Field(..., description="识别理由")
    alternative_genres: List[Dict[str, float]] = Field(default_factory=list, description="备选体裁及置信度")

class StructureInfo(BaseModel):
    """文章结构信息"""
    title: str = Field(..., description="标题")
    lead: str = Field(..., description="导语")
    body_paragraphs: List[str] = Field(..., description="正文段落")
    conclusion: Optional[str] = Field(None, description="结尾")
    structure_notes: List[str] = Field(default_factory=list, description="结构调整说明")

class StyleRewriteResult(BaseModel):
    """风格改写结果"""
    rewritten_title: str = Field(..., description="改写后标题")
    rewritten_lead: str = Field(..., description="改写后导语") 
    rewritten_body: List[str] = Field(..., description="改写后正文段落")
    rewritten_conclusion: Optional[str] = Field(None, description="改写后结尾")
    style_changes: List[str] = Field(default_factory=list, description="风格改写说明")

class FactCheckIssue(BaseModel):
    """事实校对问题"""
    issue_type: Literal["terminology", "data", "forbidden_words", "consistency"] = Field(..., description="问题类型")
    location: str = Field(..., description="问题位置")
    original_text: str = Field(..., description="原文本")
    suggested_correction: str = Field(..., description="建议修正")
    severity: Literal["high", "medium", "low"] = Field(..., description="严重程度")
    explanation: str = Field(..., description="问题说明")

class FactCheckResult(BaseModel):
    """事实校对结果"""
    issues: List[FactCheckIssue] = Field(default_factory=list, description="发现的问题")
    corrected_content: str = Field(..., description="校对后内容")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="整体准确性评分")

class QualityMetrics(BaseModel):
    """质量评估指标"""
    title_completeness: float = Field(..., ge=0.0, le=1.0, description="标题完整性")
    lead_quality: float = Field(..., ge=0.0, le=1.0, description="导语质量")
    content_coherence: float = Field(..., ge=0.0, le=1.0, description="内容连贯性")
    style_consistency: float = Field(..., ge=0.0, le=1.0, description="风格一致性")
    factual_accuracy: float = Field(..., ge=0.0, le=1.0, description="事实准确性")
    format_compliance: float = Field(..., ge=0.0, le=1.0, description="格式规范性")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="综合评分")

class QualityEvaluation(BaseModel):
    """质量评估结果"""
    metrics: QualityMetrics = Field(..., description="各项指标得分")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    passed: bool = Field(..., description="是否通过质量检查")

class ProcessingRecord(BaseModel):
    """处理记录"""
    id: str = Field(..., description="记录ID")
    input_article: ArticleInput = Field(..., description="输入文章")
    current_stage: ProcessingStage = Field(..., description="当前阶段")
    genre_result: Optional[GenreClassification] = Field(None, description="体裁识别结果")
    structure_result: Optional[StructureInfo] = Field(None, description="结构重组结果")
    style_result: Optional[StyleRewriteResult] = Field(None, description="风格改写结果")
    fact_check_result: Optional[FactCheckResult] = Field(None, description="事实校对结果")
    quality_result: Optional[QualityEvaluation] = Field(None, description="质量评估结果")
    final_content: Optional[str] = Field(None, description="最终内容")
    export_path: Optional[str] = Field(None, description="导出文件路径")
    processing_time: Dict[str, float] = Field(default_factory=dict, description="各阶段处理时间")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class KnowledgeBaseEntry(BaseModel):
    """知识库条目"""
    id: str = Field(..., description="条目ID")
    content: str = Field(..., description="内容")
    category: str = Field(..., description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    embedding: Optional[List[float]] = Field(None, description="向量表示")
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    """Agent响应基类"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    processing_time: float = Field(..., description="处理时间")
    agent_name: str = Field(..., description="Agent名称")
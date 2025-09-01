"""
配置管理模块
统一管理所有配置参数和环境变量
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类"""
    
    # API配置
    claude_api_key: str = Field(..., env="CLAUDE_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    claude_model: str = Field("claude-3-sonnet-20241022", env="CLAUDE_MODEL")
    
    # 路径配置
    project_root: Path = Path(__file__).parent.parent
    data_path: Path = project_root / "data"
    chroma_db_path: Path = Field(project_root / "data" / "chroma_db", env="CHROMA_DB_PATH")
    faiss_index_path: Path = Field(project_root / "data" / "faiss_index", env="FAISS_INDEX_PATH")
    
    # 知识库路径
    style_cards_path: Path = Field(project_root / "knowledge_base" / "style_cards", env="STYLE_CARDS_PATH")
    sentence_patterns_path: Path = Field(project_root / "knowledge_base" / "sentence_patterns", env="SENTENCE_PATTERNS_PATH")
    terminology_path: Path = Field(project_root / "knowledge_base" / "terminology", env="TERMINOLOGY_PATH")
    
    # 模型配置
    embedding_model: str = Field("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", env="EMBEDDING_MODEL")
    max_content_length: int = Field(50000, env="MAX_CONTENT_LENGTH")
    batch_size: int = Field(32, env="BATCH_SIZE")
    
    # Web服务配置
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8501, env="PORT")
    debug: bool = Field(False, env="DEBUG")
    
    # 质量评估配置
    quality_threshold: float = Field(0.75, env="QUALITY_THRESHOLD")
    regression_test_size: int = Field(100, env="REGRESSION_TEST_SIZE")
    
    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __post_init__(self):
        """初始化后处理，确保必要目录存在"""
        self.data_path.mkdir(exist_ok=True)
        self.chroma_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
        self.style_cards_path.mkdir(parents=True, exist_ok=True)
        self.sentence_patterns_path.mkdir(parents=True, exist_ok=True)
        self.terminology_path.mkdir(parents=True, exist_ok=True)

# 全局配置实例
settings = Settings()

# 确保目录存在
def ensure_directories():
    """确保所有必要目录存在"""
    directories = [
        settings.data_path,
        settings.chroma_db_path.parent,
        settings.faiss_index_path.parent,
        settings.style_cards_path,
        settings.sentence_patterns_path,
        settings.terminology_path
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

ensure_directories()
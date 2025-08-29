"""
知识库包初始化文件
"""

from .vector_store import vector_store, VectorStore
from .knowledge_manager import knowledge_manager, KnowledgeBaseManager

__all__ = [
    'vector_store',
    'VectorStore', 
    'knowledge_manager',
    'KnowledgeBaseManager'
]
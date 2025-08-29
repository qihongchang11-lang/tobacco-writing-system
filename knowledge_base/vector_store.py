"""
向量数据库管理模块
集成Chroma和FAISS，提供统一的向量检索接口
"""

import os
import json
import pickle
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import numpy as np
import chromadb
import faiss
from sentence_transformers import SentenceTransformer
from utils import settings, get_agent_logger, KnowledgeBaseEntry, generate_id, generate_hash

logger = get_agent_logger("VectorDB")

class VectorStore:
    """向量存储统一接口"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.chroma_collection = None
        self.faiss_index = None
        self.faiss_metadata = {}
        self.embedding_dim = 384  # MiniLM模型的向量维度
        
        self._initialize()
    
    def _initialize(self):
        """初始化向量存储"""
        try:
            # 初始化embedding模型
            logger.info(f"正在加载embedding模型: {settings.embedding_model}")
            self.embedding_model = SentenceTransformer(settings.embedding_model)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            
            # 初始化Chroma
            self._initialize_chroma()
            
            # 初始化FAISS
            self._initialize_faiss()
            
            logger.info("向量存储初始化完成")
            
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
            raise
    
    def _initialize_chroma(self):
        """初始化Chroma数据库"""
        try:
            self.chroma_client = chromadb.PersistentClient(path=str(settings.chroma_db_path))
            
            # 获取或创建集合
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="tobacco_writing_knowledge",
                metadata={"description": "中国烟草报写作知识库"}
            )
            
            logger.info("Chroma数据库初始化完成")
            
        except Exception as e:
            logger.error(f"Chroma初始化失败: {e}")
            raise
    
    def _initialize_faiss(self):
        """初始化FAISS索引"""
        try:
            faiss_index_file = settings.faiss_index_path / "index.faiss"
            faiss_metadata_file = settings.faiss_index_path / "metadata.pkl"
            
            if faiss_index_file.exists() and faiss_metadata_file.exists():
                # 加载现有索引
                self.faiss_index = faiss.read_index(str(faiss_index_file))
                with open(faiss_metadata_file, 'rb') as f:
                    self.faiss_metadata = pickle.load(f)
                logger.info("加载现有FAISS索引")
            else:
                # 创建新索引
                self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)  # 内积索引
                self.faiss_metadata = {}
                logger.info("创建新FAISS索引")
                
        except Exception as e:
            logger.error(f"FAISS初始化失败: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """生成文本向量"""
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
        
        try:
            embedding = self.embedding_model.encode(text.strip())
            # 归一化向量（用于内积计算余弦相似度）
            embedding = embedding / np.linalg.norm(embedding)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            return [0.0] * self.embedding_dim
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        if not texts:
            return []
        
        try:
            # 过滤空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            if not valid_texts:
                return [[0.0] * self.embedding_dim] * len(texts)
            
            embeddings = self.embedding_model.encode(valid_texts)
            # 归一化
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # 补齐原始长度
            result = []
            valid_idx = 0
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[valid_idx].tolist())
                    valid_idx += 1
                else:
                    result.append([0.0] * self.embedding_dim)
            
            return result
            
        except Exception as e:
            logger.error(f"批量文本向量化失败: {e}")
            return [[0.0] * self.embedding_dim] * len(texts)
    
    def add_to_chroma(self, entries: List[KnowledgeBaseEntry]) -> bool:
        """添加条目到Chroma"""
        try:
            if not entries:
                return True
            
            documents = [entry.content for entry in entries]
            metadatas = [
                {
                    "id": entry.id,
                    "category": entry.category,
                    "tags": json.dumps(entry.tags),
                    "created_at": entry.created_at.isoformat()
                }
                for entry in entries
            ]
            ids = [entry.id for entry in entries]
            
            self.chroma_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"已添加{len(entries)}条记录到Chroma")
            return True
            
        except Exception as e:
            logger.error(f"添加到Chroma失败: {e}")
            return False
    
    def add_to_faiss(self, entries: List[KnowledgeBaseEntry]) -> bool:
        """添加条目到FAISS"""
        try:
            if not entries:
                return True
            
            # 生成向量
            embeddings = []
            for entry in entries:
                if entry.embedding:
                    embeddings.append(entry.embedding)
                else:
                    embedding = self.embed_text(entry.content)
                    embeddings.append(embedding)
                    entry.embedding = embedding
            
            if not embeddings:
                return True
            
            # 转换为numpy数组
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # 获取当前索引大小，用作ID起始值
            start_id = self.faiss_index.ntotal
            
            # 添加到FAISS索引
            self.faiss_index.add(embeddings_array)
            
            # 更新元数据
            for i, entry in enumerate(entries):
                faiss_id = start_id + i
                self.faiss_metadata[faiss_id] = {
                    "id": entry.id,
                    "content": entry.content,
                    "category": entry.category,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat()
                }
            
            # 保存索引和元数据
            self._save_faiss()
            
            logger.info(f"已添加{len(entries)}条记录到FAISS")
            return True
            
        except Exception as e:
            logger.error(f"添加到FAISS失败: {e}")
            return False
    
    def add_entries(self, entries: List[KnowledgeBaseEntry]) -> bool:
        """添加条目到向量存储（同时添加到Chroma和FAISS）"""
        if not entries:
            return True
        
        # 确保所有条目都有向量表示
        for entry in entries:
            if not entry.embedding:
                entry.embedding = self.embed_text(entry.content)
        
        chroma_success = self.add_to_chroma(entries)
        faiss_success = self.add_to_faiss(entries)
        
        return chroma_success and faiss_success
    
    def search_chroma(self, query: str, n_results: int = 10, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """使用Chroma搜索"""
        try:
            where_filter = {}
            if category_filter:
                where_filter["category"] = category_filter
            
            results = self.chroma_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Chroma搜索失败: {e}")
            return []
    
    def search_faiss(self, query: str, n_results: int = 10, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """使用FAISS搜索"""
        try:
            if self.faiss_index.ntotal == 0:
                return []
            
            # 生成查询向量
            query_embedding = np.array([self.embed_text(query)], dtype=np.float32)
            
            # 搜索
            scores, indices = self.faiss_index.search(query_embedding, min(n_results * 2, self.faiss_index.ntotal))
            
            # 格式化结果
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS返回-1表示无效结果
                    continue
                
                if idx in self.faiss_metadata:
                    metadata = self.faiss_metadata[idx]
                    
                    # 应用分类过滤
                    if category_filter and metadata.get("category") != category_filter:
                        continue
                    
                    results.append({
                        "id": metadata["id"],
                        "content": metadata["content"],
                        "distance": float(1 - score),  # 转换为距离（1-相似度）
                        "metadata": metadata
                    })
                    
                    if len(results) >= n_results:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS搜索失败: {e}")
            return []
    
    def search(self, query: str, n_results: int = 10, category_filter: Optional[str] = None, 
               use_faiss: bool = True) -> List[Dict[str, Any]]:
        """统一搜索接口"""
        if use_faiss:
            return self.search_faiss(query, n_results, category_filter)
        else:
            return self.search_chroma(query, n_results, category_filter)
    
    def _save_faiss(self):
        """保存FAISS索引和元数据"""
        try:
            settings.faiss_index_path.mkdir(parents=True, exist_ok=True)
            
            faiss_index_file = settings.faiss_index_path / "index.faiss"
            faiss_metadata_file = settings.faiss_index_path / "metadata.pkl"
            
            faiss.write_index(self.faiss_index, str(faiss_index_file))
            
            with open(faiss_metadata_file, 'wb') as f:
                pickle.dump(self.faiss_metadata, f)
                
        except Exception as e:
            logger.error(f"保存FAISS索引失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取向量存储统计信息"""
        try:
            chroma_count = self.chroma_collection.count()
            faiss_count = self.faiss_index.ntotal if self.faiss_index else 0
            
            # 按类别统计
            category_stats = {}
            for metadata in self.faiss_metadata.values():
                category = metadata.get("category", "unknown")
                category_stats[category] = category_stats.get(category, 0) + 1
            
            return {
                "chroma_entries": chroma_count,
                "faiss_entries": faiss_count,
                "category_distribution": category_stats,
                "embedding_dimension": self.embedding_dim,
                "model": settings.embedding_model
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear_all(self) -> bool:
        """清空所有数据（谨慎使用）"""
        try:
            # 清空Chroma
            self.chroma_client.delete_collection("tobacco_writing_knowledge")
            self.chroma_collection = self.chroma_client.create_collection(
                name="tobacco_writing_knowledge",
                metadata={"description": "中国烟草报写作知识库"}
            )
            
            # 重置FAISS
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
            self.faiss_metadata = {}
            self._save_faiss()
            
            logger.info("已清空所有向量数据")
            return True
            
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            return False

# 全局向量存储实例
vector_store = VectorStore()
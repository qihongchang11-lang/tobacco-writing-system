"""
BM25 Knowledge Retriever - BM25知识检索器
提供轻量级的知识库检索功能，支持缓存
"""

import re
from typing import List, Dict, Tuple
from functools import lru_cache
from pathlib import Path
from loguru import logger


class BM25KnowledgeRetriever:
    """
    BM25知识检索器

    使用BM25算法进行知识检索，支持LRU缓存
    """

    def __init__(self, knowledge_path: str = "data/knowledge/tobacco_knowledge.txt"):
        """
        初始化检索器

        Args:
            knowledge_path: 知识库文件路径
        """
        self.knowledge_path = knowledge_path
        self.corpus = self._load_knowledge()
        self.tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]

        logger.info(f"Loaded {len(self.corpus)} knowledge entries")

    def _load_knowledge(self) -> List[str]:
        """加载知识库"""
        try:
            path = Path(self.knowledge_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    return lines
            else:
                logger.warning(f"Knowledge file not found: {self.knowledge_path}, using defaults")
                return self._get_default_knowledge()
        except Exception as e:
            logger.error(f"Failed to load knowledge: {e}")
            return self._get_default_knowledge()

    def _get_default_knowledge(self) -> List[str]:
        """默认知识库（如果文件不存在）"""
        return [
            "国家烟草专卖局是烟草行业的最高管理机构，负责全国烟草专卖管理工作。",
            "中国烟草总公司负责全国烟草生产经营管理，统一领导全国烟草产供销。",
            "专卖制度是烟草行业的基本制度，实行统一领导、垂直管理、专卖专营。",
            "卷烟是指用卷烟纸将烟丝卷制成条状的烟草制品。",
            "烟草行业实行计划管理，统一调拨，保证市场供应。",
            "烟叶是卷烟和其他烟草制品的主要原料，分为晾晒烟叶和烤烟叶。",
            "各省级烟草专卖局负责本辖区内的烟草专卖管理工作。",
            "烟草行业坚持依法治理、规范经营、服务社会的基本方针。",
            "专卖管理包括烟草专卖许可证管理、市场监督检查、案件查处等。",
            "烟草税收是国家财政收入的重要来源之一。"
        ]

    def _tokenize(self, text: str) -> List[str]:
        """
        简单的中文分词（基于字和词）

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        # 简单分词：字 + 常见词
        tokens = []

        # 1. 提取常见词汇
        common_words = [
            '国家', '烟草', '专卖', '管理', '公司', '卷烟', '烟叶',
            '制度', '行业', '市场', '生产', '经营', '许可证',
            '监督', '检查', '税收', '财政', '服务', '规范'
        ]

        for word in common_words:
            if word in text:
                tokens.append(word)

        # 2. 添加单字（去除标点）
        chars = re.findall(r'[\u4e00-\u9fa5]', text)
        tokens.extend(chars)

        return tokens

    @lru_cache(maxsize=100)
    def search(
        self,
        query: str,
        topk: int = 3
    ) -> List[Dict]:
        """
        搜索相关知识

        Args:
            query: 查询文本
            topk: 返回前K个结果

        Returns:
            List of {
                'snippet': str,
                'score': float,
                'source': str
            }
        """
        # 简化的BM25实现
        query_tokens = set(self._tokenize(query))

        if not query_tokens:
            return []

        scores = []
        for idx, doc_tokens in enumerate(self.tokenized_corpus):
            doc_token_set = set(doc_tokens)

            # 计算交集数量作为简单的相关性分数
            intersection = query_tokens & doc_token_set
            score = len(intersection) / len(query_tokens) if query_tokens else 0

            if score > 0:
                scores.append((score, idx))

        # 排序并取topk
        scores.sort(reverse=True)
        top_results = scores[:topk]

        results = []
        for score, idx in top_results:
            results.append({
                'snippet': self.corpus[idx],
                'score': round(score, 2),
                'source': f'local:tobacco_knowledge.txt#L{idx+1}'
            })

        logger.debug(f"Found {len(results)} relevant knowledge entries for query: {query[:50]}...")
        return results

    def add_knowledge(self, text: str):
        """
        动态添加知识条目

        Args:
            text: 新知识条目
        """
        if text and text not in self.corpus:
            self.corpus.append(text)
            self.tokenized_corpus.append(self._tokenize(text))

            # 清空缓存（因为知识库变化了）
            self.search.cache_clear()

            logger.info(f"Added new knowledge entry: {text[:50]}...")


if __name__ == "__main__":
    # 测试代码
    retriever = BM25KnowledgeRetriever()

    # 测试查询
    test_queries = [
        "国家烟草专卖局的职责是什么",
        "卷烟生产管理",
        "烟草税收政策"
    ]

    print("="*50)
    print("BM25 Knowledge Retriever Test")
    print("="*50)

    for query in test_queries:
        print(f"\n查询: {query}")
        results = retriever.search(query, topk=2)

        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  相关度: {result['score']}")
            print(f"  内容: {result['snippet']}")
            print(f"  来源: {result['source']}")

    # 测试缓存
    print("\n" + "="*50)
    print("测试缓存 (第二次查询应该更快):")
    import time

    start = time.time()
    retriever.search(test_queries[0])
    print(f"首次查询耗时: {(time.time() - start)*1000:.2f}ms")

    start = time.time()
    retriever.search(test_queries[0])
    print(f"缓存查询耗时: {(time.time() - start)*1000:.2f}ms")
# -*- coding: utf-8 -*-
"""
新华财经样本检索器
基于BM25的样本相似度检索，复用tobacco-writing-pipeline的检索架构
"""
import json
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple
import math


class XHFSampleRetriever:
    """新华财经样本检索器"""

    def __init__(
        self,
        samples_json: str = "data/xhf_samples/structured_articles.json",
        top_k: int = 3
    ):
        """
        初始化检索器

        Args:
            samples_json: 结构化样本JSON路径
            top_k: 返回top-k个最相似样本
        """
        self.top_k = top_k
        self.samples = self._load_samples(samples_json)
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.idf = {}
        self._build_bm25_index()

    def _load_samples(self, json_path: str) -> List[Dict]:
        """加载样本文章"""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"样本文件不存在: {json_path}")

        with open(path, 'r', encoding='utf-8') as f:
            samples = json.load(f)

        print(f"[XHFRetriever] 已加载 {len(samples)} 篇样本文章")
        return samples

    def _tokenize(self, text: str) -> List[str]:
        """中文分词（简化版，使用正则）"""
        # 提取中文词、数字、英文单词
        tokens = re.findall(r'[\u4e00-\u9fa5]+|[0-9]+\.?[0-9]*|[a-zA-Z]+', text)
        return [t for t in tokens if len(t) >= 2]

    def _build_bm25_index(self) -> None:
        """构建BM25索引"""
        corpus_tokens = []

        # 分词并统计文档长度
        for sample in self.samples:
            text = f"{sample['title']} {sample['lead']} {sample['body']}"
            tokens = self._tokenize(text)
            corpus_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))

        # 计算平均文档长度
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1

        # 计算IDF
        doc_count = len(corpus_tokens)
        word_doc_count = Counter()

        for tokens in corpus_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                word_doc_count[token] += 1

        # IDF公式: log((N - df + 0.5) / (df + 0.5))
        for word, df in word_doc_count.items():
            self.idf[word] = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)

        print(f"[XHFRetriever] BM25索引构建完成，文档数: {len(corpus_tokens)}, 词汇数: {len(self.idf)}")

    def _bm25_score(self, query_tokens: List[str], doc_idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        """计算BM25分数"""
        doc_text = f"{self.samples[doc_idx]['title']} {self.samples[doc_idx]['lead']} {self.samples[doc_idx]['body']}"
        doc_tokens = self._tokenize(doc_text)
        doc_len = len(doc_tokens)

        if doc_len == 0:
            return 0.0

        # 统计词频
        term_freq = Counter(doc_tokens)

        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue

            tf = term_freq.get(token, 0)
            if tf == 0:
                continue

            # BM25公式
            idf_score = self.idf[token]
            norm = k1 * (1 - b + b * (doc_len / self.avg_doc_length))
            score += idf_score * (tf * (k1 + 1)) / (tf + norm)

        return score

    def retrieve(
        self,
        query_text: str,
        article_type: str = None
    ) -> List[Dict]:
        """
        检索最相似的样本文章

        Args:
            query_text: 待改写的原文
            article_type: 文章类型（可选，用于过滤）

        Returns:
            List[Dict]: top-k个相似样本，每个包含article和score
        """
        # 分词
        query_tokens = self._tokenize(query_text)

        # 计算所有文档的BM25分数
        scores = []
        for idx in range(len(self.samples)):
            score = self._bm25_score(query_tokens, idx)
            scores.append((idx, score))

        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)

        # 构建结果（可选按类型过滤）
        results = []
        for idx, score in scores:
            sample = self.samples[idx]

            # 类型过滤
            if article_type and sample.get('type') != article_type:
                continue

            results.append({
                "article": sample,
                "score": float(score),
                "id": sample.get('id', f'xhf_{idx:03d}')
            })

            if len(results) >= self.top_k:
                break

        # 如果过滤后不足top_k，补充其他样本
        if len(results) < self.top_k:
            for idx, score in scores:
                if len(results) >= self.top_k:
                    break
                sample = self.samples[idx]
                if sample.get('id') not in [r['id'] for r in results]:
                    results.append({
                        "article": sample,
                        "score": float(score),
                        "id": sample.get('id', f'xhf_{idx:03d}')
                    })

        print(f"[XHFRetriever] 检索到 {len(results)} 个相似样本")
        return results

    def get_sample_by_id(self, sample_id: str) -> Dict:
        """根据ID获取样本"""
        for sample in self.samples:
            if sample.get('id') == sample_id:
                return sample
        return None


# 测试代码
if __name__ == '__main__':
    # 初始化检索器
    retriever = XHFSampleRetriever(top_k=3)

    # 测试检索
    test_query = """
    近日，山东省烟草专卖局召开全省数字化转型推进会议，
    深入贯彻落实行业高质量发展要求，推动智能制造和数字化管理全面升级。
    今年以来，全省累计投入资金5000万元用于智能化改造项目。
    """

    print("\n" + "=" * 60)
    print("测试检索")
    print("=" * 60)
    print(f"\n查询文本: {test_query[:100]}...")

    results = retriever.retrieve(test_query)

    print(f"\n检索结果 (Top {len(results)}):")
    for i, result in enumerate(results, 1):
        article = result['article']
        score = result['score']
        print(f"\n[{i}] ID: {result['id']} | Score: {score:.2f}")
        print(f"    标题: {article['title']}")
        print(f"    类型: {article.get('type', 'unknown')}")
        print(f"    导语: {article['lead'][:80]}...")

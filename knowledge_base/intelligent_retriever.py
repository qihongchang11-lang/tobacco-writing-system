"""
智能样本检索系统 - BM25 + 语义相似度混合检索
用于学习驱动的改写系统，从样本库中检索最相关的文章
"""

import json
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentRetriever:
    """智能样本检索器"""

    def __init__(self, data_file: str = "data/samples/structured_articles.json"):
        self.data_file = Path(data_file)
        self.articles = []
        self.bm25_index = {}
        self.vocab = set()
        self.idf_scores = {}

        # 加载数据
        self._load_articles()
        self._build_bm25_index()

    def _load_articles(self) -> None:
        """加载结构化文章数据"""
        try:
            if not self.data_file.exists():
                logger.warning(f"数据文件不存在: {self.data_file}")
                return

            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', [])

            logger.info(f"加载了 {len(self.articles)} 篇文章")

        except Exception as e:
            logger.error(f"加载文章数据失败: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """中文文本分词（简化版）"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        # 分割为字符（中文按字分词）
        tokens = []
        for char in text:
            if char.strip() and char not in [' ', '\t', '\n']:
                tokens.append(char)

        # 组合常见词汇
        text_clean = ''.join(tokens)
        common_words = [
            '烟草', '卷烟', '烟叶', '专卖', '营销', '销售', '监管', '生产',
            '会议', '召开', '举办', '活动', '工作', '发展', '建设', '管理',
            '同比', '增长', '下降', '提升', '优化', '推进', '落实', '部署'
        ]

        for word in common_words:
            if word in text_clean:
                tokens.append(word)

        return tokens

    def _build_bm25_index(self) -> None:
        """构建BM25索引"""
        if not self.articles:
            return

        # 计算文档词频
        doc_tokens = []
        all_tokens = []

        for article in self.articles:
            # 合并标题、导语、正文
            full_text = f"{article.get('title', '')} {article.get('lead', '')} {article.get('body', '')}"
            tokens = self._tokenize(full_text)
            doc_tokens.append(tokens)
            all_tokens.extend(tokens)

        # 建立词汇表
        self.vocab = set(all_tokens)

        # 计算IDF
        doc_count = len(self.articles)
        for token in self.vocab:
            doc_freq = sum(1 for tokens in doc_tokens if token in tokens)
            self.idf_scores[token] = math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5))

        # 构建索引
        for i, tokens in enumerate(doc_tokens):
            token_counts = Counter(tokens)
            self.bm25_index[i] = {
                'tokens': token_counts,
                'length': len(tokens)
            }

        logger.info(f"构建BM25索引完成，词汇量: {len(self.vocab)}")

    def _calculate_bm25_score(self, query_tokens: List[str], doc_index: int) -> float:
        """计算BM25相似度得分"""
        if doc_index not in self.bm25_index:
            return 0.0

        doc_info = self.bm25_index[doc_index]
        doc_tokens = doc_info['tokens']
        doc_length = doc_info['length']

        # BM25参数
        k1, b = 1.2, 0.75
        avg_doc_length = sum(info['length'] for info in self.bm25_index.values()) / len(self.bm25_index)

        score = 0.0
        for token in query_tokens:
            if token not in self.vocab:
                continue

            tf = doc_tokens.get(token, 0)
            idf = self.idf_scores.get(token, 0)

            # BM25公式
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * (numerator / denominator)

        return score

    def _calculate_semantic_similarity(self, query: str, article: Dict[str, Any]) -> float:
        """计算语义相似度（简化版）"""
        # 合并文章文本
        article_text = f"{article.get('title', '')} {article.get('lead', '')} {article.get('body', '')}"

        # 关键词匹配
        query_lower = query.lower()
        article_lower = article_text.lower()

        # 核心概念匹配
        tobacco_concepts = ['烟草', '卷烟', '烟叶', '专卖', '营销', '销售', '监管']
        business_concepts = ['会议', '活动', '工作', '发展', '建设', '管理', '部署']
        data_concepts = ['增长', '下降', '同比', '环比', '数据', '统计', '分析']

        concept_groups = [tobacco_concepts, business_concepts, data_concepts]

        similarity = 0.0

        # 概念组匹配
        for concepts in concept_groups:
            query_match = sum(1 for concept in concepts if concept in query_lower)
            article_match = sum(1 for concept in concepts if concept in article_lower)
            if query_match > 0 and article_match > 0:
                similarity += min(query_match, article_match) / len(concepts)

        # 栏目匹配奖励
        features = article.get('features', {})
        column_indicators = features.get('column_indicators', {})

        column_keywords = {
            'news_general': ['会议', '召开', '举办', '活动'],
            'economic_data': ['增长', '销售', '收入', '数据', '%'],
            'policy_interpretation': ['政策', '通知', '公告', '规定'],
            'case_observation': ['典型', '先进', '案例', '经验']
        }

        for column, keywords in column_keywords.items():
            if any(kw in query_lower for kw in keywords) and column_indicators.get(column, False):
                similarity += 0.3

        return min(similarity, 1.0)

    def retrieve_similar_samples(
        self,
        query_text: str,
        target_column: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        检索相似样本

        Args:
            query_text: 查询文本
            target_column: 目标栏目（可选过滤）
            top_k: 返回数量

        Returns:
            相似文章列表，包含相似度得分
        """
        if not self.articles:
            logger.warning("没有可用的文章数据")
            return []

        query_tokens = self._tokenize(query_text)

        candidates = []

        for i, article in enumerate(self.articles):
            # 栏目过滤
            if target_column:
                features = article.get('features', {})
                column_indicators = features.get('column_indicators', {})
                if not column_indicators.get(target_column, False):
                    continue

            # 计算BM25得分
            bm25_score = self._calculate_bm25_score(query_tokens, i)

            # 计算语义相似度
            semantic_score = self._calculate_semantic_similarity(query_text, article)

            # 混合得分 (BM25: 40%, 语义: 60%)
            combined_score = 0.4 * bm25_score + 0.6 * semantic_score

            candidates.append({
                'article': article,
                'bm25_score': bm25_score,
                'semantic_score': semantic_score,
                'combined_score': combined_score
            })

        # 按综合得分排序
        candidates.sort(key=lambda x: x['combined_score'], reverse=True)

        # 多样性控制：避免相似文章聚集
        diverse_results = []
        used_titles = set()

        for candidate in candidates:
            if len(diverse_results) >= top_k:
                break

            title = candidate['article'].get('title', '')
            # 简单去重：标题相似度过高的跳过
            is_duplicate = any(
                self._title_similarity(title, used_title) > 0.7
                for used_title in used_titles
            )

            if not is_duplicate:
                diverse_results.append({
                    'article_id': candidate['article']['id'],
                    'title': title,
                    'lead': candidate['article'].get('lead', ''),
                    'body': candidate['article'].get('body', ''),
                    'similarity_score': round(candidate['combined_score'], 3),
                    'features': candidate['article'].get('features', {}),
                    'full_article': candidate['article']
                })
                used_titles.add(title)

        logger.info(f"检索到 {len(diverse_results)} 个相关样本 (查询: {query_text[:20]}...)")
        return diverse_results

    def _title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0

        # 简单的字符重叠率
        set1 = set(title1)
        set2 = set(title2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        if not self.articles:
            return {"total_articles": 0, "vocab_size": 0}

        # 栏目分布
        column_distribution = {}
        for article in self.articles:
            features = article.get('features', {})
            column_indicators = features.get('column_indicators', {})
            for column, has_indicator in column_indicators.items():
                if has_indicator:
                    column_distribution[column] = column_distribution.get(column, 0) + 1

        return {
            "total_articles": len(self.articles),
            "vocab_size": len(self.vocab),
            "column_distribution": column_distribution,
            "avg_article_length": sum(len(article.get('body', '')) for article in self.articles) / len(self.articles),
            "index_status": "ready" if self.bm25_index else "not_built"
        }


def main():
    """测试函数"""
    retriever = IntelligentRetriever()

    # 显示统计信息
    stats = retriever.get_statistics()
    print(f"📊 检索器统计: {stats}")

    # 测试检索
    test_queries = [
        "山东省烟草召开会议推进营销工作",
        "销售收入增长数据分析",
        "政策解读通知发布"
    ]

    for query in test_queries:
        print(f"\n🔍 查询: {query}")
        results = retriever.retrieve_similar_samples(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']} (相似度: {result['similarity_score']})")


if __name__ == "__main__":
    main()
"""
数据采集模块
用于采集中国烟草报等媒体的公开稿件，建立训练样本库
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import random

from utils import settings, get_agent_logger, generate_id, clean_text, safe_filename
from knowledge_base import knowledge_manager

logger = get_agent_logger("DataCollector")

class ArticleCollector:
    """文章采集器基类"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = None
        self.collected_urls = set()
        
    async def collect_articles(self, max_pages: int = 5, delay: float = 1.0) -> List[Dict[str, Any]]:
        """采集文章，子类需要实现"""
        raise NotImplementedError
    
    def clean_article_content(self, content: str) -> str:
        """清理文章内容"""
        if not content:
            return ""
        
        # 基础文本清理
        content = clean_text(content)
        
        # 移除常见的无关内容
        remove_patterns = [
            r"本报讯",
            r"记者\s*\w+\s*报道",
            r"来源[:：]\s*[\w\s]+",
            r"责任编辑[:：]\s*\w+",
            r"相关链接",
            r"【打印】",
            r"【关闭】"
        ]
        
        import re
        for pattern in remove_patterns:
            content = re.sub(pattern, "", content)
        
        return content.strip()
    
    def extract_article_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """从页面提取文章信息，子类需要实现"""
        raise NotImplementedError

class ChinaTobaccoCollector(ArticleCollector):
    """中国烟草报采集器"""
    
    def __init__(self):
        super().__init__("中国烟草报", "http://www.echinatobacco.com")
        
        # 常见栏目URL模式
        self.section_urls = [
            "/news/",  # 新闻
            "/comment/",  # 评论
            "/feature/",  # 特写
            "/interview/",  # 访谈
        ]
        
    async def collect_articles(self, max_pages: int = 5, delay: float = 1.0) -> List[Dict[str, Any]]:
        """采集中国烟草报文章"""
        articles = []
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            for section in self.section_urls:
                logger.info(f"开始采集栏目: {section}")
                
                try:
                    section_articles = await self._collect_section_articles(
                        section, max_pages, delay
                    )
                    articles.extend(section_articles)
                    
                    # 避免频繁请求
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"采集栏目{section}失败: {e}")
                    continue
        
        logger.info(f"共采集到{len(articles)}篇文章")
        return articles
    
    async def _collect_section_articles(self, section: str, max_pages: int, delay: float) -> List[Dict[str, Any]]:
        """采集特定栏目的文章"""
        articles = []
        
        for page in range(1, max_pages + 1):
            try:
                page_url = f"{self.base_url}{section}?page={page}"
                
                async with self.session.get(page_url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"页面请求失败: {page_url}, 状态码: {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 提取文章链接（需要根据实际网站结构调整）
                    article_links = self._extract_article_links(soup)
                    
                    for link in article_links:
                        if link in self.collected_urls:
                            continue
                        
                        self.collected_urls.add(link)
                        
                        try:
                            article = await self._collect_single_article(link)
                            if article:
                                articles.append(article)
                                
                            # 控制请求频率
                            await asyncio.sleep(delay)
                            
                        except Exception as e:
                            logger.error(f"采集文章失败 {link}: {e}")
                            continue
                            
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"采集页面失败 {page}: {e}")
                continue
        
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """提取文章链接（模拟实现，需要根据实际网站调整）"""
        links = []
        
        # 这里是示例代码，实际需要根据网站结构调整
        article_elements = soup.find_all("a", class_="article-link")
        
        for element in article_elements:
            href = element.get("href")
            if href:
                full_url = urljoin(self.base_url, href)
                links.append(full_url)
        
        return links
    
    async def _collect_single_article(self, url: str) -> Optional[Dict[str, Any]]:
        """采集单篇文章"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                article_info = self.extract_article_info(soup, url)
                return article_info
                
        except Exception as e:
            logger.error(f"采集文章内容失败 {url}: {e}")
            return None
    
    def extract_article_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """从页面提取文章信息（模拟实现）"""
        try:
            # 提取标题（需要根据实际HTML结构调整）
            title_element = soup.find("h1", class_="article-title") or soup.find("title")
            title = title_element.get_text().strip() if title_element else ""
            
            # 提取正文
            content_element = soup.find("div", class_="article-content") or soup.find("div", class_="content")
            if not content_element:
                return None
            
            content = content_element.get_text().strip()
            content = self.clean_article_content(content)
            
            if not content or len(content) < 100:  # 过滤太短的内容
                return None
            
            # 提取发布时间
            time_element = soup.find("time") or soup.find("span", class_="publish-time")
            publish_time = time_element.get_text().strip() if time_element else ""
            
            # 提取作者
            author_element = soup.find("span", class_="author") or soup.find("div", class_="author")
            author = author_element.get_text().strip() if author_element else ""
            
            return {
                "id": generate_id(),
                "title": title,
                "content": content,
                "author": author,
                "publish_time": publish_time,
                "url": url,
                "source": self.name,
                "collected_at": datetime.now().isoformat(),
                "word_count": len(content)
            }
            
        except Exception as e:
            logger.error(f"提取文章信息失败: {e}")
            return None

class SampleDataGenerator:
    """示例数据生成器（用于测试和演示）"""
    
    def __init__(self):
        self.sample_articles = [
            {
                "title": "某省烟草商业系统扎实推进高质量发展取得显著成效",
                "content": """日前，记者从某省烟草专卖局（公司）获悉，该局（公司）认真贯彻落实国家局党组决策部署，坚持稳中求进工作总基调，统筹推进各项工作，高质量发展取得显著成效。

据了解，该局（公司）始终把党的建设摆在首要位置，深入学习贯彻习近平新时代中国特色社会主义思想，扎实开展主题教育，党建引领作用更加凸显。同时，该局（公司）持续深化供给侧结构性改革，优化卷烟投放结构，市场化经营水平不断提升。

在专卖管理方面，该局（公司）强化市场监管，严厉打击各类涉烟违法行为，市场秩序持续向好。此外，该局（公司）还加大科技创新力度，推进数字化转型，管理效能显著提高。

下一步，该局（公司）将继续坚持高质量发展不动摇，为行业持续健康发展贡献更大力量。""",
                "genre": "news",
                "source": "中国烟草报"
            },
            {
                "title": "以改革创新精神推动烟草行业高质量发展",
                "content": """当前，烟草行业正处于转型升级的关键时期，面临着新的机遇和挑战。如何在新形势下实现高质量发展，是全行业必须深入思考和积极实践的重大课题。

改革创新是推动高质量发展的根本动力。我们要坚持问题导向，勇于破解制约发展的体制机制障碍，不断激发内生发展动力。要深化供给侧结构性改革，优化资源配置，提高供给质量和效率。

科技创新是高质量发展的重要支撑。要加大研发投入，强化创新驱动，推进产业链现代化，提升核心竞争力。要积极拥抱数字化转型，运用大数据、人工智能等新技术，推动管理变革和效率提升。

人才是第一资源。要完善人才培养机制，优化人才结构，激发人才活力，为高质量发展提供智力保障。

新时代呼唤新作为。让我们以改革创新的精神，推动烟草行业在高质量发展道路上行稳致远。""",
                "genre": "commentary",
                "source": "中国烟草报"
            }
        ]
    
    def generate_sample_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """生成示例文章数据"""
        articles = []
        
        for i in range(count):
            base_article = random.choice(self.sample_articles)
            
            article = {
                "id": generate_id(),
                "title": base_article["title"],
                "content": base_article["content"],
                "genre": base_article["genre"],
                "source": base_article["source"],
                "author": f"记者{chr(65 + i)}",
                "publish_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "url": f"http://example.com/article/{generate_id()}",
                "collected_at": datetime.now().isoformat(),
                "word_count": len(base_article["content"])
            }
            
            articles.append(article)
        
        return articles

class DataCollectionManager:
    """数据采集管理器"""
    
    def __init__(self):
        self.collectors = {
            "china_tobacco": ChinaTobaccoCollector()
        }
        self.sample_generator = SampleDataGenerator()
        self.storage_path = settings.data_path / "collected_articles"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def collect_all_sources(self, max_pages_per_source: int = 3) -> List[Dict[str, Any]]:
        """从所有来源采集文章"""
        all_articles = []
        
        for name, collector in self.collectors.items():
            logger.info(f"开始采集来源: {name}")
            
            try:
                articles = await collector.collect_articles(max_pages_per_source)
                all_articles.extend(articles)
                logger.info(f"来源{name}采集完成，共{len(articles)}篇")
                
            except Exception as e:
                logger.error(f"采集来源{name}失败: {e}")
        
        return all_articles
    
    def generate_sample_articles(self, count: int = 20) -> List[Dict[str, Any]]:
        """生成示例文章（用于测试）"""
        return self.sample_generator.generate_sample_data(count)
    
    def save_articles(self, articles: List[Dict[str, Any]], filename: str = None) -> str:
        """保存采集的文章"""
        if not filename:
            filename = f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        file_path = self.storage_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"文章已保存到: {file_path}")
        return str(file_path)
    
    def load_articles(self, filename: str) -> List[Dict[str, Any]]:
        """加载已采集的文章"""
        file_path = self.storage_path / filename
        
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            logger.info(f"已加载{len(articles)}篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"加载文章失败: {e}")
            return []
    
    def add_articles_to_knowledge_base(self, articles: List[Dict[str, Any]]) -> bool:
        """将采集的文章添加到知识库"""
        try:
            success_count = 0
            
            for article in articles:
                # 将文章作为知识库条目
                content = f"标题: {article.get('title', '')}\n\n{article.get('content', '')}"
                
                # 确定分类
                genre = article.get('genre', 'unknown')
                category = f"samples_{genre}"
                
                # 生成标签
                tags = [
                    article.get('source', 'unknown'),
                    genre,
                    "sample"
                ]
                
                success = knowledge_manager.add_knowledge_entry(
                    content=content,
                    category=category,
                    tags=tags
                )
                
                if success:
                    success_count += 1
            
            logger.info(f"成功添加{success_count}/{len(articles)}篇文章到知识库")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"添加文章到知识库失败: {e}")
            return False

# 全局数据采集管理器
data_collector = DataCollectionManager()
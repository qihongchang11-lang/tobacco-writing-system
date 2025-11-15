"""
东方烟草报风格改写系统 API
提供基于新华财经风格的烟草行业文章智能改写服务
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path
import time
import os
import asyncio
from loguru import logger
from dotenv import load_dotenv
from openai import OpenAI


# 加载环境变量
load_dotenv(".env", override=True)

# 获取新闻系统配置
NEWS_API_HOST = os.getenv("NEWS_API_HOST", "0.0.0.0")
NEWS_API_PORT = int(os.getenv("NEWS_API_PORT", "8081"))

# 设置API密钥
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-c8b34b714d3e409e82b894362975caab")
os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
os.environ["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL", "deepseek-chat")

# 清除可能冲突的环境变量
if "CLAUDE_API_KEY" in os.environ:
    del os.environ["CLAUDE_API_KEY"]

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心组件
from core.constraint_decoder import ConstraintDecoder
from core.knowledge_retriever import BM25KnowledgeRetriever
from core.postprocess import RewritePostProcessor

# 导入学习驱动组件
from knowledge_base.intelligent_retriever import IntelligentRetriever
from agents.few_shot_rewriter import FewShotRewriter

# 导入新华财经组件
from core.xhf_style_injector import XHFStyleInjector
from core.xhf_quality_checker import XHFQualityChecker

# 创建FastAPI应用
app = FastAPI(
    title="东方烟草报风格改写系统 API",
    description="基于新华财经风格的烟草行业文章智能改写服务，提供专业化、文学化的内容生成",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 数据模型
class RewriteRequest(BaseModel):
    text: str
    genres: Optional[List[str]] = []
    strict_mode: Optional[bool] = False

class RewriteResponse(BaseModel):
    column: Dict[str, Any]
    title: str
    lead: str
    body: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    audit: Dict[str, Any]
    scores: Dict[str, float]
    meta: Dict[str, Any]

class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    port: int
    mode: str
    components: Dict[str, bool]
    learning_stats: Optional[Dict[str, Any]] = None

# 全局组件实例
_components = {}

@app.on_event("startup")
async def startup_event():
    """初始化所有组件"""
    logger.info("正在初始化东方烟草报风格改写系统...")

    try:
        # 初始化约束解码器
        _components["decoder"] = ConstraintDecoder()
        logger.info("ConstraintDecoder initialized with 9 org whitelist entries")

        # 初始化知识检索器
        _components["retriever"] = BM25KnowledgeRetriever()
        logger.info("BM25KnowledgeRetriever initialized")

        # 初始化后处理器
        _components["postprocessor"] = RewritePostProcessor()
        logger.info("RewritePostProcessor initialized")

        # 初始化智能检索器
        _components["intelligent_retriever"] = IntelligentRetriever()
        logger.info("IntelligentRetriever initialized")

        # 初始化Few-shot重写器
        _components["few_shot_rewriter"] = FewShotRewriter(
            retriever=_components["intelligent_retriever"]
        )
        logger.info("FewShotRewriter initialized")

        # 初始化新华财经风格注入器
        _components["xhf_style_injector"] = XHFStyleInjector()
        logger.info("XHFStyleInjector initialized")

        # 初始化新华财经质量检查器
        _components["xhf_quality_checker"] = XHFQualityChecker()
        logger.info("XHFQualityChecker initialized")

        logger.info("东方烟草报风格改写系统所有组件初始化完成")
        logger.info(f"服务运行在端口: {NEWS_API_PORT}")

    except Exception as e:
        logger.error(f"组件初始化失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """清理资源"""
    logger.info("东方烟草报风格改写系统正在关闭...")
    _components.clear()

@app.get("/", response_model=dict)
async def root():
    """根路径信息"""
    return {
        "service": "东方烟草报风格改写系统",
        "version": "2.0.0",
        "mode": "few_shot_learning",
        "status": "running",
        "port": NEWS_API_PORT
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 检查所有组件状态
        component_status = {
            name: bool(component) for name, component in _components.items()
        }

        # 获取学习统计信息
        learning_stats = None
        if _components.get("intelligent_retriever"):
            learning_stats = _components["intelligent_retriever"].get_stats()

        return HealthResponse(
            ok=True,
            service="东方烟草报风格改写系统",
            version="2.0.0",
            port=NEWS_API_PORT,
            mode="few_shot_learning",
            components=component_status,
            learning_stats=learning_stats
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            ok=False,
            service="东方烟草报风格改写系统",
            version="2.0.0",
            port=NEWS_API_PORT,
            mode="error",
            components={},
            learning_stats=None
        )

@app.post("/rewrite", response_model=RewriteResponse)
async def rewrite_article(request: RewriteRequest):
    """文章改写接口"""
    start_time = time.time()

    try:
        logger.info(f"收到改写请求，文本长度: {len(request.text)}")

        # 使用Few-shot重写器进行改写
        rewriter = _components.get("few_shot_rewriter")
        if not rewriter:
            raise HTTPException(status_code=503, detail="重写器未初始化")

        # 执行改写
        result = await asyncio.to_thread(
            rewriter.rewrite,
            request.text,
            genres=request.genres,
            strict_mode=request.strict_mode
        )

        # 处理时间
        latency_ms = int((time.time() - start_time) * 1000)
        result["meta"]["latency_ms"] = latency_ms
        result["meta"]["port"] = NEWS_API_PORT
        result["meta"]["service"] = "东方烟草报风格改写系统"

        logger.info(f"改写完成，耗时: {latency_ms}ms")
        return RewriteResponse(**result)

    except Exception as e:
        logger.error(f"改写失败: {e}")
        raise HTTPException(status_code=500, detail=f"改写失败: {str(e)}")

@app.get("/learning-stats")
async def learning_stats():
    """学习统计接口"""
    try:
        retriever = _components.get("intelligent_retriever")
        if not retriever:
            return {"error": "学习组件未初始化"}

        stats = retriever.get_stats()
        stats["service"] = "东方烟草报风格改写系统"
        stats["port"] = NEWS_API_PORT
        return stats
    except Exception as e:
        logger.error(f"获取学习统计失败: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动东方烟草报风格改写系统，端口: {NEWS_API_PORT}")
    uvicorn.run(
        "news_api_main:app",
        host=NEWS_API_HOST,
        port=NEWS_API_PORT,
        reload=False,
        log_level="info"
    )
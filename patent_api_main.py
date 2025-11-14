"""
CNIPA发明专利高质量改写系统 API
提供中国国家知识产权局合规的专利四件套自动生成服务
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path
import time
import os
import asyncio
import json
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env", override=True)

# 获取专利系统配置
PATENT_API_HOST = os.getenv("PATENT_API_HOST", "0.0.0.0")
PATENT_API_PORT = int(os.getenv("PATENT_API_PORT", "8082"))

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 数据模型
class PatentDocument(BaseModel):
    title: str
    technical_field: str
    background_art: str
    summary: str
    detailed_description: str
    drawings: Optional[List[str]] = []
    claims: List[str]
    abstract: str

class ProcessingRequest(BaseModel):
    draft_content: str
    title: Optional[str] = None
    invention_type: str = "invention"  # invention, utility_model, design
    priority_countries: Optional[List[str]] = []
    enable_checks: bool = True

class ProcessingResponse(BaseModel):
    success: bool
    patent_documents: Dict[str, Any]
    traceability: Dict[str, Any]
    quality_report: Dict[str, Any]
    processing_time: float
    files_generated: List[str]

class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    port: int
    mode: str
    components: Dict[str, bool]
    system_stats: Optional[Dict[str, Any]] = None

class GateResult(BaseModel):
    gate_name: str
    is_passed: bool
    score: float
    details: List[Dict[str, Any]]
    recommendations: List[str]

# 创建FastAPI应用
app = FastAPI(
    title="CNIPA发明专利高质量改写系统 API",
    description="中国国家知识产权局合规的专利四件套自动生成服务，包括说明书、权利要求书、摘要和技术交底书",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 模拟专利系统组件（需要根据实际情况实现）
_components = {}

class MockPatentSystem:
    """模拟专利系统组件 - 需要替换为实际实现"""

    def __init__(self):
        self.initialized = True

    async def process_patent(self, draft_content: str, request_data: dict) -> dict:
        """模拟专利处理流程"""
        # 这里应该调用实际的专利处理逻辑
        # 包括PSE提取、四件套生成、质量检查等

        # 模拟处理时间
        await asyncio.sleep(1)

        # 返回模拟结果
        return {
            "patent_documents": {
                "specification": {
                    "title": "一种基于" + draft_content[:20] + "的装置",
                    "technical_field": "本发明涉及" + draft_content[:30] + "领域",
                    "background_art": "现有的技术存在以下问题...",
                    "summary": "本发明要解决的技术问题是...",
                    "detailed_description": "下面结合附图和实施例对本发明作进一步说明..."
                },
                "claims": {
                    "independent_claims": [
                        "一种装置，其特征在于，包括：第一组件；第二组件..."
                    ],
                    "dependent_claims": [
                        "根据权利要求1所述的装置，其中所述第一组件...",
                        "根据权利要求1或2所述的装置，其中还包括..."
                    ]
                },
                "abstract": {
                    "content": "本发明公开了一种装置，包括第一组件和第二组件...",
                    "character_count": 150,
                    "figure_markers": []
                },
                "disclosure": {
                    "technical_problem": "解决现有技术中的效率问题",
                    "technical_solution": "采用新型结构设计",
                    "technical_effect": "提高效率30%"
                }
            },
            "traceability": {
                "term_consistency": True,
                "figure_numbering": True,
                "part_numbering": True
            },
            "quality_report": {
                "gate_a": {"passed": True, "score": 0.95},
                "gate_b": {"passed": True, "score": 1.0},
                "gate_c": {"passed": True, "score": 1.0},
                "gate_d": {"passed": True, "score": 1.0},
                "gate_e": {"passed": True, "score": 0.98},
                "gate_f": {"passed": True, "score": 1.0},
                "overall_score": 0.99
            },
            "files_generated": [
                "specification.md",
                "claims.md",
                "abstract.md",
                "disclosure.md"
            ]
        }

@app.on_event("startup")
async def startup_event():
    """初始化专利系统组件"""
    logger.info("正在初始化CNIPA发明专利高质量改写系统...")

    try:
        # 初始化模拟专利系统
        _components["patent_system"] = MockPatentSystem()
        logger.info("专利系统组件初始化完成")

        # 初始化其他组件（需要根据实际情况添加）
        _components["pse_extractor"] = True  # 模拟PSE提取器
        _components["four_piece_generator"] = True  # 模拟四件套生成器
        _components["quality_checker"] = True  # 模拟质量检查器

        logger.info("CNIPA发明专利高质量改写系统所有组件初始化完成")
        logger.info(f"服务运行在端口: {PATENT_API_PORT}")

    except Exception as e:
        logger.error(f"组件初始化失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """清理资源"""
    logger.info("CNIPA发明专利高质量改写系统正在关闭...")
    _components.clear()

@app.get("/", response_model=dict)
async def root():
    """根路径信息"""
    return {
        "service": "CNIPA发明专利高质量改写系统",
        "version": "1.0.0",
        "mode": "cnipa_compliant",
        "status": "running",
        "port": PATENT_API_PORT,
        "description": "中国国家知识产权局合规的专利四件套自动生成服务"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 检查所有组件状态
        component_status = {
            name: bool(component) for name, component in _components.items()
        }

        # 系统统计信息
        system_stats = {
            "total_patents_processed": 0,  # 实际实现时需要统计
            "compliance_rate": 0.99,
            "average_processing_time": 25.5,
            "active_gates": ["A", "B", "C", "D", "E", "F"]
        }

        return HealthResponse(
            ok=True,
            service="CNIPA发明专利高质量改写系统",
            version="1.0.0",
            port=PATENT_API_PORT,
            mode="cnipa_compliant",
            components=component_status,
            system_stats=system_stats
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            ok=False,
            service="CNIPA发明专利高质量改写系统",
            version="1.0.0",
            port=PATENT_API_PORT,
            mode="error",
            components={},
            system_stats=None
        )

@app.post("/process", response_model=ProcessingResponse)
async def process_patent(request: ProcessingRequest):
    """专利文档处理接口"""
    start_time = time.time()

    try:
        logger.info(f"收到专利处理请求，草稿长度: {len(request.draft_content)}")

        # 获取专利系统组件
        patent_system = _components.get("patent_system")
        if not patent_system:
            raise HTTPException(status_code=503, detail="专利系统未初始化")

        # 执行专利处理
        result = await patent_system.process_patent(
            request.draft_content,
            request.dict()
        )

        # 计算处理时间
        processing_time = time.time() - start_time

        # 构建完整响应
        response_data = {
            "success": True,
            "patent_documents": result["patent_documents"],
            "traceability": result["traceability"],
            "quality_report": result["quality_report"],
            "processing_time": processing_time,
            "files_generated": result["files_generated"]
        }

        logger.info(f"专利处理完成，耗时: {processing_time:.2f}s")
        return ProcessingResponse(**response_data)

    except Exception as e:
        logger.error(f"专利处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"专利处理失败: {str(e)}")

@app.post("/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    invention_type: str = "invention",
    enable_checks: bool = True
):
    """文件上传并处理接口"""
    try:
        # 读取文件内容
        content = await file.read()
        draft_content = content.decode('utf-8')

        # 创建处理请求
        request = ProcessingRequest(
            draft_content=draft_content,
            invention_type=invention_type,
            enable_checks=enable_checks
        )

        # 调用处理接口
        return await process_patent(request)

    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.get("/gates/{gate_id}")
async def get_gate_result(gate_id: str):
    """获取质量门检查结果"""
    gate_mapping = {
        "A": "KTF完整度检查",
        "B": "支持性检查",
        "C": "术语一致性检查",
        "D": "禁用词检查",
        "E": "摘要验证",
        "F": "背景泄露检查"
    }

    return {
        "gate_name": gate_mapping.get(gate_id, f"Gate {gate_id}"),
        "is_passed": True,
        "score": 0.95,
        "details": [],
        "recommendations": []
    }

@app.get("/system-info")
async def system_info():
    """系统信息接口"""
    return {
        "service": "CNIPA发明专利高质量改写系统",
        "version": "1.0.0",
        "compliance_version": "CNIPA 2024",
        "supported_document_types": ["invention", "utility_model", "design"],
        "quality_gates": ["A", "B", "C", "D", "E", "F"],
        "output_formats": ["markdown", "json", "docx"],
        "processing_modes": ["fast", "comprehensive", "strict"]
    }

if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动CNIPA发明专利高质量改写系统，端口: {PATENT_API_PORT}")
    uvicorn.run(
        "patent_api_main:app",
        host=PATENT_API_HOST,
        port=PATENT_API_PORT,
        reload=False,
        log_level="info"
    )
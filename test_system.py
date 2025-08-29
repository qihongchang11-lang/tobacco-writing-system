"""
系统测试脚本
验证各个组件的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main_pipeline import main_pipeline
from utils import get_agent_logger

logger = get_agent_logger("SystemTest")

# 测试文章样本
TEST_ARTICLE = """
某省烟草专卖局积极推进数字化转型取得良好效果

近期，某省烟草专卖局在数字化转型方面取得了不错的进展。该局通过引入新技术，优化了工作流程，提高了效率。

据介绍，该局首先对现有系统进行了升级改造，然后开展了员工培训，最后实施了新的管理制度。通过这些措施，工作质量得到了明显改善。

相关负责人表示，这项工作还将继续深入开展，争取取得更大成效。他们希望通过不断努力，为行业发展做出更大贡献。
"""

async def test_complete_pipeline():
    """测试完整流水线"""
    logger.info("开始测试完整流水线...")
    
    try:
        # 初始化系统
        await main_pipeline.initialize_knowledge_base()
        
        # 处理测试文章
        result = await main_pipeline.process_article(
            content=TEST_ARTICLE,
            title="测试文章",
            author="测试作者"
        )
        
        # 验证结果
        logger.info(f"处理状态: {result.current_stage}")
        logger.info(f"处理耗时: {result.processing_time.get('total', 0):.2f}秒")
        
        if result.genre_result:
            logger.info(f"体裁识别: {result.genre_result.genre.value} (置信度: {result.genre_result.confidence:.2f})")
        
        if result.quality_result:
            logger.info(f"质量评分: {result.quality_result.metrics.overall_score:.2f}")
        
        if result.final_content:
            logger.info("✅ 流水线测试成功")
            print("\n" + "="*50)
            print("最终改写结果:")
            print("="*50)
            print(result.final_content)
            print("="*50)
        else:
            logger.error("❌ 流水线测试失败：未生成最终内容")
        
        return result.final_content is not None
        
    except Exception as e:
        logger.error(f"流水线测试异常: {e}")
        return False

async def test_individual_agents():
    """测试各个Agent"""
    logger.info("开始测试各个Agent...")
    
    from agents import (
        GenreClassifierAgent, StructureReorganizerAgent,
        StyleRewriterAgent, FactCheckerAgent,
        FormatExporterAgent, QualityEvaluatorAgent
    )
    
    # 测试体裁识别
    genre_agent = GenreClassifierAgent()
    genre_result = await genre_agent.execute({"content": TEST_ARTICLE})
    logger.info(f"体裁识别Agent: {'✅' if genre_result.success else '❌'}")
    
    if not genre_result.success:
        logger.error(f"体裁识别失败: {genre_result.message}")
        return False
    
    # 测试结构重组
    structure_agent = StructureReorganizerAgent()
    structure_result = await structure_agent.execute({
        "content": TEST_ARTICLE,
        "genre_classification": genre_result.data["genre_classification"]
    })
    logger.info(f"结构重组Agent: {'✅' if structure_result.success else '❌'}")
    
    if not structure_result.success:
        logger.error(f"结构重组失败: {structure_result.message}")
        return False
    
    # 测试风格改写
    style_agent = StyleRewriterAgent()
    style_result = await style_agent.execute({
        "structure_info": structure_result.data["structure_info"],
        "genre": genre_result.data["genre_classification"].genre
    })
    logger.info(f"风格改写Agent: {'✅' if style_result.success else '❌'}")
    
    if not style_result.success:
        logger.error(f"风格改写失败: {style_result.message}")
        return False
    
    logger.info("✅ 各个Agent测试完成")
    return True

def main():
    """主测试函数"""
    print("🧪 开始系统测试...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 测试各个Agent
        agents_ok = loop.run_until_complete(test_individual_agents())
        
        if not agents_ok:
            print("❌ Agent测试失败")
            return 1
        
        # 测试完整流水线
        pipeline_ok = loop.run_until_complete(test_complete_pipeline())
        
        if pipeline_ok:
            print("✅ 系统测试通过")
            return 0
        else:
            print("❌ 系统测试失败")
            return 1
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return 1
    finally:
        loop.close()

if __name__ == "__main__":
    exit(main())
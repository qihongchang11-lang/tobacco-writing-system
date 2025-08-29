"""
启动脚本
用于启动整个系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main_pipeline import main_pipeline
from knowledge_base import knowledge_manager, data_collector
from utils import settings, get_agent_logger

logger = get_agent_logger("Startup")

async def initialize_system():
    """初始化系统"""
    logger.info("开始初始化中国烟草报改写系统...")
    
    try:
        # 1. 初始化知识库
        logger.info("步骤 1/3: 初始化知识库")
        kb_success = await main_pipeline.initialize_knowledge_base()
        
        if not kb_success:
            logger.warning("知识库初始化失败，将使用示例数据")
            
            # 生成示例数据
            sample_articles = data_collector.generate_sample_articles(10)
            data_collector.add_articles_to_knowledge_base(sample_articles)
            logger.info("已添加示例数据到知识库")
        
        # 2. 验证系统组件
        logger.info("步骤 2/3: 验证系统组件")
        pipeline_stats = main_pipeline.get_pipeline_statistics()
        logger.info(f"流水线包含 {pipeline_stats['agent_count']} 个Agent")
        
        # 3. 系统就绪
        logger.info("步骤 3/3: 系统就绪")
        logger.info("=" * 50)
        logger.info("🎉 中国烟草报风格改写系统启动完成！")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 启动中国烟草报风格改写系统...")
    
    # 异步初始化
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(initialize_system())
        
        if not success:
            print("❌ 系统初始化失败")
            return 1
        
        print("\n📱 启动Web界面...")
        print(f"🌐 请访问: http://localhost:{settings.port}")
        print("⏹️  按 Ctrl+C 停止服务")
        
        # 启动Streamlit应用
        import subprocess
        import os
        
        web_app_path = project_root / "web_interface" / "app.py"
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        # 启动Streamlit
        subprocess.run([
            "streamlit", "run", 
            str(web_app_path),
            "--server.port", str(settings.port),
            "--server.address", settings.host,
            "--server.headless", "true" if not settings.debug else "false"
        ], env=env)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 系统已停止")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    finally:
        loop.close()

if __name__ == "__main__":
    exit(main())
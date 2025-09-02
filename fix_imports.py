"""
路径和导入修复模块
确保所有模块能够正确导入
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加各个子包路径
for subdir in ['agents', 'utils', 'knowledge_base', 'templates']:
    subdir_path = project_root / subdir
    if subdir_path.exists() and str(subdir_path) not in sys.path:
        sys.path.insert(0, str(subdir_path))

# 环境变量设置
os.environ.setdefault('PYTHONPATH', str(project_root))

# 检查关键模块是否可用
def check_imports():
    """检查关键模块导入"""
    try:
        # 基础工具
        from utils import settings, get_agent_logger
        print("✅ Utils模块导入成功")
        
        # Agents
        from agents import GenreClassifierAgent, StyleRewriterAgent
        print("✅ Agents模块导入成功")
        
        # 知识库
        from knowledge_base import knowledge_manager
        print("✅ Knowledge Base模块导入成功")
        
        # 主流水线
        from main_pipeline import main_pipeline
        print("✅ Main Pipeline导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("检查模块导入...")
    check_imports()
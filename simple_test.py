#!/usr/bin/env python3
"""
简化测试脚本 - 验证系统基础功能
"""

print("🚀 中国烟草报风格改写系统 - 测试版")
print("="*50)

try:
    import sys
    print(f"✅ Python版本: {sys.version}")
    
    # 测试基础导入
    try:
        import pathlib
        import datetime
        print("✅ 基础模块导入成功")
    except ImportError as e:
        print(f"❌ 基础模块导入失败: {e}")
        
    # 测试项目结构
    from pathlib import Path
    project_root = Path(__file__).parent
    
    expected_dirs = ['agents', 'knowledge_base', 'utils', 'web_interface']
    for dir_name in expected_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ 目录检查: {dir_name}")
        else:
            print(f"❌ 目录缺失: {dir_name}")
    
    # 测试配置文件
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ 环境配置文件存在")
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "CLAUDE_API_KEY=your_claude_api_key_here" in content:
                print("⚠️  需要配置Claude API密钥")
            else:
                print("✅ API密钥已配置")
    else:
        print("❌ 环境配置文件缺失")
    
    print("\n" + "="*50)
    print("📋 配置指南:")
    print("1. 获取Claude API密钥: https://console.anthropic.com/")
    print("2. 编辑 .env 文件，替换 CLAUDE_API_KEY 的值")
    print("3. 安装依赖: pip install -r requirements.txt")
    print("4. 运行: python run.py")
    print("="*50)
    
except Exception as e:
    print(f"❌ 系统测试失败: {e}")
    import traceback
    traceback.print_exc()
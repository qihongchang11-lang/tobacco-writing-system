#!/usr/bin/env python3
"""
快速改写工具 - 命令行版本
无需复杂配置，直接处理文章
"""

import sys
import os
from pathlib import Path

def quick_rewrite():
    """快速改写入口"""
    
    print("🎯 中国烟草报风格快速改写工具")
    print("="*50)
    
    # 检查参数
    if len(sys.argv) < 2:
        print("使用方法：")
        print(f"  python {sys.argv[0]} '你的文章内容'")
        print(f"  python {sys.argv[0]} --file 文章文件.txt")
        print()
        print("示例：")
        print(f"  python {sys.argv[0]} '某市烟草局最近在数字化建设方面...'")
        return
    
    # 获取文章内容
    if sys.argv[1] == '--file':
        if len(sys.argv) < 3:
            print("❌ 请指定文件路径")
            return
        
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return
            
        with open(file_path, 'r', encoding='utf-8') as f:
            article_content = f.read()
    else:
        article_content = sys.argv[1]
    
    if not article_content.strip():
        print("❌ 文章内容为空")
        return
    
    # 生成改写提示
    prompt = f"""你是中国烟草报的资深编辑，请将以下文章改写为符合烟草报风格的专业稿件。

改写要求：
1. 体裁识别：判断是消息、通讯、还是经验材料
2. 结构优化：标题(15-25字) + 导语(40-60字) + 三段式正文
3. 风格转换：正式、客观、权威的语言风格
4. 规范校对：术语、数字、日期、机构名称规范化

中国烟草报风格特征：
- 语言：正式、客观、简洁有力
- 标题："{"{主体}+{动作}+{成果}"}" 格式
- 导语：包含时间、地点、主体、动作、成效
- 用词：使用"扎实推进""成效显著""持续深化"等规范表达
- 避免：夸张词汇(震撼、惊人)、口语化表达(给力、超赞)
- 数字：万以上用阿拉伯数字，如"3.2万""15.6%""1.5亿元"
- 机构：首次使用全称"XX省烟草专卖局（公司）"

请处理以下文章：

{article_content}

期望输出格式：

### 📋 改写分析
**原文体裁**：[消息/通讯/经验材料]
**主要调整**：[列出3-5个主要修改点]

### 📝 改写结果

---
**[改写后的标题]**

[改写后的导语段落]

[改写后的正文第1段]

[改写后的正文第2段] 

[改写后的正文第3段]
---

### 📊 改写说明
| 位置 | 原表达 | 新表达 | 修改理由 |
|------|--------|--------|----------|

**字数统计**：改写后xxx字
**符合性评估**：结构✅ 用词✅ 格式✅"""
    
    # 输出提示词
    print("📋 已生成改写提示词，请复制以下内容到Claude中：")
    print("="*50)
    print(prompt)
    print("="*50)
    
    # 保存到文件
    output_file = "rewrite_prompt.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"📁 提示词已保存到: {output_file}")
    print("💡 复制该内容到Claude对话中即可获得改写结果")

if __name__ == "__main__":
    quick_rewrite()
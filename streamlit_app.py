"""
云端部署专用的简化版主应用
移除复杂依赖，专注核心改写功能
"""

# 修复 sqlite3 版本兼容性问题
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import streamlit as st
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json

# 设置页面配置
st.set_page_config(
    page_title="中国烟草报风格改写系统 - 云端版",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 基础配置
class SimpleConfig:
    """简化的配置类"""
    def __init__(self):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY", "")
        if not self.claude_api_key:
            st.error("❌ 未配置Claude API密钥，请在Streamlit Cloud的Secrets中添加CLAUDE_API_KEY")
            st.stop()

config = SimpleConfig()

# 简化的改写Agent
class SimpleTobaccoRewriter:
    """简化的烟草报风格改写器"""
    
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
    
    async def rewrite_article(self, content: str, title: str = "", author: str = "") -> Dict[str, Any]:
        """改写文章为烟草报风格"""
        
        prompt = f"""你是中国烟草报的专业编辑，需要将以下文章改写为符合烟草报风格的稿件。

烟草报写作要求：
1. 行业专业性：突出烟草行业特色，使用行业专业术语
2. 政策导向性：体现国家政策和行业发展方向
3. 正面积极性：传递正能量，展现行业发展成就
4. 规范严谨性：语言规范，逻辑清晰，结构完整
5. 实用指导性：对读者具有实际指导意义

请按照以下步骤进行改写：

第一步：体裁分析
- 分析原文体裁类型（新闻报道/政策解读/经验交流/理论文章等）

第二步：结构优化
- 重新组织文章结构，确保逻较清晰
- 添加合适的小标题

第三步：风格改写
- 改写为烟草报风格
- 使用行业专业术语
- 体现政策导向

第四步：质量评估
- 对改写结果进行评分（1-100分）
- 说明评分理由

原文标题：{title}
原文作者：{author}
原文内容：
{content}

请按照上述步骤完成改写，并以JSON格式返回结果：
{{
    "genre_analysis": "体裁分析结果",
    "structure_optimization": "结构优化说明",
    "rewritten_content": "改写后的完整文章",
    "quality_score": 评分数字,
    "quality_analysis": "质量评估说明"
}}"""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model="claude-3-sonnet-20241022",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            result_text = response.content[0].text
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
            except:
                # 如果JSON解析失败，创建基本结构
                result = {
                    "genre_analysis": "分析中出现错误",
                    "structure_optimization": "结构优化中出现错误", 
                    "rewritten_content": result_text,
                    "quality_score": 0,
                    "quality_analysis": "评估中出现错误"
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"改写过程中出现错误: {str(e)}",
                "genre_analysis": "错误",
                "structure_optimization": "错误",
                "rewritten_content": "改写失败",
                "quality_score": 0,
                "quality_analysis": "处理失败"
            }

# 创建改写器实例
@st.cache_resource
def get_rewriter():
    return SimpleTobaccoRewriter(config.claude_api_key)

def main():
    """主应用"""
    
    # 页面标题
    st.title("🎯 中国烟草报风格改写系统")
    st.markdown("**云端版** - 专业的烟草行业文章改写工具")
    
    # 侧边栏系统信息
    with st.sidebar:
        st.header("📊 系统信息")
        st.info("**简化云端版本**\n\n✅ 核心改写功能\n✅ 烟草报风格\n✅ 质量评估\n\n⚠️ 已移除复杂依赖以确保稳定运行")
        
        st.header("📋 使用提示")
        st.markdown("""
        1. 输入要改写的文章内容
        2. 填写标题和作者（可选）
        3. 点击"开始改写"按钮
        4. 等待系统处理（约30-60秒）
        5. 查看改写结果和质量评估
        """)
    
    # 主要输入区域
    st.header("📝 文章输入")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        content = st.text_area(
            "文章内容",
            placeholder="请输入要改写的文章内容...",
            height=300,
            help="支持中文文章，建议长度在500-5000字"
        )
    
    with col2:
        title = st.text_input(
            "文章标题（可选）",
            placeholder="请输入文章标题..."
        )
        
        author = st.text_input(
            "作者（可选）", 
            placeholder="请输入作者姓名..."
        )
    
    # 改写按钮
    if st.button("🚀 开始改写", type="primary", use_container_width=True):
        if not content.strip():
            st.error("❌ 请输入文章内容")
            return
        
        if len(content) < 50:
            st.warning("⚠️ 文章内容过短，建议至少50字以上")
            return
        
        # 显示处理进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 获取改写器
            rewriter = get_rewriter()
            
            # 执行改写
            status_text.text("🎭 正在分析文章体裁...")
            progress_bar.progress(25)
            
            status_text.text("🏗️ 正在优化文章结构...")
            progress_bar.progress(50)
            
            status_text.text("✨ 正在改写为烟草报风格...")
            progress_bar.progress(75)
            
            result = await rewriter.rewrite_article(content, title, author)
            
            status_text.text("📊 正在评估改写质量...")
            progress_bar.progress(100)
            
            # 清除进度显示
            progress_bar.empty()
            status_text.empty()
            
            # 显示结果
            if "error" in result:
                st.error(f"❌ {result['error']}")
                return
            
            # 改写结果展示
            st.header("📄 改写结果")
            
            # 结果标签页
            tab1, tab2, tab3 = st.tabs(["✨ 改写结果", "📊 分析报告", "💾 导出下载"])
            
            with tab1:
                st.markdown("### 改写后的文章")
                st.markdown(result.get("rewritten_content", ""))
            
            with tab2:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🎭 体裁分析")
                    st.info(result.get("genre_analysis", ""))
                    
                    st.markdown("### 🏗️ 结构优化")
                    st.info(result.get("structure_optimization", ""))
                
                with col2:
                    st.markdown("### 📊 质量评估")
                    score = result.get("quality_score", 0)
                    
                    # 质量分数显示
                    if score >= 85:
                        st.success(f"🌟 优秀：{score}分")
                    elif score >= 70:
                        st.info(f"👍 良好：{score}分")
                    elif score >= 60:
                        st.warning(f"⚠️ 及格：{score}分")
                    else:
                        st.error(f"❌ 需要改进：{score}分")
                    
                    st.markdown("**评估说明：**")
                    st.write(result.get("quality_analysis", ""))
            
            with tab3:
                st.markdown("### 📁 文件下载")
                
                # 准备下载内容
                download_content = f"""# 中国烟草报风格改写结果

## 原文信息
- 标题：{title or '未提供'}
- 作者：{author or '未提供'}
- 改写时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 体裁分析
{result.get("genre_analysis", "")}

## 结构优化
{result.get("structure_optimization", "")}

## 改写结果
{result.get("rewritten_content", "")}

## 质量评估
- 评分：{result.get("quality_score", 0)}/100
- 说明：{result.get("quality_analysis", "")}

---
生成工具：中国烟草报风格改写系统（云端版）
"""
                
                # 下载按钮
                st.download_button(
                    label="📥 下载Markdown格式",
                    data=download_content,
                    file_name=f"改写稿件_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown"
                )
                
                st.info("💡 提示：下载后可以导入到Word中进行进一步编辑")
        
        except Exception as e:
            st.error(f"❌ 处理失败：{str(e)}")
            st.info("请稍后重试或联系技术支持")

if __name__ == "__main__":
    main()
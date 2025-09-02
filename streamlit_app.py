"""
云端部署专用的主应用 - Streamlit Cloud版本
优化为云端部署，简化配置，提升性能
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

# 路径修复
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置页面配置
st.set_page_config(
    page_title="中国烟草报风格改写系统 - 云端版",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_cloud_environment():
    """检查云端环境配置"""
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key or claude_api_key == "":
        return False, "未配置Claude API密钥"
    return True, "环境配置正常"

def init_session_state():
    """初始化会话状态"""
    if "processing_result" not in st.session_state:
        st.session_state.processing_result = None
    if "environment_checked" not in st.session_state:
        st.session_state.environment_checked = False
    if "pipeline_initialized" not in st.session_state:
        st.session_state.pipeline_initialized = False

@st.cache_resource
def get_main_pipeline():
    """获取主流水线实例，带错误处理"""
    try:
        st.info("正在初始化Agent系统...")
        
        # 逐步导入，便于错误诊断
        try:
            from main_pipeline import main_pipeline
            st.success("✅ 主流水线导入成功")
            return main_pipeline
        except ImportError as e:
            st.error(f"❌ 主流水线导入失败: {e}")
            # 尝试备用导入路径
            try:
                sys.path.append(str(Path(__file__).parent))
                from main_pipeline import main_pipeline
                st.success("✅ 备用路径导入成功")
                return main_pipeline
            except Exception as e2:
                st.error(f"❌ 备用导入也失败: {e2}")
                return None
                
    except Exception as e:
        st.error(f"❌ 系统初始化失败: {e}")
        return None

async def process_article_cloud(content, title="", author=""):
    """云端版本的文章处理 - 调用完整Agent系统"""
    try:
        # 获取流水线
        pipeline = get_main_pipeline()
        if not pipeline:
            return None
            
        # 初始化知识库（如果需要）
        if not st.session_state.pipeline_initialized:
            with st.spinner("正在初始化知识库和向量数据库..."):
                try:
                    await pipeline.initialize_knowledge_base()
                    st.session_state.pipeline_initialized = True
                    st.success("✅ 知识库初始化成功")
                except Exception as e:
                    st.warning(f"⚠️ 知识库初始化失败: {e}")
                    st.info("将使用基础模式运行")
        
        # 处理文章
        st.info("开始处理文章，调用完整Agent流水线...")
        result = await pipeline.process_article(content, title, author)
        
        if result:
            st.success("✅ Agent流水线处理完成")
        return result
            
    except Exception as e:
        st.error(f"❌ 处理失败: {str(e)}")
        st.error(f"详细错误信息: {type(e).__name__}")
        return None

def sync_process_article(content, title="", author=""):
    """同步包装器，带详细错误处理"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(process_article_cloud(content, title, author))
        finally:
            loop.close()
    except Exception as e:
        st.error(f"❌ 同步处理失败: {e}")
        return None

def show_system_diagnostics():
    """显示系统诊断信息"""
    with st.expander("🔧 系统诊断信息", expanded=False):
        st.write("**Python路径:**")
        for path in sys.path[:5]:  # 只显示前5个路径
            st.code(path)
        
        st.write("**环境变量:**")
        claude_key = os.getenv('CLAUDE_API_KEY', '')
        st.write(f"CLAUDE_API_KEY: {'✅ 已配置' if claude_key else '❌ 未配置'}")
        
        st.write("**模块检查:**")
        modules_to_check = [
            'anthropic', 'streamlit', 'pandas', 'numpy', 
            'pydantic', 'loguru', 'requests'
        ]
        
        for module in modules_to_check:
            try:
                __import__(module)
                st.write(f"✅ {module}")
            except ImportError:
                st.write(f"❌ {module}")

def main():
    """主应用"""
    init_session_state()
    
    # 页面标题
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>🎯 中国烟草报风格改写系统</h1>
        <p style="color: #666; font-size: 18px;">基于Claude多Agent架构的智能公文写作工具 - 云端版</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 检查环境配置
    if not st.session_state.environment_checked:
        env_ok, env_msg = check_cloud_environment()
        if not env_ok:
            st.error(f"❌ {env_msg}")
            st.markdown("""
            ### 🔧 配置说明
            此应用需要Claude API密钥才能运行。请在Streamlit Cloud的Secrets中配置：
            ```toml
            CLAUDE_API_KEY = "sk-ant-api03-你的密钥"
            ```
            """)
            show_system_diagnostics()
            return
        else:
            st.success(f"✅ {env_msg}")
            st.session_state.environment_checked = True
    
    # 侧边栏信息
    with st.sidebar:
        st.header("📚 系统信息")
        st.info("""
        **核心功能**:
        - 🎭 体裁识别Agent
        - 🏗️ 结构重组Agent
        - ✨ 风格改写Agent
        - 🔍 事实校对Agent
        - 📄 版式导出Agent
        - 📊 质量评估Agent
        """)
        
        st.header("🎯 使用提示")
        st.write("""
        1. 输入要改写的文章内容
        2. 点击"开始改写"按钮
        3. 等待系统处理（约30-60秒）
        4. 查看完整的Agent处理结果
        """)
        
        show_system_diagnostics()
    
    # 主内容区域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 文章改写")
        
        # 输入表单
        with st.form("article_form"):
            title = st.text_input("文章标题（可选）", placeholder="请输入文章标题...")
            
            content = st.text_area(
                "文章内容",
                placeholder="""请输入您要改写的文章内容...

示例：
某市烟草局最近在数字化建设方面取得了很好的成果。他们通过引入新的信息系统，大大提高了工作效率，员工们都觉得很给力。这个项目从去年开始，花了不少时间和精力，现在终于看到了成效。下一步，他们还打算继续扩大数字化的范围，争取在更多领域实现突破。""",
                height=200
            )
            
            author = st.text_input("作者（可选）", placeholder="请输入作者姓名...")
            
            submitted = st.form_submit_button("🚀 开始改写", type="primary", use_container_width=True)
        
        # 处理提交
        if submitted:
            if not content.strip():
                st.error("❌ 请输入文章内容")
            elif len(content.strip()) < 50:
                st.error("❌ 文章内容太短，请输入至少50字的内容")
            else:
                # 显示进度
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    stages = [
                        "🎭 启动体裁识别Agent...",
                        "🏗️ 启动结构重组Agent...",
                        "✨ 启动风格改写Agent...", 
                        "🔍 启动事实校对Agent...",
                        "📄 启动版式导出Agent...",
                        "📊 启动质量评估Agent..."
                    ]
                    
                    for i, stage in enumerate(stages):
                        status_text.text(stage)
                        progress_bar.progress((i + 1) / len(stages))
                    
                    # 实际处理
                    try:
                        result = sync_process_article(content, title, author)
                        
                        if result and hasattr(result, 'final_content') and result.final_content:
                            st.session_state.processing_result = result
                            progress_bar.progress(1.0)
                            status_text.text("✅ 完整Agent流水线处理完成！")
                            st.rerun()
                        else:
                            st.error("❌ Agent流水线处理失败")
                            
                    except Exception as e:
                        st.error(f"❌ 处理异常: {str(e)}")
                        st.error("请检查系统诊断信息或联系技术支持")
    
    with col2:
        st.header("📊 处理状态")
        
        if st.session_state.processing_result:
            result = st.session_state.processing_result
            
            # 基础信息
            st.success("✅ Agent流水线处理完成")
            
            if hasattr(result, 'processing_time') and result.processing_time:
                total_time = result.processing_time.get('total', 0)
                st.metric("处理耗时", f"{total_time:.1f}秒")
            
            if hasattr(result, 'quality_result') and result.quality_result:
                if hasattr(result.quality_result, 'metrics'):
                    score = result.quality_result.metrics.overall_score
                    st.metric("质量评分", f"{score:.1%}")
                    
                    if score >= 0.8:
                        st.success("🎉 改写质量优秀")
                    elif score >= 0.7:
                        st.info("✅ 改写质量良好") 
                    else:
                        st.warning("⚠️ 改写质量一般")
        else:
            st.info("等待Agent流水线处理...")
    
    # 显示处理结果
    if st.session_state.processing_result:
        show_results(st.session_state.processing_result)

def show_results(result):
    """显示处理结果"""
    st.markdown("---")
    st.header("🎉 Agent流水线处理结果")
    
    # 结果标签页
    tab1, tab2, tab3 = st.tabs(["📝 最终稿件", "📊 详细分析", "💾 导出下载"])
    
    with tab1:
        if hasattr(result, 'final_content') and result.final_content:
            st.subheader("改写后的文章")
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #28a745;">
                {result.final_content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            # 字数统计
            word_count = len(result.final_content)
            st.info(f"📊 改写后字数：{word_count}字")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # 体裁识别结果
            if hasattr(result, 'genre_result') and result.genre_result:
                st.subheader("🎭 体裁识别Agent结果")
                if hasattr(result.genre_result, 'genre'):
                    st.write(f"**识别结果**: {result.genre_result.genre}")
                if hasattr(result.genre_result, 'confidence'):
                    st.write(f"**置信度**: {result.genre_result.confidence:.1%}")
                if hasattr(result.genre_result, 'reasoning'):
                    st.write(f"**分析**: {result.genre_result.reasoning}")
        
        with col2:
            # 质量评估
            if hasattr(result, 'quality_result') and result.quality_result:
                st.subheader("📊 质量评估Agent结果")
                if hasattr(result.quality_result, 'metrics'):
                    metrics = result.quality_result.metrics
                    
                    if hasattr(metrics, 'title_completeness'):
                        st.progress(metrics.title_completeness, text=f"标题完整性 ({metrics.title_completeness:.1%})")
                    if hasattr(metrics, 'lead_quality'):
                        st.progress(metrics.lead_quality, text=f"导语质量 ({metrics.lead_quality:.1%})")
                    if hasattr(metrics, 'content_coherence'):
                        st.progress(metrics.content_coherence, text=f"内容连贯性 ({metrics.content_coherence:.1%})")
                    if hasattr(metrics, 'style_consistency'):
                        st.progress(metrics.style_consistency, text=f"风格一致性 ({metrics.style_consistency:.1%})")
        
        # 改进建议
        if hasattr(result, 'quality_result') and result.quality_result and hasattr(result.quality_result, 'suggestions') and result.quality_result.suggestions:
            st.subheader("💡 改进建议")
            for suggestion in result.quality_result.suggestions:
                st.write(f"• {suggestion}")
    
    with tab3:
        st.subheader("💾 导出选项")
        
        if hasattr(result, 'final_content') and result.final_content:
            # 文本下载
            st.download_button(
                label="📄 下载TXT文件",
                data=result.final_content,
                file_name=f"改写稿件_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
            
            # Markdown下载
            title_text = ""
            if hasattr(result, 'input_article') and result.input_article and hasattr(result.input_article, 'title'):
                title_text = result.input_article.title or '改写稿件'
            else:
                title_text = '改写稿件'
                
            markdown_content = f"""# {title_text}

{result.final_content}

---
*改写时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}*  
*系统: 中国烟草报风格改写系统（完整Agent版）*
"""
            st.download_button(
                label="📝 下载Markdown文件",
                data=markdown_content,
                file_name=f"改写稿件_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown"
            )
            
            st.info("💡 提示：下载后可以导入到Word中进行进一步编辑")

if __name__ == "__main__":
    main()

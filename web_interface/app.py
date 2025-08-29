"""
主Web界面 - Streamlit应用
提供用户友好的界面来使用烟草报改写系统
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from main_pipeline import main_pipeline
from utils import format_confidence_score, count_words
from knowledge_base import knowledge_manager

st.set_page_config(
    page_title="中国烟草报风格改写系统",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """初始化会话状态"""
    if "processing_record" not in st.session_state:
        st.session_state.processing_record = None
    if "knowledge_base_initialized" not in st.session_state:
        st.session_state.knowledge_base_initialized = False

async def process_article_async(content, title, author):
    """异步处理文章"""
    return await main_pipeline.process_article(content, title, author)

def process_article_sync(content, title, author):
    """同步包装异步处理"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_article_async(content, title, author))
    finally:
        loop.close()

async def init_knowledge_base_async():
    """异步初始化知识库"""
    return await main_pipeline.initialize_knowledge_base()

def init_knowledge_base_sync():
    """同步包装异步初始化"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(init_knowledge_base_async())
    finally:
        loop.close()

def main():
    """主界面"""
    init_session_state()
    
    # 页面标题
    st.title("🎯 中国烟草报风格改写系统")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 系统设置")
        
        # 知识库状态
        st.subheader("📚 知识库状态")
        if not st.session_state.knowledge_base_initialized:
            if st.button("初始化知识库", type="primary"):
                with st.spinner("正在初始化知识库..."):
                    success = init_knowledge_base_sync()
                    if success:
                        st.session_state.knowledge_base_initialized = True
                        st.success("知识库初始化成功！")
                        st.rerun()
                    else:
                        st.error("知识库初始化失败，请检查配置")
        else:
            st.success("✅ 知识库已就绪")
        
        # 系统统计
        st.subheader("📊 处理统计")
        records = main_pipeline.list_processing_records()
        st.metric("处理文章数", len(records))
        
        if records:
            successful = sum(1 for r in records.values() if r.final_content)
            st.metric("成功处理", successful)
            st.metric("成功率", f"{successful/len(records)*100:.1f}%")
    
    # 主内容区域
    tab1, tab2, tab3 = st.tabs(["📝 文章改写", "📋 处理记录", "ℹ️ 系统信息"])
    
    with tab1:
        st.header("文章改写")
        
        # 输入区域
        col1, col2 = st.columns([3, 1])
        
        with col1:
            title = st.text_input("文章标题（可选）", placeholder="请输入文章标题...")
            
            content = st.text_area(
                "文章内容",
                placeholder="请输入您要改写的文章内容...\n\n系统会自动识别体裁，重新组织结构，并改写为符合中国烟草报风格的专业稿件。",
                height=300
            )
            
            author = st.text_input("作者（可选）", placeholder="请输入作者姓名...")
        
        with col2:
            st.markdown("### 📊 文本统计")
            if content:
                word_count = count_words(content)
                st.metric("字数统计", f"{word_count}字")
                
                if word_count < 100:
                    st.warning("⚠️ 文章内容较短")
                elif word_count > 5000:
                    st.warning("⚠️ 文章内容较长")
                else:
                    st.success("✅ 文章长度适中")
            else:
                st.info("请输入文章内容")
        
        # 处理按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            process_button = st.button(
                "🚀 开始改写",
                type="primary",
                disabled=not content or not st.session_state.knowledge_base_initialized,
                use_container_width=True
            )
        
        # 处理文章
        if process_button:
            if not content.strip():
                st.error("❌ 请输入文章内容")
            else:
                with st.spinner("正在处理文章，请稍候..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 模拟处理进度
                    stages = [
                        "体裁识别中...",
                        "结构重组中...", 
                        "风格改写中...",
                        "事实校对中...",
                        "格式导出中...",
                        "质量评估中..."
                    ]
                    
                    for i, stage in enumerate(stages):
                        status_text.text(stage)
                        progress_bar.progress((i + 1) / len(stages))
                        
                    # 实际处理
                    try:
                        record = process_article_sync(content, title, author)
                        st.session_state.processing_record = record
                        
                        progress_bar.progress(1.0)
                        status_text.text("处理完成！")
                        
                        st.success("✅ 文章处理完成！")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 处理失败: {str(e)}")
        
        # 显示处理结果
        if st.session_state.processing_record:
            show_processing_results(st.session_state.processing_record)
    
    with tab2:
        show_processing_history()
    
    with tab3:
        show_system_info()

def show_processing_results(record):
    """显示处理结果"""
    st.header("🎉 处理结果")
    
    # 基础信息
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("处理状态", record.current_stage.value)
    with col2:
        total_time = record.processing_time.get("total", 0)
        st.metric("处理耗时", f"{total_time:.2f}秒")
    with col3:
        if record.quality_result:
            score = record.quality_result.metrics.overall_score
            st.metric("质量评分", f"{score:.1%}")
    
    # 详细结果
    if record.genre_result:
        st.subheader("🎭 体裁识别结果")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**识别体裁**: {record.genre_result.genre.value}")
            st.info(f"**置信度**: {format_confidence_score(record.genre_result.confidence)}")
        with col2:
            st.write(f"**识别理由**: {record.genre_result.reasoning}")
    
    if record.style_result:
        st.subheader("✨ 风格改写结果")
        
        # 标题对比
        st.write("**标题优化**:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("*原标题*:")
            st.text(record.input_article.title or "未提供")
        with col2:
            st.write("*改写后*:")
            st.text(record.style_result.rewritten_title)
        
        # 导语对比
        st.write("**导语优化**:")
        col1, col2 = st.columns(2)
        with col1:
            st.write("*原导语*:")
            st.text_area("", record.structure_result.lead if record.structure_result else "", height=100, key="orig_lead", disabled=True)
        with col2:
            st.write("*改写后*:")
            st.text_area("", record.style_result.rewritten_lead, height=100, key="new_lead", disabled=True)
        
        # 改写说明
        if record.style_result.style_changes:
            st.write("**主要修改**:")
            for change in record.style_result.style_changes:
                st.write(f"• {change}")
    
    if record.fact_check_result:
        st.subheader("🔍 事实校对结果")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("准确性评分", f"{record.fact_check_result.overall_score:.1%}")
        with col2:
            st.metric("发现问题", len(record.fact_check_result.issues))
        
        if record.fact_check_result.issues:
            st.write("**问题详情**:")
            for i, issue in enumerate(record.fact_check_result.issues):
                with st.expander(f"问题 {i+1}: {issue.issue_type}"):
                    st.write(f"**位置**: {issue.location}")
                    st.write(f"**原文**: {issue.original_text}")
                    st.write(f"**建议**: {issue.suggested_correction}")
                    st.write(f"**严重程度**: {issue.severity}")
                    st.write(f"**说明**: {issue.explanation}")
    
    if record.quality_result:
        st.subheader("📊 质量评估结果")
        
        metrics = record.quality_result.metrics
        
        # 评分雷达图（简化显示）
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**各项指标评分**:")
            st.progress(metrics.title_completeness, text=f"标题完整性 ({metrics.title_completeness:.1%})")
            st.progress(metrics.lead_quality, text=f"导语质量 ({metrics.lead_quality:.1%})")
            st.progress(metrics.content_coherence, text=f"内容连贯性 ({metrics.content_coherence:.1%})")
            
        with col2:
            st.write("**&nbsp;**")
            st.progress(metrics.style_consistency, text=f"风格一致性 ({metrics.style_consistency:.1%})")
            st.progress(metrics.factual_accuracy, text=f"事实准确性 ({metrics.factual_accuracy:.1%})")
            st.progress(metrics.format_compliance, text=f"格式规范性 ({metrics.format_compliance:.1%})")
        
        # 改进建议
        if record.quality_result.suggestions:
            st.write("**改进建议**:")
            for suggestion in record.quality_result.suggestions:
                st.write(f"• {suggestion}")
    
    # 最终内容
    if record.final_content:
        st.subheader("📄 最终稿件")
        st.text_area("", record.final_content, height=400, key="final_content")
        
        # 下载按钮
        if record.export_path and os.path.exists(record.export_path):
            with open(record.export_path, "rb") as file:
                st.download_button(
                    label="📥 下载DOCX文件",
                    data=file.read(),
                    file_name=os.path.basename(record.export_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

def show_processing_history():
    """显示处理历史"""
    st.header("📋 处理记录")
    
    records = main_pipeline.list_processing_records()
    
    if not records:
        st.info("暂无处理记录")
        return
    
    # 按时间排序
    sorted_records = sorted(records.values(), key=lambda x: x.created_at, reverse=True)
    
    for record in sorted_records:
        with st.expander(f"📝 {record.input_article.title or '无标题'} - {record.created_at.strftime('%Y-%m-%d %H:%M')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**状态**: {record.current_stage.value}")
                st.write(f"**字数**: {count_words(record.input_article.content)}字")
            
            with col2:
                if record.genre_result:
                    st.write(f"**体裁**: {record.genre_result.genre.value}")
                    st.write(f"**置信度**: {format_confidence_score(record.genre_result.confidence)}")
            
            with col3:
                if record.quality_result:
                    st.write(f"**质量评分**: {record.quality_result.metrics.overall_score:.1%}")
                    st.write(f"**是否通过**: {'✅' if record.quality_result.passed else '❌'}")
            
            if st.button(f"查看详情 - {record.id[:8]}", key=f"view_{record.id}"):
                st.session_state.processing_record = record
                st.rerun()

def show_system_info():
    """显示系统信息"""
    st.header("ℹ️ 系统信息")
    
    # 系统架构
    st.subheader("🏗️ 系统架构")
    st.info("""
    **多Agent流水线架构**:
    1. 体裁识别Agent - 自动识别文章类型
    2. 结构重组Agent - 优化文章结构布局
    3. 风格改写Agent - 转换为烟草报风格
    4. 事实校对Agent - 检查准确性和规范性
    5. 版式导出Agent - 生成标准格式文档
    6. 质量评估Agent - 综合评分和建议
    """)
    
    # 知识库信息
    st.subheader("📚 知识库")
    try:
        kb_stats = knowledge_manager.get_knowledge_statistics()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("知识条目", kb_stats.get("faiss_entries", 0))
        with col2:
            st.metric("向量维度", kb_stats.get("embedding_dimension", 0))
        with col3:
            st.metric("模型", "MiniLM-L12-v2")
        
        if kb_stats.get("category_distribution"):
            st.write("**知识库分布**:")
            for category, count in kb_stats["category_distribution"].items():
                st.write(f"• {category}: {count}条")
                
    except Exception as e:
        st.error(f"获取知识库信息失败: {e}")
    
    # 流水线统计
    st.subheader("📊 流水线统计")
    try:
        pipeline_stats = main_pipeline.get_pipeline_statistics()
        
        st.write(f"**Agent数量**: {pipeline_stats['agent_count']}")
        
        if pipeline_stats.get("agent_stats"):
            for agent_stat in pipeline_stats["agent_stats"]:
                with st.expander(f"🤖 {agent_stat['agent_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("总请求数", agent_stat["total_requests"])
                        st.metric("成功次数", agent_stat["success_count"])
                    with col2:
                        st.metric("成功率", f"{agent_stat['success_rate']:.1%}")
                        st.metric("平均耗时", f"{agent_stat['average_processing_time']:.2f}s")
                        
    except Exception as e:
        st.error(f"获取流水线统计失败: {e}")

if __name__ == "__main__":
    main()
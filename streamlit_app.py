"""
云端部署专用的主应用 - 动态Agent系统
根据可用依赖自动选择最佳运行模式
"""

# SQLite修复
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import streamlit as st
import asyncio
import html
import os
import requests
from datetime import datetime
from pathlib import Path

# 路径修复
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入动态加载器；ZIP main 中可能没有该模块，本地运行时降级到 FastAPI 客户端。
try:
    from dynamic_loader import get_dynamic_loader
except ImportError:
    get_dynamic_loader = None

# 设置页面配置
st.set_page_config(
    page_title="东方烟草报 / 新华财经风格改写工具",
    page_icon="稿",
    layout="wide",
    initial_sidebar_state="expanded"
)

SAMPLE_TEXT = (
    "某市烟草专卖局近日围绕客户服务、市场监管和数字化转型开展专项行动，"
    "通过完善服务机制、加强市场走访、提升数据分析能力，进一步提高终端服务质量和市场治理水平。"
)

STYLE_TO_GENRE = {
    "东方烟草报": "要闻",
    "新华财经": "新华财经",
}

ERROR_HINTS = {
    401: "模型 Key 认证失败，请检查开发副本 .env 中的 OPENAI_API_KEY。",
    404: "模型名或接口路径错误，请检查 OPENAI_MODEL 和 OPENAI_BASE_URL。",
    429: "请求过于频繁或额度限制，请稍后重试或检查 DeepSeek 额度。",
    500: "后端生成失败，请查看 8082 后端 PowerShell 日志。",
}


def inject_local_styles():
    """注入本地工作台样式，仅影响 Streamlit 前端展示。"""
    st.markdown(
        """
        <style>
        :root {
            --ink: #102a43;
            --muted: #62748a;
            --line: #e3e8ef;
            --panel: #ffffff;
            --soft: #f5f7fa;
            --brand: #0f3d5e;
            --brand-2: #123c55;
            --accent: #2f6f5e;
            --success-bg: #ecf7f1;
            --info-bg: #eef5fa;
            --shadow: 0 16px 40px rgba(16, 42, 67, 0.08);
            --soft-shadow: 0 8px 22px rgba(16, 42, 67, 0.06);
        }
        .stApp {
            background: #f5f7fa;
            color: var(--ink);
            font-size: 16px;
        }
        [data-testid="stHeader"] {
            background: rgba(245, 247, 250, 0.88);
            backdrop-filter: blur(10px);
        }
        .main .block-container {
            max-width: 1260px !important;
            padding: 2.25rem 2.2rem 3.6rem 2.2rem;
        }
        [data-testid="stSidebar"] {
            background: #fbfcfe;
            border-right: 1px solid var(--line);
            font-size: 15px;
        }
        [data-testid="stSidebarContent"] {
            padding: 1.7rem 1.05rem 2rem 1.05rem;
        }
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--brand);
            letter-spacing: 0;
        }
        [data-testid="stSidebar"] h2 {
            font-size: 21px;
        }
        [data-testid="stSidebar"] h3 {
            font-size: 18px;
        }
        div[data-testid="stMarkdownContainer"] p {
            font-size: 15.5px;
            line-height: 1.65;
        }
        label,
        .stRadio label,
        .stCheckbox label,
        [data-testid="stWidgetLabel"] {
            font-size: 15px !important;
            color: #20364a !important;
        }
        .hero-card {
            position: relative;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 28px 32px 26px 32px;
            margin-bottom: 22px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        .hero-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 5px;
            background: #0f3d5e;
        }
        .hero-kicker {
            color: var(--accent);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: .02em;
            margin-bottom: 8px;
        }
        .hero-card h1 {
            margin: 0 0 8px 0;
            color: #102f47;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 0;
            line-height: 1.25;
        }
        .hero-card p {
            margin: 0;
            color: var(--muted);
            font-size: 16px;
            line-height: 1.65;
        }
        .status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }
        .status-pill {
            border: 1px solid #d5e1ea;
            background: #f0f5f8;
            color: #173a52;
            border-radius: 999px;
            padding: 7px 13px;
            font-size: 13px;
            font-weight: 650;
            line-height: 1.3;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .status-pill.ok {
            background: var(--success-bg);
            border-color: #c8e4d4;
            color: #1d5d43;
        }
        .sidebar-title {
            color: var(--brand);
            font-size: 21px;
            font-weight: 750;
            margin: 0 0 4px 0;
        }
        .sidebar-subtitle {
            color: #7a8796;
            font-size: 13px;
            line-height: 1.55;
            margin-bottom: 14px;
        }
        .sidebar-section-title {
            color: #18364c;
            font-size: 14px;
            font-weight: 750;
            margin-bottom: 8px;
        }
        .endpoint-box {
            background: #f7fafc;
            border: 1px solid var(--line);
            border-radius: 8px;
            color: #27465f;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12.5px;
            line-height: 1.5;
            padding: 10px 11px;
            word-break: break-all;
            margin: 7px 0 10px 0;
        }
        .status-card {
            background: #f8fafc;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 12px 13px;
        }
        .status-card strong {
            display: block;
            color: #102a43;
            font-size: 28px;
            line-height: 1.15;
            margin: 5px 0 11px 0;
        }
        .status-card span {
            display: block;
            color: #7a8796;
            font-size: 13px;
            line-height: 1.6;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid var(--line) !important;
            border-radius: 14px !important;
            box-shadow: var(--soft-shadow);
            padding: 1.05rem 1.15rem 1.15rem 1.15rem;
        }
        .section-title {
            color: #143c5a;
            font-size: 20px;
            font-weight: 750;
            margin: 0 0 5px 0;
        }
        .section-caption {
            color: var(--muted);
            font-size: 14.5px;
            line-height: 1.65;
            margin-bottom: 14px;
        }
        .panel-heading {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .panel-badge {
            border: 1px solid #d7e1e8;
            background: #f3f7fa;
            color: #31536a;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
        }
        .char-counter {
            color: #748292;
            font-size: 13.5px;
            margin: 8px 0 12px 0;
        }
        .result-title {
            color: #102f47;
            font-size: 26px;
            font-weight: 700;
            line-height: 1.35;
        }
        .result-title-card {
            background: #f8fbfd;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 15px 16px;
            margin: 4px 0 14px 0;
        }
        .mini-label {
            color: #62748a;
            font-size: 13px;
            font-weight: 750;
            margin: 0 0 7px 0;
        }
        .lead-box {
            background: #eef7f3;
            border-left: 4px solid var(--accent);
            padding: 15px 17px;
            border-radius: 8px;
            color: #26343d;
            font-size: 16px;
            line-height: 1.75;
            margin-bottom: 14px;
        }
        .body-paragraph {
            font-size: 17px;
            line-height: 1.9;
            color: #222b33;
            margin: 0 0 15px 0;
        }
        .empty-state {
            background: #f2f6fa;
            border: 1px dashed #cad6e2;
            border-radius: 12px;
            padding: 34px 24px;
            text-align: center;
            margin-top: 8px;
        }
        .empty-title {
            color: #173a52;
            font-size: 20px;
            font-weight: 750;
            margin-bottom: 8px;
        }
        .empty-copy {
            color: #6f7f90;
            font-size: 14.5px;
            line-height: 1.7;
        }
        div.stButton > button,
        div.stDownloadButton > button {
            border-radius: 8px;
            font-size: 15px !important;
            font-weight: 650;
            min-height: 38px;
            border: 1px solid #d6dee8;
            background: #ffffff;
            color: #19364d;
            box-shadow: 0 3px 10px rgba(16, 42, 67, 0.04);
            transition: all 120ms ease;
        }
        div.stButton > button[kind="primary"] {
            background: #0f3d5e;
            border: 1px solid #0f3d5e;
            color: #ffffff;
            border-radius: 9px;
            font-weight: 650;
            min-height: 44px;
            box-shadow: 0 10px 24px rgba(15, 61, 94, 0.2);
        }
        div.stButton > button[kind="primary"]:hover {
            background: #0b334f;
            border-color: #0b334f;
            color: #ffffff;
            transform: translateY(-1px);
        }
        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
            border-color: #aebdca;
            background: #f8fafc;
            color: #102a43;
        }
        textarea {
            border-radius: 8px !important;
            border-color: #d8e1ea !important;
            background: #fbfcfe !important;
            font-size: 16px !important;
            line-height: 1.75 !important;
        }
        textarea:focus {
            border-color: #7aa0b8 !important;
            box-shadow: 0 0 0 1px rgba(15, 61, 94, 0.12) !important;
        }
        code {
            color: #24445b;
            font-size: 13.5px;
        }
        .stAlert {
            border-radius: 10px;
        }
        @media (max-width: 900px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .hero-card {
                padding: 24px 22px;
            }
            .hero-card h1 {
                font-size: 27px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_local_state():
    defaults = {
        "draft_text": "",
        "rewrite_result": None,
        "last_error": None,
        "elapsed_seconds": None,
        "backend_status": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def get_backend_base() -> str:
    return os.getenv("NEWS_TOBACCO_BASE", "http://localhost:8082").rstrip("/")


def check_backend_status(backend_base: str) -> dict:
    try:
        response = requests.get(f"{backend_base}/health", timeout=5)
        if response.ok:
            data = response.json()
            return {"ok": bool(data.get("ok")), "detail": data}
        return {"ok": False, "status_code": response.status_code, "detail": response.text}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def friendly_error(status_code: int | None, detail: str) -> str:
    if status_code in ERROR_HINTS:
        return ERROR_HINTS[status_code]
    if status_code is None:
        return "无法连接后端，请确认 8082 后端服务是否启动。"
    return f"请求失败，HTTP {status_code}。请查看后端日志。"


def result_to_text(data: dict) -> str:
    title = data.get("title", "")
    lead = data.get("lead", "")
    body = data.get("body", {})
    paragraphs = body.get("paragraphs") or []
    if not paragraphs and body.get("raw"):
        paragraphs = [body["raw"]]
    parts = []
    if title:
        parts.append(title)
    if lead:
        parts.append(lead)
    parts.extend(str(p) for p in paragraphs if str(p).strip())
    return "\n\n".join(parts)

def check_cloud_environment():
    """检查云端环境配置"""
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if not claude_api_key or claude_api_key == "":
        return False, "未配置Claude API密钥"
    return True, "环境配置正常"

def render_fastapi_client():
    """本地正式工作台：直接调用开发版 FastAPI 新闻改写后端。"""
    inject_local_styles()
    ensure_local_state()

    backend_base = get_backend_base()
    endpoint = f"{backend_base}/rewrite"
    model_name = os.getenv("OPENAI_MODEL", "deepseek-v4-pro")

    if st.session_state.backend_status is None:
        st.session_state.backend_status = check_backend_status(backend_base)
    backend_ok = bool(st.session_state.backend_status.get("ok"))
    backend_label = "可用" if backend_ok else "不可用"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-kicker">稿件改写工作台</div>
            <h1>东方烟草报 / 新华财经风格改写工具</h1>
            <p>面向行业新闻、工作动态与综合材料的智能改写工作台</p>
            <div class="status-row">
                <span class="status-pill">模型 {html.escape(model_name)}</span>
                <span class="status-pill">后端端口：8082</span>
                <span class="status-pill">当前环境：开发版</span>
                <span class="status-pill {'ok' if backend_ok else ''}">接口状态：{backend_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-title">参数设置</div>
            <div class="sidebar-subtitle">开发版工作台配置，仅连接 8082 后端。</div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown('<div class="sidebar-section-title">后端接口</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="endpoint-box">{html.escape(endpoint)}</div>', unsafe_allow_html=True)
            if st.button("检测后端", use_container_width=True):
                st.session_state.backend_status = check_backend_status(backend_base)
                backend_ok = bool(st.session_state.backend_status.get("ok"))
                if backend_ok:
                    st.success("后端连接正常")
                else:
                    st.warning("后端暂不可用")

        with st.container(border=True):
            st.markdown('<div class="sidebar-section-title">改写参数</div>', unsafe_allow_html=True)
            style = st.radio("改写风格", ["东方烟草报", "新华财经"], horizontal=False)
            strict_mode = st.toggle("严格模式", value=False)
            output_length = st.segmented_control(
                "输出长度",
                options=["简洁", "标准", "详尽"],
                default="标准",
            )
            article_type = st.selectbox(
                "稿件类型",
                ["客户服务", "市场监管", "车间技改", "数字化转型", "综合新闻"],
                index=4,
            )

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="sidebar-section-title">运行状态</div>
                <div class="status-card">
                    <span>后端状态</span>
                    <strong>{html.escape(backend_label)}</strong>
                    <span>模型：{html.escape(model_name)}</span>
                    <span>端口：8082 / 8502</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    input_col, output_col = st.columns([1, 1.08], gap="large")

    with input_col:
        with st.container(border=True):
            st.markdown(
                """
                <div class="panel-heading">
                    <div>
                        <div class="section-title">原始稿件</div>
                        <div class="section-caption">请粘贴需要改写的新闻、工作动态或材料文本</div>
                    </div>
                    <div class="panel-badge">编辑区</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_a, action_b, action_c = st.columns([1, 1, 2])
            if action_a.button("填入示例", use_container_width=True):
                st.session_state.draft_text = SAMPLE_TEXT
            if action_b.button("清空输入", use_container_width=True):
                st.session_state.draft_text = ""
                st.session_state.last_error = None

            text = st.text_area(
                "原始稿件",
                key="draft_text",
                label_visibility="collapsed",
                height=330,
                placeholder="粘贴一段新闻稿、工作动态或行业材料...",
            )
            char_count = len(text.strip())
            st.markdown(f'<div class="char-counter">当前字数：{char_count} 字</div>', unsafe_allow_html=True)

            submit_col, clear_col = st.columns([2.2, 1])
            submitted = submit_col.button("生成改写稿", type="primary", use_container_width=True)
            if clear_col.button("清空结果", use_container_width=True):
                st.session_state.rewrite_result = None
                st.session_state.last_error = None
                st.session_state.elapsed_seconds = None

            if submitted:
                st.session_state.last_error = None
                st.session_state.rewrite_result = None
                if not text.strip():
                    st.warning("请先输入需要改写的稿件内容。")
                else:
                    genre = STYLE_TO_GENRE[style]
                    payload = {
                        "text": text.strip(),
                        "genres": [genre],
                        "strict_mode": strict_mode,
                    }
                    start = datetime.now()
                    try:
                        with st.spinner("正在分析原文结构并生成改写稿..."):
                            response = requests.post(endpoint, json=payload, timeout=180)
                        st.session_state.elapsed_seconds = (
                            datetime.now() - start
                        ).total_seconds()
                        if response.ok:
                            st.session_state.rewrite_result = response.json()
                            st.toast("改写稿生成完成")
                        else:
                            st.session_state.last_error = {
                                "status": response.status_code,
                                "message": friendly_error(response.status_code, response.text),
                                "detail": response.text,
                            }
                    except Exception as exc:
                        st.session_state.elapsed_seconds = (
                            datetime.now() - start
                        ).total_seconds()
                        st.session_state.last_error = {
                            "status": None,
                            "message": friendly_error(None, str(exc)),
                            "detail": str(exc),
                        }

    with output_col:
        with st.container(border=True):
            st.markdown(
                """
                <div class="panel-heading">
                    <div>
                        <div class="section-title">改写结果</div>
                        <div class="section-caption">结果按标题、导语、正文和生成信息分区展示</div>
                    </div>
                    <div class="panel-badge">输出区</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.last_error:
                error = st.session_state.last_error
                st.error(error["message"])
                with st.expander("查看错误详情"):
                    st.code(error.get("detail", ""))
            elif st.session_state.rewrite_result:
                data = st.session_state.rewrite_result
                title = data.get("title", "改写标题")
                lead = data.get("lead", "")
                body = data.get("body", {})
                paragraphs = body.get("paragraphs") or []
                if not paragraphs and body.get("raw"):
                    paragraphs = [body["raw"]]
                meta = data.get("meta", {})
                result_text = result_to_text(data)
                elapsed = st.session_state.elapsed_seconds

                st.markdown(
                    f"""
                    <div class="result-title-card">
                        <div class="mini-label">改写标题</div>
                        <div class="result-title">{html.escape(title)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if lead:
                    st.markdown('<div class="mini-label">导语</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="lead-box">{html.escape(lead)}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('<div class="mini-label">正文</div>', unsafe_allow_html=True)
                for paragraph in paragraphs:
                    st.markdown(
                        f'<p class="body-paragraph">{html.escape(str(paragraph))}</p>',
                        unsafe_allow_html=True,
                    )

                download_col, md_col = st.columns(2)
                download_col.download_button(
                    "下载 TXT",
                    data=result_text,
                    file_name="rewritten_article.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
                md_col.download_button(
                    "下载 MD",
                    data=f"# {title}\n\n{lead}\n\n" + "\n\n".join(paragraphs),
                    file_name="rewritten_article.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
                st.text_area("可复制全文", value=result_text, height=180)

                with st.expander("生成信息", expanded=False):
                    info = {
                        "模型": meta.get("model", model_name),
                        "风格": style,
                        "稿件类型": article_type,
                        "输出长度": output_length,
                        "严格模式": strict_mode,
                        "原文字数": char_count,
                        "生成耗时": f"{elapsed:.1f}s" if elapsed is not None else None,
                        "后端地址": endpoint,
                    }
                    st.json(info)
                    st.caption("完整后端响应")
                    st.json(data, expanded=False)
            else:
                st.markdown(
                    """
                    <div class="empty-state">
                        <div class="empty-title">改写结果将在这里生成</div>
                        <div class="empty-copy">提交原始稿件后，系统将按标题、导语、正文结构化展示改写结果，并保留下载与复制入口。</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

def init_session_state():
    """初始化会话状态"""
    if "processing_result" not in st.session_state:
        st.session_state.processing_result = None
    if "environment_checked" not in st.session_state:
        st.session_state.environment_checked = False
    if "system_mode" not in st.session_state:
        st.session_state.system_mode = None
    if "dependency_check" not in st.session_state:
        st.session_state.dependency_check = None

def show_system_status():
    """显示系统状态"""
    loader = get_dynamic_loader()
    
    if st.session_state.dependency_check is None:
        with st.spinner("正在检测系统依赖..."):
            st.session_state.dependency_check = loader.check_dependencies()
    
    deps = st.session_state.dependency_check
    
    # 确定运行模式
    if deps['agents'] and deps['vector_db']:
        st.session_state.system_mode = "完整Agent系统"
        mode_color = "success"
        mode_icon = "🎯"
    elif deps['agents']:
        st.session_state.system_mode = "基础Agent系统"
        mode_color = "info"
        mode_icon = "⚡"
    else:
        st.session_state.system_mode = "基础改写模式"
        mode_color = "warning" 
        mode_icon = "🔧"
    
    # 显示状态
    if mode_color == "success":
        st.success(f"{mode_icon} 当前运行模式：{st.session_state.system_mode}")
    elif mode_color == "info":
        st.info(f"{mode_icon} 当前运行模式：{st.session_state.system_mode}")
    else:
        st.warning(f"{mode_icon} 当前运行模式：{st.session_state.system_mode}")
    
    # 详细状态
    with st.expander("🔧 详细系统状态", expanded=False):
        st.write("**依赖检查结果:**")
        st.write(f"✅ 核心依赖: {'正常' if deps['core'] else '异常'}")
        st.write(f"{'✅' if deps['vector_db'] else '❌'} 向量数据库: {'可用' if deps['vector_db'] else '不可用'}")
        st.write(f"{'✅' if deps['agents'] else '❌'} Agent系统: {'可用' if deps['agents'] else '不可用'}")
        
        st.write("**运行能力:**")
        if deps['agents'] and deps['vector_db']:
            st.write("🎭 体裁识别Agent ✅")
            st.write("🏗️ 结构重组Agent ✅") 
            st.write("✨ 风格改写Agent ✅")
            st.write("🔍 事实校对Agent ✅")
            st.write("📄 版式导出Agent ✅")
            st.write("📊 质量评估Agent ✅")
            st.write("🗂️ 知识库检索 ✅")
        elif deps['agents']:
            st.write("🎭 体裁识别Agent ✅")
            st.write("🏗️ 结构重组Agent ✅") 
            st.write("✨ 风格改写Agent ✅")
            st.write("🔍 事实校对Agent ✅")
            st.write("📄 版式导出Agent ✅")
            st.write("📊 质量评估Agent ✅")
            st.write("🗂️ 知识库检索 ❌（无向量数据库）")
        else:
            st.write("✨ 基础改写功能 ✅")
            st.write("📊 基础质量评估 ✅")

async def process_article_dynamic(content, title="", author=""):
    """动态处理文章"""
    try:
        loader = get_dynamic_loader()
        rewriter = loader.get_rewriter_instance()
        
        return await rewriter.process_article(content, title, author)
        
    except Exception as e:
        st.error(f"处理失败: {str(e)}")
        return None

def sync_process_article(content, title="", author=""):
    """同步包装器"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(process_article_dynamic(content, title, author))
        finally:
            loop.close()
    except Exception as e:
        st.error(f"同步处理失败: {e}")
        return None

def main():
    """主应用"""
    if get_dynamic_loader is None:
        render_fastapi_client()
        return

    init_session_state()
    
    # 页面标题
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>🎯 中国烟草报风格改写系统</h1>
        <p style="color: #666; font-size: 18px;">智能Agent文章改写工具 - 云端自适应版</p>
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
            return
        else:
            st.success(f"✅ {env_msg}")
            st.session_state.environment_checked = True
    
    # 显示系统状态
    show_system_status()
    
    # 侧边栏信息
    with st.sidebar:
        st.header("📚 系统信息")
        
        if st.session_state.system_mode:
            if "完整" in st.session_state.system_mode:
                st.success(f"**当前模式**: {st.session_state.system_mode}")
                st.info("""
                **完整功能**:
                - 🎭 体裁识别Agent
                - 🏗️ 结构重组Agent
                - ✨ 风格改写Agent
                - 🔍 事实校对Agent
                - 📄 版式导出Agent
                - 📊 质量评估Agent
                - 🗂️ 知识库检索
                """)
            elif "基础Agent" in st.session_state.system_mode:
                st.info(f"**当前模式**: {st.session_state.system_mode}")
                st.info("""
                **可用功能**:
                - 🎭 体裁识别Agent
                - 🏗️ 结构重组Agent
                - ✨ 风格改写Agent
                - 🔍 事实校对Agent
                - 📄 版式导出Agent
                - 📊 质量评估Agent
                """)
            else:
                st.warning(f"**当前模式**: {st.session_state.system_mode}")
                st.info("""
                **可用功能**:
                - ✨ 智能改写
                - 📊 质量评估
                - 📄 文档导出
                """)
        
        st.header("🎯 使用提示")
        st.write("""
        1. 输入要改写的文章内容
        2. 点击"开始改写"按钮
        3. 等待系统处理（约30-60秒）
        4. 查看改写结果和质量评估
        """)
    
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
                    
                    if "完整" in st.session_state.system_mode:
                        stages = [
                            "🎭 体裁识别Agent处理中...",
                            "🏗️ 结构重组Agent处理中...",
                            "✨ 风格改写Agent处理中...", 
                            "🔍 事实校对Agent处理中...",
                            "📄 版式导出Agent处理中...",
                            "📊 质量评估Agent处理中..."
                        ]
                    elif "基础Agent" in st.session_state.system_mode:
                        stages = [
                            "🎭 启动体裁识别Agent...",
                            "🏗️ 启动结构重组Agent...",
                            "✨ 启动风格改写Agent...",
                            "📊 启动质量评估Agent..."
                        ]
                    else:
                        stages = [
                            "🔍 分析文章内容...",
                            "✨ 智能改写处理...",
                            "📊 质量评估中..."
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
                            status_text.text(f"✅ {st.session_state.system_mode}处理完成！")
                            st.rerun()
                        else:
                            st.error("❌ 处理失败，请稍后重试")
                            
                    except Exception as e:
                        st.error(f"❌ 处理异常: {str(e)}")
                        st.error("请检查系统状态或联系技术支持")
    
    with col2:
        st.header("📊 处理状态")
        
        if st.session_state.processing_result:
            result = st.session_state.processing_result
            
            st.success(f"✅ {st.session_state.system_mode}处理完成")
            
            # 质量评估显示
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
            st.info(f"等待{st.session_state.system_mode or '系统'}处理...")
    
    # 显示处理结果
    if st.session_state.processing_result:
        show_results(st.session_state.processing_result)

def show_results(result):
    """显示处理结果"""
    st.markdown("---")
    st.header(f"🎉 {st.session_state.system_mode}处理结果")
    
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
            
            word_count = len(result.final_content)
            st.info(f"📊 改写后字数：{word_count}字")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # 体裁识别结果
            if hasattr(result, 'genre_result') and result.genre_result:
                st.subheader("🎭 体裁识别结果")
                if hasattr(result.genre_result, 'genre'):
                    st.write(f"**识别结果**: {result.genre_result.genre}")
                if hasattr(result.genre_result, 'confidence'):
                    st.write(f"**置信度**: {result.genre_result.confidence:.1%}")
                if hasattr(result.genre_result, 'reasoning'):
                    st.write(f"**分析**: {result.genre_result.reasoning}")
        
        with col2:
            # 质量评估
            if hasattr(result, 'quality_result') and result.quality_result:
                st.subheader("📊 质量评估结果")
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
            title_text = "改写稿件"
            if hasattr(result, 'input_article') and result.input_article and hasattr(result.input_article, 'title'):
                title_text = result.input_article.title or '改写稿件'
                
            markdown_content = f"""# {title_text}

{result.final_content}

---
*改写时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}*  
*处理模式: {st.session_state.system_mode}*
*系统: 中国烟草报风格改写系统*
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

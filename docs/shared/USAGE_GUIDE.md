# 中国烟草报风格改写系统 - 使用指南

## 🎯 系统概述

中国烟草报风格改写系统是一个基于Claude多Agent架构的智能公文写作工具，专门用于将初稿文章改写为符合中国烟草报风格的专业稿件。

### 核心功能
- **智能体裁识别**：自动识别新闻、评论、通讯等文章类型
- **结构化重组**：按烟草报标准重新组织文章结构
- **风格化改写**：基于知识库学习的语言风格转换
- **专业校对**：术语一致性和事实准确性检查
- **标准化导出**：生成符合格式要求的DOCX文档
- **质量评估**：多维度评分和改进建议

## 🚀 快速开始

### 1. 环境准备

```bash
# 1. 确保Python 3.8+环境
python --version

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入Claude API密钥
```

### 2. 启动系统

```bash
# 方法1：使用启动脚本（推荐）
python run.py

# 方法2：直接启动Web界面
streamlit run web_interface/app.py
```

### 3. 系统测试

```bash
# 运行系统测试
python test_system.py
```

## 📝 使用方法

### Web界面使用

1. **启动系统**
   ```bash
   python run.py
   ```
   访问 http://localhost:8501

2. **初始化知识库**
   - 首次使用需点击"初始化知识库"按钮
   - 系统会自动加载风格卡、句式库、术语库

3. **文章改写流程**
   - 在"文章改写"页面输入待改写内容
   - 可选填写标题和作者信息
   - 点击"开始改写"按钮
   - 系统自动执行6步改写流程
   - 查看改写结果和质量评估

4. **结果导出**
   - 支持DOCX和Markdown格式导出
   - 可下载标准格式的文档文件

### API使用（编程方式）

```python
import asyncio
from main_pipeline import main_pipeline

async def process_article():
    # 初始化系统
    await main_pipeline.initialize_knowledge_base()
    
    # 处理文章
    result = await main_pipeline.process_article(
        content="您的文章内容",
        title="文章标题",
        author="作者姓名"
    )
    
    # 获取结果
    if result.final_content:
        print("改写成功！")
        print(result.final_content)
    else:
        print("改写失败")

# 运行
asyncio.run(process_article())
```

## 🏗️ 系统架构

### 多Agent流水线

```
原稿输入 → 体裁判定 → 结构重组 → 风格改写 → 事实校对 → 版式导出 → 质量评估
```

1. **体裁识别Agent** (`GenreClassifierAgent`)
   - 识别文章类型（新闻/评论/通讯等）
   - 基于关键词匹配 + LLM分析
   - 输出体裁类型和置信度

2. **结构重组Agent** (`StructureReorganizerAgent`)
   - 按体裁标准重新组织结构
   - 优化标题、导语、正文布局
   - 识别并修复结构问题

3. **风格改写Agent** (`StyleRewriterAgent`)
   - 核心改写模块，转换语言风格
   - 基于知识库的句式和表达优化
   - 逐段改写，保持原意

4. **事实校对Agent** (`FactCheckerAgent`)
   - 检查术语使用规范性
   - 识别禁用词和不当表述
   - 验证事实一致性

5. **版式导出Agent** (`FormatExporterAgent`)
   - 生成标准DOCX文档
   - 应用统一格式模板
   - 支持多种导出格式

6. **质量评估Agent** (`QualityEvaluatorAgent`)
   - 多维度质量评分
   - 生成改进建议
   - 判断是否达到发布标准

### 知识库系统

- **向量数据库**：基于Chroma + FAISS的混合检索
- **风格卡库**：各体裁的写作特征和规范
- **句式库**：常用表达模式和转换模板
- **术语库**：行业标准用词和口径规范

## ⚙️ 配置说明

### 环境变量配置 (`.env`)

```bash
# Claude API配置
CLAUDE_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-sonnet-20241022

# 数据库路径
CHROMA_DB_PATH=./data/chroma_db
FAISS_INDEX_PATH=./data/faiss_index

# 模型配置
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
MAX_CONTENT_LENGTH=50000

# Web服务
HOST=0.0.0.0
PORT=8501

# 质量评估
QUALITY_THRESHOLD=0.75
```

### 知识库定制

可以通过以下方式扩展知识库：

```python
from knowledge_base import knowledge_manager

# 添加自定义风格卡
knowledge_manager.add_knowledge_entry(
    content="您的风格规范内容",
    category="style_cards",
    tags=["新闻", "风格", "自定义"]
)

# 添加句式模板
knowledge_manager.add_knowledge_entry(
    content="句式模板内容",
    category="sentence_patterns", 
    tags=["句式", "模板"]
)
```

## 📊 质量评估指标

系统提供6个维度的质量评估：

1. **标题完整性** (0-1)：标题是否简洁明了、突出重点
2. **导语质量** (0-1)：是否概括全文、回答关键问题
3. **内容连贯性** (0-1)：逻辑是否清晰、过渡是否自然
4. **风格一致性** (0-1)：是否符合官方媒体风格要求
5. **事实准确性** (0-1)：信息是否准确、表述是否规范
6. **格式规范性** (0-1)：结构是否标准、格式是否统一

**综合评分** = 各维度加权平均，≥0.7视为通过质量检查

## 🔧 常见问题

### 1. 知识库初始化失败
- 检查网络连接和embedding模型下载
- 确认有足够的磁盘空间
- 查看日志文件定位具体错误

### 2. Claude API调用失败
- 验证API密钥是否正确
- 检查API调用限制和余额
- 确认网络可以访问Claude API

### 3. 改写质量不佳
- 增加相关领域的知识库内容
- 调整质量评估阈值
- 检查输入文章的质量和完整性

### 4. 处理速度慢
- 优化embedding模型选择
- 调整批处理大小
- 考虑使用更快的硬件

## 📈 性能优化

### 1. 硬件建议
- **CPU**：4核心以上
- **内存**：8GB以上 
- **存储**：SSD，至少5GB可用空间
- **网络**：稳定的互联网连接

### 2. 软件优化
- 使用GPU加速（如果可用）
- 调整并发处理数量
- 开启向量数据库缓存

### 3. 知识库优化
- 定期清理冗余数据
- 优化向量索引结构
- 使用更高效的embedding模型

## 🔄 持续改进

### 数据收集
- 收集更多行业稿件样本
- 建立人工评估反馈机制
- 记录用户使用偏好

### 模型优化
- A/B测试不同改写策略
- 基于反馈调整Agent参数
- 定期更新知识库内容

### 功能扩展
- 支持更多文档格式
- 增加批量处理功能
- 开发移动端应用

## 📞 技术支持

如遇到问题，请：

1. 查看系统日志：`./data/logs/`
2. 运行系统测试：`python test_system.py`
3. 检查配置文件：`.env`
4. 联系技术支持或提交Issue

---

## 📄 许可证

本项目仅供学习和研究使用。请遵守相关法律法规和API服务条款。
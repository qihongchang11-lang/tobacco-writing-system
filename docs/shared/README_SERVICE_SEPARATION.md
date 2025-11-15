# 服务分离说明文档

## 🎯 概述

本项目现已完全分离为两个独立的服务系统：

1. **东方烟草报风格改写系统** (端口: 8081)
2. **CNIPA发明专利高质量改写系统** (端口: 8082)

## 📋 服务对比

| 特性 | 东方烟草报系统 | CNIPA专利系统 |
|------|----------------|---------------|
| **服务名称** | 东方烟草报风格改写系统 | CNIPA发明专利高质量改写系统 |
| **端口** | 8081 | 8082 |
| **主要功能** | 烟草行业文章风格改写 | 专利四件套文档生成 |
| **API标题** | 东方烟草报风格改写系统 API | CNIPA发明专利高质量改写系统 API |
| **风格** | 新华财经风格 | CNIPA合规标准 |
| **学习模式** | Few-shot学习 | 规则驱动检查 |

## 🚀 快速启动

### 前置要求

- Python 3.12+
- DeepSeek API密钥（或其他OpenAI兼容的LLM服务）

### 环境配置

```bash
# 1. 克隆项目
git clone <repository-url>
cd tobacco-writing-pipeline

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.separated .env
# 编辑 .env 文件，设置 API 密钥
```

### 启动服务

#### 方法一：分别启动

```bash
# 启动东方烟草报系统（端口 8081）
python news_api_main.py

# 启动CNIPA专利系统（端口 8082）
python patent_api_main.py
```

#### 方法二：使用启动脚本

```bash
# 启动两个服务
./scripts/start_both_services.sh

# 或者分别启动
./scripts/start_news_service.sh
./scripts/start_patent_service.sh
```

## 🔍 验证服务

### 手动验证

```bash
# 验证新闻服务健康状态
curl http://localhost:8081/health

# 验证专利服务健康状态
curl http://localhost:8082/health

# 验证OpenAPI文档
curl http://localhost:8081/openapi.json | jq '.info.title'
curl http://localhost:8082/openapi.json | jq '.info.title'
```

### 自动验证

```bash
# 运行完整验证脚本
python scripts/validate_service_separation.py

# 或者使用CI验证
./scripts/run_validation_tests.sh
```

## 📖 API 文档

### 东方烟草报系统 API (http://localhost:8081)

#### 主要端点
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `POST /rewrite` - 文章改写
- `GET /learning-stats` - 学习统计
- `GET /docs` - API文档 (Swagger UI)

#### 使用示例
```bash
curl -X POST "http://localhost:8081/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "镇江烟草推进数字化转型工作",
    "genres": ["news_general"],
    "strict_mode": false
  }'
```

### CNIPA专利系统 API (http://localhost:8082)

#### 主要端点
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `POST /process` - 专利文档处理
- `POST /upload-and-process` - 文件上传处理
- `GET /gates/{gate_id}` - 质量门检查
- `GET /system-info` - 系统信息
- `GET /docs` - API文档 (Swagger UI)

#### 使用示例
```bash
curl -X POST "http://localhost:8082/process" \
  -H "Content-Type: application/json" \
  -d '{
    "draft_content": "一种改进的烟草加工设备",
    "invention_type": "invention",
    "enable_checks": true
  }'
```

## 🔧 环境变量配置

### 服务端配置
```env
# 东方烟草报系统
NEWS_API_HOST=0.0.0.0
NEWS_API_PORT=8081

# CNIPA专利系统
PATENT_API_HOST=0.0.0.0
PATENT_API_PORT=8082
```

### API配置
```env
# DeepSeek API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

## 🧪 测试与验证

### 单元测试
```bash
# 运行新闻服务测试
pytest tests/test_news_service.py -v

# 运行专利服务测试
pytest tests/test_patent_service.py -v
```

### 集成测试
```bash
# 运行服务分离验证
python scripts/validate_service_separation.py

# 运行端口冲突检查
python scripts/check_port_conflicts.py
```

### CI/CD 验证
GitHub Actions 会自动运行以下验证：
- ✅ 健康检查验证
- ✅ OpenAPI文档验证
- ✅ 端口分离验证
- ✅ 功能测试验证
- ✅ 无交叉污染验证

## 🚨 故障排除

### 端口冲突
如果端口被占用，修改 `.env` 文件中的端口配置：
```env
NEWS_API_PORT=8083  # 修改为其他端口
PATENT_API_PORT=8084  # 修改为其他端口
```

### 服务启动失败
1. 检查端口是否被占用
2. 验证环境变量配置
3. 查看服务日志
4. 确保所有依赖已安装

### API调用失败
1. 验证服务是否正常运行
2. 检查请求格式是否正确
3. 查看服务日志获取详细错误信息

## 📝 开发说明

### 添加新功能
1. 确定功能所属的系统（新闻/专利）
2. 在对应的 API 文件中添加端点
3. 更新 OpenAPI 文档
4. 添加相应的测试用例

### 修改端口配置
1. 更新 `.env` 文件
2. 更新启动脚本
3. 更新文档说明
4. 运行验证测试

## 🔗 相关链接

- [API文档 - 新闻系统](http://localhost:8081/docs)
- [API文档 - 专利系统](http://localhost:8082/docs)
- [项目任务卡](jobcards/fix_service_separation.yaml)
- [验证脚本](scripts/validate_service_separation.py)

## 📞 支持

如遇到问题，请：
1. 查看服务日志
2. 运行验证脚本
3. 检查端口占用情况
4. 提交 Issue 到项目仓库

---

**确保两个系统完全分离运行，避免任何交叉污染或端口冲突。**
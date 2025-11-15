# 开发与协作最佳实践指南

> **文档目标**：基于本项目的实际经验，总结开发、协作、项目管理的最佳实践，为团队新成员和未来项目提供指导。

---

## 🚀 项目启动最佳实践

### 1. 需求确认与方案设计

#### ✅ 推荐做法
- **多方案对比**：提供2-3个可行方案，说明优缺点
- **用户参与决策**：重大技术选择让用户选择
- **分阶段实施**：复杂变更分解为小步骤
- **风险评估**：评估每个方案的实施风险

#### ❌ 避免的错误
- 假设用户需求，直接按技术思维实施
- 单一方案推进，缺乏备选
- 一次性大规模变更
- 忽视现有系统的约束

#### 🎯 实际案例
```
❌ 错误：认为"分仓库更清晰"就直接实施
✅ 正确：提供统一仓库vs分仓库两种方案，解释利弊让用户选择
```

### 2. 技术方案评估框架

#### 评估维度
1. **用户价值** - 是否解决实际问题
2. **实施风险** - 对现有系统的影响
3. **维护成本** - 长期维护的复杂度
4. **扩展性** - 未来需求的适应性
5. **团队能力** - 是否在团队技能范围内

#### 决策矩阵示例
| 方案 | 用户价值 | 实施风险 | 维护成本 | 扩展性 | 团队能力 | 总分 |
|------|----------|----------|----------|--------|----------|------|
| 统一仓库 | 9 | 3 | 6 | 8 | 9 | 35 |
| 分仓库 | 6 | 8 | 7 | 7 | 8 | 36 |
| 目录重组 | 7 | 9 | 5 | 6 | 7 | 34 |

---

## 💻 代码开发最佳实践

### 1. Python项目结构管理

#### ✅ 推荐做法
- **导入路径稳定性**：避免频繁移动包含`__init__.py`的目录
- **相对导入谨慎使用**：优先使用绝对导入
- **环境变量管理**：使用.env文件管理配置
- **依赖明确声明**：requirements.txt及时更新

#### ❌ 避免的错误
```python
# ❌ 避免：移动目录后忘记更新导入
from agents.few_shot_rewriter import FewShotRewriter  # 旧路径

# ✅ 推荐：保持稳定的导入路径
from agents import FewShotRewriter
```

#### 🔧 重构策略
```bash
# ❌ 错误：直接移动包目录
mv core/ news-system/core/

# ✅ 正确：先评估影响，准备迁移脚本
grep -r "from core import" .
# 评估影响范围，制定迁移计划
```

### 2. API设计规范

#### 接口一致性
```python
# ✅ 推荐：统一的响应格式
{
    "success": True,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2025-11-16T10:30:00Z"
}

# ❌ 避免：不一致的响应格式
{"result": {...}}  # 某些接口
{"data": {...}}    # 另一些接口
```

#### 错误处理
```python
# ✅ 推荐：结构化错误信息
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": "参数验证失败",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 3. 配置管理

#### 环境配置分离
```python
# ✅ 推荐：分环境配置
# .env.development
NEWS_API_PORT=8081
OPENAI_API_KEY=dev_key
LOG_LEVEL=debug

# .env.production
NEWS_API_PORT=80
OPENAI_API_KEY=prod_key
LOG_LEVEL=info
```

#### 配置验证
```python
# ✅ 推荐：启动时验证配置
from pydantic import BaseSettings

class Settings(BaseSettings):
    news_api_port: int = 8081
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"

settings = Settings()  # 自动验证必需配置
```

---

## 🤝 团队协作最佳实践

### 1. Git工作流

#### 提交消息规范
```bash
# ✅ 推荐：结构化提交消息
feat: 添加新华财经风格检测器

- 实现XHF风格特征识别
- 添加修辞手法检测算法
- 更新相关单元测试

Closes #42

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### 分支策略
```bash
# ✅ 推荐：功能分支工作流
main                    # 稳定主分支
├── feature/xhf-style   # 功能开发分支
├── bugfix/import-path  # 问题修复分支
└── hotfix/prod-crash   # 紧急修复分支
```

### 2. 代码审查

#### 审查检查清单
- [ ] **功能正确性**：是否解决了预期问题
- [ ] **代码质量**：是否遵循项目约定
- [ ] **测试覆盖**：是否有足够的测试
- [ ] **文档更新**：是否更新了相关文档
- [ ] **向后兼容**：是否破坏现有功能
- [ ] **安全考虑**：是否引入安全风险

#### 审查反馈模板
```markdown
## 总体评价
功能实现正确，代码质量良好。

## 必须修改
- [ ] line 42: 需要添加异常处理
- [ ] line 67: 硬编码的API密钥应该使用环境变量

## 建议优化
- [ ] 考虑抽取公共函数减少代码重复
- [ ] 添加类型注解提升可读性

## 测试建议
- [ ] 添加边界条件测试用例
- [ ] 考虑性能测试
```

### 3. 文档维护

#### 文档同步策略
```bash
# ✅ 推荐：代码变更时同步更新文档
git add code_changes.py docs/api_reference.md
git commit -m "feat: 新增API接口并更新文档"
```

#### 文档质量检查
- [ ] **完整性**：是否覆盖所有功能
- [ ] **准确性**：是否与实际代码一致
- [ ] **可用性**：新用户能否按文档操作成功
- [ ] **及时性**：是否及时更新变更

---

## 🔍 质量保障最佳实践

### 1. 测试策略

#### 测试分层
```
📊 测试金字塔
    /\
   /UI\      <- E2E测试（少量）
  /____\
 /集成测试\    <- API集成测试（适量）
/__单元测试__\  <- 单元测试（大量）
```

#### 测试用例设计
```python
# ✅ 推荐：AAA模式（Arrange-Act-Assert）
def test_tobacco_style_rewrite():
    # Arrange - 准备测试数据
    original_text = "原始财经新闻内容..."
    expected_style = "tobacco"

    # Act - 执行操作
    result = rewriter.rewrite(original_text, style=expected_style)

    # Assert - 验证结果
    assert result.success is True
    assert "烟草" in result.content
    assert len(result.content) > len(original_text) * 0.8
```

### 2. 持续集成

#### GitHub Actions示例
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=./ --cov-report=xml
      - name: Lint code
        run: ruff check .
      - name: Type check
        run: mypy .
```

### 3. 监控与告警

#### 核心指标
- **可用性**：API响应成功率 >99.9%
- **性能**：API响应时间P95 <500ms
- **质量**：单元测试覆盖率 >80%
- **安全**：无高危漏洞

#### 告警规则
```yaml
# 示例：Prometheus告警规则
groups:
  - name: api_alerts
    rules:
      - alert: APIHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        annotations:
          summary: "API错误率过高"
          description: "5分钟内错误率超过10%"
```

---

## 🚧 部署与运维最佳实践

### 1. 环境管理

#### 多环境策略
```
开发环境 (dev)     测试环境 (staging)    生产环境 (prod)
├── 快速迭代       ├── 稳定版本测试        ├── 严格变更控制
├── 详细日志       ├── 性能测试            ├── 完整监控
└── Mock外部服务   └── 集成测试            └── 备份恢复
```

#### 配置管理
```bash
# ✅ 推荐：环境特定配置
config/
├── base.yml        # 基础配置
├── development.yml # 开发环境覆盖
├── staging.yml     # 测试环境覆盖
└── production.yml  # 生产环境覆盖
```

### 2. 部署策略

#### 蓝绿部署
```bash
# 部署流程
1. 在绿环境部署新版本
2. 健康检查通过后切换流量
3. 保留蓝环境一段时间以备回滚
4. 确认稳定后清理蓝环境
```

#### 启动脚本最佳实践
```bash
#!/bin/bash
# ✅ 推荐：健壮的启动脚本

set -e  # 遇到错误立即退出

# 环境检查
if [[ ! -f ".env" ]]; then
    echo "错误：缺少.env配置文件"
    exit 1
fi

# 依赖检查
python -c "import openai" || {
    echo "错误：缺少openai依赖"
    exit 1
}

# 目录准备
mkdir -p logs

# 健康检查函数
check_health() {
    local port=$1
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:$port/health >/dev/null 2>&1; then
            echo "服务启动成功 (端口 $port)"
            return 0
        fi
        echo "等待服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "服务启动失败 (端口 $port)"
    return 1
}

# 启动服务
python news_api_main.py &
NEWS_PID=$!

# 等待服务就绪
check_health 8081 || {
    kill $NEWS_PID
    exit 1
}

echo "所有服务已成功启动"
```

---

## 📊 错误处理与恢复最佳实践

### 1. 错误分类与处理

#### 错误分类策略
```python
class ErrorType(Enum):
    VALIDATION_ERROR = "validation_error"    # 4xx - 客户端错误
    BUSINESS_ERROR = "business_error"        # 4xx - 业务逻辑错误
    SYSTEM_ERROR = "system_error"            # 5xx - 系统错误
    EXTERNAL_ERROR = "external_error"        # 5xx - 外部服务错误

# ✅ 推荐：结构化错误处理
@app.exception_handler(OpenAIError)
async def openai_error_handler(request: Request, exc: OpenAIError):
    logger.error(f"OpenAI API错误: {exc}", extra={
        "error_type": ErrorType.EXTERNAL_ERROR.value,
        "request_id": request.headers.get("X-Request-ID"),
        "user_id": getattr(request.state, "user_id", None)
    })

    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": "外部服务暂时不可用，请稍后重试",
            "error_code": "EXTERNAL_SERVICE_ERROR",
            "request_id": request.headers.get("X-Request-ID")
        }
    )
```

### 2. 重试与熔断

#### 指数退避重试
```python
import asyncio
from functools import wraps

def async_retry(max_attempts=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise

                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)

            return None
        return wrapper
    return decorator

# 使用示例
@async_retry(max_attempts=3, backoff_factor=2)
async def call_openai_api(prompt: str):
    return await openai.ChatCompletion.acreate(...)
```

---

## 📚 知识管理最佳实践

### 1. 文档体系建设

#### 文档分类标准
```
📚 文档体系结构
├── README.md           # 项目入口，快速上手
├── docs/
│   ├── shared/         # 跨系统通用文档
│   │   ├── ARCHITECTURE_DECISIONS.md  # 技术决策记录
│   │   ├── PROJECT_WORK_SUMMARY.md    # 工作总结
│   │   └── BEST_PRACTICES.md         # 最佳实践（本文档）
│   ├── api/            # API文档
│   │   ├── openapi.json
│   │   └── examples/
│   └── deployment/     # 部署文档
│       ├── setup.md
│       └── troubleshooting.md
```

#### 文档维护流程
1. **创建** - 新功能开发时同步创建文档
2. **更新** - 代码变更时及时更新相关文档
3. **审查** - 代码审查时检查文档更新
4. **清理** - 定期清理过时文档

### 2. 知识传递

#### 新人入职检查清单
- [ ] 克隆仓库并成功运行系统
- [ ] 阅读README和架构决策文档
- [ ] 完成一个小功能的开发和测试
- [ ] 参与代码审查流程
- [ ] 了解部署和监控流程

#### 知识分享会议
- **技术分享**：每月分享新技术、工具或方法
- **案例复盘**：季度复盘重大问题和解决方案
- **最佳实践更新**：半年更新最佳实践文档

---

**文档版本**：v1.0
**创建日期**：2025-11-16
**适用范围**：tobacco-writing-system及类似项目
**维护责任**：全体开发团队
**更新机制**：重要经验积累后及时更新
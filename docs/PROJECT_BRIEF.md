# Tobacco Writing System – 项目简述

## 目标
将输入稿件改写为"东方烟草报/中国烟草报"风格，并保持数字、日期、机构名等事实一致。

## 当前架构（Phase 1）
- FastAPI 后端（端口 8081）
- ConstraintDecoder（占位符 + 白名单锁定 + 新数字检测 + 泄漏兜底）
- BM25 检索（LRU 缓存）
- column_rules.yaml 进行栏目风格匹配
- 审计字段：entities_locked, new_numbers_detected, evidence, retries, needs_review

## 状态
- ✅ Phase 1 完成
- ✅ API 运行中（8081）
- ✅ /health 检查正常
- ⏳ 下一步：完善栏目规则与批量测试

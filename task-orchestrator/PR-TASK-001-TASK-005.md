## 描述

完成 V0.0.4 关键能力交付：

- TASK-005 数据模型设计（5 张 Bitable 表、约束、关系、数据字典、ER 图）
- TASK-001 Bitable API 集成（连接管理 + 任务 CRUD + 执行/指标/错误/建议持久化）
- 单元测试与集成测试（含 mock API 与性能基准）

## 关联 Issue

- Closes #TASK-001
- Closes #TASK-005

## 改动类型

- [x] 新功能
- [x] 文档更新
- [x] 测试增强

## 关键改动

1. `bitable-integration.sh` 重构至 V0.0.4
   - 支持 `BITABLE_BACKEND=auto|local|api`
   - Feishu token 获取与缓存
   - HTTP 重试与错误处理
   - 完整任务 CRUD：`create/get/update/delete/list`
   - 执行记录、性能指标、错误模式、优化建议写入
   - 性能摘要与错误分析聚合

2. `BITABLE-SCHEMA.md`
   - 5 张核心表结构定义
   - 字段约束与枚举
   - 数据字典
   - ER 图（Mermaid）

3. 测试
   - `tests/unit/test-bitable-unit.sh`
   - `tests/integration/mock_feishu_bitable_server.py`
   - `test-bitable-integration.sh`

4. 文档
   - 更新 `CHANGELOG.md`
   - 更新 `GETTING-STARTED.md`
   - 更新 `MILESTONES.md`

## 测试结果

```bash
bash tests/unit/test-bitable-unit.sh
bash test-bitable-integration.sh
shellcheck bitable-integration.sh tests/unit/test-bitable-unit.sh test-bitable-integration.sh
```

## 风险与回滚

- 风险：API 模式依赖飞书字段命名与 schema 一致
- 缓解：local backend 兜底 + mock API 集成测试
- 回滚：回退 `bitable-integration.sh` 至 V0.0.3 前版本

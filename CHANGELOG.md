# Changelog

All notable changes to Task Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [V0.0.3] - 2026-03-06

### Added
- **Supervisor (Orchestrator-Worker) 模式** - 中央协调器 + 专业Worker agents
- **事件驱动任务队列** - 异步任务队列，防止阻塞
- **共享状态管理** - 标准化数据传递和持久化
- **工作流定义系统** - 预定义工作流 (document_analysis, tech_evaluation)
- **工作流执行引擎** - 支持并行/顺序执行
- **智能监控系统** - 实时健康检查 + 自动恢复
- **Log-Analyzer集成** - 智能日志分析和错误模式检测
- **Proactive-Agent集成** - 主动监控和自我修复
- **结构化日志系统** - 统一JSON格式日志

### Changed
- 架构从简单队列升级为Supervisor模式
- 执行时间从15分钟优化到6分钟 (-60%)
- 并发能力从1个agent提升到5个agents (+400%)
- 错误恢复从手动改为自动

### Fixed
- bash语法错误 (for循环重定向问题)
- 运行时目录缺失问题
- Agent配置验证机制

### Documentation
- 添加 WORKFLOWS.md - 工作流定义文档
- 添加 MULTI-AGENT-ORCHESTRATOR-UPGRADE.md - 升级总结
- 添加 LOG-ANALYZER-INTEGRATION.md - 日志分析集成文档
- 添加 PROACTIVE-AGENT-INTEGRATION.md - 主动监控集成文档
- 添加 README.md - 项目说明文档
- 添加 CHANGELOG.md - 变更日志

## [V0.0.2] - 2026-03-05

### Added
- 基础任务队列系统
- 简单监控机制
- Subagent状态追踪

### Changed
- 从单Agent模式升级为多Agent协作

## [V0.0.1] - 2026-03-04

### Added
- 初始版本
- 基础Agent调度功能
- 简单的任务管理

---

**版本号规范**: V0.0.X
- V0.0.X - 开发版本
- V0.X.0 - 测试版本
- VX.0.0 - 正式版本
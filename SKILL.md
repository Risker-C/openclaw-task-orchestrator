---
name: task-orchestrator
description: AI驱动的智能任务编排系统 v0.0.1 - 基于复杂度的多Agent协作平台
homepage: https://github.com/Risker-C/openclaw-task-orchestrator
metadata: {"clawdbot":{"emoji":"🎯","requires":{"bins":["python3"],"env":[]}}}
---

# Task Orchestrator v0.0.1 - AI驱动的任务编排系统

## 🎯 版本说明

- **当前版本**: v0.0.1 (初始版本)
- **状态**: 实验性质，功能验证阶段
- **目标**: 验证.md文档驱动的设计理念
- **适用**: 学习、参考、功能验证

## 🚀 核心理念

**从复杂代码到智能文档的架构革新**

Task Orchestrator 是一个基于.md文档驱动的OpenClaw Skill，通过AI直接分析任务复杂度，自动选择最优的执行策略，实现智能化的多Agent任务编排。

### ✨ 设计原则
- **文档驱动**: 主要逻辑通过.md文档指导AI行为
- **OpenClaw原生**: 充分利用OpenClaw现有AI能力和工具
- **必要脚本**: 只有复杂技术实现才使用Python脚本
- **简洁专一**: 专注于任务编排核心价值

## 🎯 工作流程

### 基本流程
```
用户输入任务描述
    ↓
我读取 complexity-guide.md 判断复杂度
    ↓
根据 agent-selection.md 选择合适Agent
    ↓
使用 execution-templates.md 执行策略
    ↓
通过 sessions_send 分配任务给Agent
    ↓
可选：调用 scripts/feishu-sync.py 同步状态
```

### 复杂度分级执行策略

#### L1 - 简单任务 (5-15分钟)
- **特征**: 查询、获取、读取类操作
- **处理**: 直接返回执行建议
- **示例**: "查询用户信息"、"检查系统状态"

#### L2 - 专业任务 (30-90分钟)  
- **特征**: 分析、设计、编写类任务
- **处理**: 分配给单个专业Agent
- **示例**: "分析性能瓶颈"、"编写技术文档"

#### L3 - 复杂任务 (2-6小时)
- **特征**: 系统性、多领域协作任务
- **处理**: 多Agent协调执行
- **示例**: "设计微服务架构"、"完整项目规划"

## 📋 使用方式

### 直接对话使用
```
用户: "帮我分析网站性能问题"

我的处理过程:
1. 读取 complexity-guide.md → 判断为L2任务
2. 读取 agent-selection.md → 选择architect
3. 使用 sessions_send 分配任务
4. 可选同步到飞书工单系统
```

### 配置飞书集成 (可选)
```bash
# 配置飞书应用信息
参考 feishu-config.md 进行配置

# 同步任务状态
python scripts/feishu-sync.py --task-id 123 --status completed

# 发送通知
python scripts/feishu-notify.py --message "任务完成" --target chat_id
```

## 🔧 Agent选择规则

基于任务内容自动选择最合适的Agent：

- **技术类任务** → architect, code-reviewer
- **文档类任务** → doc-engineer  
- **研究类任务** → research-analyst
- **设计类任务** → ui-designer, architect
- **安全类任务** → security-monitor
- **管理类任务** → implementation-planner, resource-manager
- **默认选择** → research-analyst

详细规则参见 `agent-selection.md`

## 📊 OpenClaw集成

### 使用的OpenClaw工具
- **sessions_send**: Agent任务分配和通信
- **agents_list**: 获取可用Agent列表
- **subagents**: Agent状态监控和管理
- **session_status**: 会话状态检查

### 避免的问题
- ❌ 不使用sessions_spawn (存在agentToAgent冲突)
- ✅ 使用sessions_send (稳定可靠)
- ✅ 基于OpenClaw原生能力，不重复造轮子

## 🎨 架构优势

### v0.0.1 特点
- **轻量化**: 主要逻辑通过文档，代码量最小
- **AI驱动**: 真正的AI判断，不是规则匹配
- **易维护**: 文档更新比代码修改更简单
- **可扩展**: 新场景通过文档调整即可适应

### 与传统方案对比
| 方面 | 传统代码驱动 | Task Orchestrator v0.0.1 |
|------|-------------|---------------------------|
| 复杂度判断 | 复杂算法 | AI直接分析 |
| 维护成本 | 高 | 低 |
| 扩展性 | 需要代码更新 | 文档调整 |
| 可读性 | 代码逻辑 | 自然语言 |

## 📝 相关文档

- **complexity-guide.md**: 详细的复杂度判断标准和示例
- **agent-selection.md**: Agent选择规则和映射关系  
- **execution-templates.md**: 不同复杂度的执行模板
- **feishu-config.md**: 飞书集成配置说明
- **examples.md**: 典型使用场景和示例
- **CONTRIBUTING.md**: 开发规范和贡献指南

## ⚠️ 使用说明

### v0.0.1 限制
- **实验版本**: 功能还在完善中
- **文档驱动**: 主要依赖文档指导，可能需要调整
- **反馈欢迎**: 需要用户使用反馈来改进
- **持续迭代**: 会根据使用情况不断优化

### 适用场景
- ✅ 学习AI驱动的任务编排理念
- ✅ 验证.md文档驱动的架构设计
- ✅ 简单到中等复杂度的任务编排
- ❌ 生产环境的关键任务 (等待v1.0.0)

## 🔮 版本规划

- **v0.0.1**: 基础文档+脚本，验证设计理念 (当前)
- **v0.1.0**: 功能稳定，用户反馈整合
- **v0.2.0**: 性能优化，体验改进  
- **v1.0.0**: 生产就绪，正式发布

## 🤝 贡献

欢迎贡献代码、文档或使用反馈！

- **GitHub**: https://github.com/Risker-C/openclaw-task-orchestrator
- **Issues**: 报告问题或提出建议
- **贡献指南**: 参见 CONTRIBUTING.md

---

**Task Orchestrator v0.0.1 - 让AI来判断，让编排更智能** 🎯
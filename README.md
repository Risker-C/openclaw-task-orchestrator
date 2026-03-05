# Task Orchestrator v0.0.1 - AI驱动的智能任务编排系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-2026.3.2+-green.svg)](https://openclaw.ai)
[![Version](https://img.shields.io/badge/version-0.0.1-orange.svg)](https://github.com/Risker-C/openclaw-task-orchestrator/releases)

## 🎯 项目愿景

**从复杂代码到智能文档的架构革新**

Task Orchestrator v0.0.1 是一个基于.md文档驱动的OpenClaw Skill，通过AI直接分析任务复杂度，自动选择最优的执行策略，实现智能化的多Agent任务编排。

### ⚠️ 版本说明
- **当前版本**: v0.0.1 (初始版本)
- **状态**: 实验性质，功能验证阶段
- **目标**: 验证.md文档驱动的设计理念
- **适用**: 学习、参考、功能验证

## 🚀 核心特性

### ✨ AI驱动的复杂度判断
- 使用AI直接分析任务复杂度（L1/L2/L3）
- 自动适应新领域和边缘情况
- 提供详细判断理由和置信度评分

### 🎯 智能执行策略
- **L1任务**: 直接执行建议（5-15分钟）
- **L2任务**: 单Agent专业处理（30-90分钟）
- **L3任务**: 多Agent协作编排（2-6小时）

### 📱 飞书深度集成
- 自动同步Bitable工单状态
- 实时任务进度通知
- 可视化任务管理面板

### 🔧 OpenClaw原生集成
- 基于sessions_send的可靠通信
- 避免sessions_spawn的已知问题
- 完整的Agent状态监控

### 🚨 智能监控系统
- 按需启动的subagent失败检测
- 零token消耗的后台监控
- 30秒内自动发现并处理失败任务
- 没有任务时零资源消耗

## 📋 快速开始

### 安装要求
- Python 3.8+
- OpenClaw 2026.3.2+
- 飞书应用配置（可选）

### 基本使用
```bash
# 1. 克隆项目到OpenClaw Skill目录
git clone https://github.com/Risker-C/openclaw-task-orchestrator.git
cd ~/.openclaw/workspace/skills/task-orchestrator

# 2. 直接使用（无需安装依赖）
# 在OpenClaw中直接对话即可：
"帮我分析网站性能问题"

# 3. 配置飞书集成（可选）
# 参考 feishu-config.md 进行配置
```

### 使用示例
```
用户: "设计微服务架构"
↓
AI判断: L3任务（复杂系统设计）
↓
执行策略: 多Agent协作
↓
结果: 完整的架构设计方案
```

## 🎨 架构设计

### 核心理念
- ✅ **.md文档驱动**: 主要逻辑通过文档指导
- ✅ **OpenClaw原生**: 充分利用现有AI能力
- ✅ **必要脚本**: 只有技术实现才用Python
- ✅ **简洁专一**: 专注任务编排核心价值

### 项目结构
```
~/.openclaw/workspace/skills/task-orchestrator/
├── SKILL.md                    # 核心Skill文档
├── README.md                   # 项目说明 (本文件)
├── CONTRIBUTING.md             # 开发规范
├── complexity-guide.md         # 复杂度判断指南
├── agent-selection.md          # Agent选择规则
├── execution-templates.md      # 执行模板
├── feishu-config.md           # 飞书配置说明
├── examples.md                # 使用示例
├── .github/                   # GitHub模板
│   ├── ISSUE_TEMPLATE/        # Issue模板
│   └── pull_request_template.md
└── scripts/                   # 必要脚本 (待实现)
    ├── feishu-sync.py         # 飞书同步
    └── feishu-notify.py       # 消息通知
```

### v0.0.1 vs 传统方案对比

| 方面 | 传统代码驱动 | Task Orchestrator v0.0.1 |
|------|-------------|---------------------------|
| 复杂度判断 | 复杂算法 | AI直接分析 |
| 维护成本 | 高 | 低 |
| 扩展性 | 需要代码更新 | 文档调整 |
| 可读性 | 代码逻辑 | 自然语言 |
| 学习成本 | 高 | 低 |

## 📊 功能特性

### 复杂度分级标准

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

### Agent选择规则
- **技术类任务** → architect, code-reviewer
- **文档类任务** → doc-engineer  
- **研究类任务** → research-analyst
- **设计类任务** → ui-designer, architect
- **安全类任务** → security-monitor
- **管理类任务** → implementation-planner, resource-manager

详细规则参见 [agent-selection.md](agent-selection.md)

## 🔧 配置说明

### OpenClaw配置要求
确保OpenClaw配置中关闭agentToAgent：
```json
{
  "tools": {
    "agentToAgent": {
      "enabled": false
    }
  }
}
```

### 飞书集成配置（可选）
参考 [feishu-config.md](feishu-config.md) 进行详细配置：
- 创建飞书应用
- 配置权限和Bitable
- 设置通知和同步

## 📚 文档导航

| 文档 | 描述 | 适用人群 |
|------|------|----------|
| [SKILL.md](SKILL.md) | 核心功能说明 | 所有用户 |
| [complexity-guide.md](complexity-guide.md) | 复杂度判断标准 | 开发者、高级用户 |
| [agent-selection.md](agent-selection.md) | Agent选择规则 | 开发者、系统管理员 |
| [execution-templates.md](execution-templates.md) | 执行流程模板 | 开发者 |
| [feishu-config.md](feishu-config.md) | 飞书集成配置 | 企业用户 |
| [examples.md](examples.md) | 使用示例 | 新用户、学习者 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 开发规范 | 贡献者 |

## 🎯 使用场景

### ✅ 适用场景
- 学习AI驱动的任务编排理念
- 验证.md文档驱动的架构设计
- 简单到中等复杂度的任务编排
- 团队协作和任务分配
- 飞书工单化管理

### ❌ 不适用场景
- 生产环境的关键任务 (等待v1.0.0)
- 需要实时响应的紧急任务
- 超大规模的复杂项目管理
- 需要严格SLA保证的场景

## 🔮 版本规划

| 版本 | 状态 | 主要目标 | 预计时间 |
|------|------|---------|----------|
| **v0.0.1** | 开发中 | 基础文档+脚本，验证设计理念 | 2026-03-10 |
| **v0.1.0** | 规划中 | 功能稳定，用户反馈整合 | 2026-04-01 |
| **v0.2.0** | 规划中 | 性能优化，体验改进 | 2026-05-01 |
| **v1.0.0** | 远期 | 生产就绪，正式发布 | 2026-Q3 |

### v0.1.0 计划改进
- 真实AI API集成优化
- 增强飞书集成功能
- 完善错误处理机制
- 添加使用统计和分析

### v0.2.0 计划改进
- Web监控面板开发
- 性能优化和缓存机制
- 支持自定义Agent配置
- 多租户支持

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 快速贡献
```bash
# 1. Fork项目
# 2. 创建feature分支
git checkout -b feature/issue-{number}-{description}

# 3. 提交变更
git commit -m "feat(scope): description

Closes #{issue-number}"

# 4. 推送并创建PR
git push origin feature/issue-{number}-{description}
```

### 开发规范
- 遵循Git提交规范
- 使用Issue驱动开发
- 完善文档和示例
- 确保代码质量

## 📊 项目状态

### 当前进度
- [x] 核心架构设计 ✅
- [x] 文档体系建立 ✅
- [ ] 飞书脚本实现 🚧
- [ ] 功能测试验证 📋
- [ ] 用户反馈收集 📋

### 开发活跃度
- **最近更新**: 2026-03-05
- **开放Issues**: 5个
- **已完成Issues**: 18个
- **代码提交**: 活跃开发中

## 📞 支持和反馈

### 获取帮助
- **GitHub Issues**: 报告问题或提出建议
- **文档**: 查看详细的使用文档
- **示例**: 参考examples.md中的使用案例

### 联系方式
- **项目维护者**: Ikaros (伊卡洛斯)
- **GitHub**: https://github.com/Risker-C/openclaw-task-orchestrator
- **OpenClaw社区**: https://discord.com/invite/clawd

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenClaw](https://openclaw.ai) - 强大的AI Agent平台
- [飞书开放平台](https://open.feishu.cn) - 企业协作集成
- 所有贡献者和社区成员

---

**Task Orchestrator v0.0.1 - 让AI来判断，让编排更智能** 🎯

*这是一个实验性项目，旨在探索AI驱动的任务编排新模式。欢迎试用并提供反馈！*
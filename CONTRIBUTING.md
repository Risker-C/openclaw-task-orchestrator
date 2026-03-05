# Contributing to Task Orchestrator

欢迎为 Task Orchestrator 项目贡献代码！本文档将指导您如何参与项目开发。

## 🎯 项目理念

Task Orchestrator 是一个基于 .md 文档驱动的 OpenClaw Skill，专注于 AI 驱动的任务编排。

### 核心原则
- **文档驱动**: 主要逻辑通过 .md 文档指导
- **OpenClaw 原生**: 充分利用 OpenClaw 现有能力
- **必要脚本**: 只有复杂技术实现才使用 Python 脚本
- **简洁专一**: 专注于任务编排核心价值

## 📋 开发流程

### 1. Issue 生命周期

#### 创建阶段
- **标题格式**: `🔧 功能描述` 或 `📝 文档描述` 或 `🐛 问题描述`
- **内容结构**: 
  - 任务描述
  - 目标
  - 技术要求
  - 验收标准
  - 时间安排
- **标记**: 优先级 (High/Medium/Low) + 复杂度 (L1/L2/L3)

#### 执行阶段
- **开始标记**: 在 Issue 中添加开始时间注释
- **进度更新**: 定期更新执行状态和遇到的问题
- **代码提交**: 每个提交都要关联 Issue 编号

#### 关闭阶段
- **验收确认**: 所有验收标准都已满足
- **提交记录**: 必须有对应的 Git 提交记录
- **文档更新**: 相关文档已同步更新
- **关闭说明**: 简要说明完成情况

### 2. Git 提交规范

#### 提交消息格式
```
<type>(<scope>): <subject>

<body>

Closes #<issue-number>
```

#### 类型说明
- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

#### 示例
```
docs(core): 创建 SKILL.md 核心文档

- 添加任务编排工作流程说明
- 定义 L1/L2/L3 复杂度标准
- 提供 Agent 选择规则

Closes #24
```

### 3. 分支管理

#### 分支命名规范
- **feature/issue-{number}-{description}**: 功能开发
- **docs/issue-{number}-{description}**: 文档更新
- **fix/issue-{number}-{description}**: 问题修复

#### 工作流程
1. 从 `main` 分支创建 feature 分支
2. 在 feature 分支上开发
3. 提交时关联 Issue 编号
4. 创建 Pull Request
5. 代码审查通过后合并到 `main`
6. 删除 feature 分支

## 📊 版本管理

### 版本号规范
- **v0.0.x**: 初始开发版本，功能验证
- **v0.x.0**: 功能版本，新特性添加
- **v1.0.0**: 正式发布版本，生产就绪

### 里程碑管理
- **v0.0.1**: 基础文档 + 脚本实现
- **v0.1.0**: 功能稳定 + 用户反馈整合
- **v0.2.0**: 性能优化 + 体验改进

## 🔧 开发环境

### 项目结构
```
~/.openclaw/workspace/skills/task-orchestrator/
├── SKILL.md                    # 核心 Skill 文档
├── README.md                   # 项目说明
├── CONTRIBUTING.md             # 开发规范 (本文件)
├── complexity-guide.md         # 复杂度判断指南
├── agent-selection.md          # Agent 选择规则
├── execution-templates.md      # 执行模板
├── feishu-config.md           # 飞书配置说明
├── examples.md                # 使用示例
└── scripts/                   # 必要脚本
    ├── feishu-sync.py         # 飞书同步
    └── feishu-notify.py       # 消息通知
```

### 开发要求
- **Python 3.8+**: 脚本开发环境
- **OpenClaw**: 运行环境
- **GitHub CLI**: 项目管理工具
- **Markdown 编辑器**: 文档编写

## 📝 文档规范

### Markdown 文档
- 使用清晰的标题层级
- 提供丰富的示例
- 包含版本信息
- 保持内容更新

### 代码注释
- Python 脚本使用 docstring
- 关键逻辑添加行内注释
- 配置文件添加说明注释

## 🧪 质量保证

### 代码质量
- 遵循 PEP 8 Python 代码规范
- 函数和类添加类型提示
- 错误处理要完善
- 日志记录要详细

### 文档质量
- 结构清晰易懂
- 示例丰富实用
- 更新及时准确
- 版本控制规范

### 测试验证
- 功能测试通过
- 边界情况考虑
- 错误场景处理
- 用户体验良好

## 🤝 贡献方式

### 1. 报告问题
- 使用 GitHub Issues 报告 bug
- 提供详细的复现步骤
- 包含环境信息和错误日志

### 2. 提出建议
- 使用 GitHub Issues 提出功能建议
- 说明使用场景和预期效果
- 考虑与项目理念的契合度

### 3. 提交代码
- Fork 项目到个人仓库
- 创建 feature 分支进行开发
- 提交 Pull Request
- 等待代码审查和合并

## 📞 联系方式

- **GitHub Issues**: 项目相关问题和建议
- **项目维护者**: Ikaros (伊卡洛斯)
- **OpenClaw 社区**: https://discord.com/invite/clawd

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

感谢您对 Task Orchestrator 项目的贡献！🎉
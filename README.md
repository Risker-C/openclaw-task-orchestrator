# OpenClaw Task Orchestrator

基于OpenClaw和飞书深度集成的智能任务编排系统

## 核心特性

- **异步工单机制**: 主Agent立即响应，后台Agent池并行执行
- **智能复杂度判断**: L1/L2/L3自动分流，支持手动指定
- **飞书深度集成**: Bitable看板、拖拽操作、实时协作
- **OpenSpec工作流**: propose→apply→archive标准流程
- **可观测性**: 实时状态追踪，完整生命周期管理

## 架构设计

### 分层架构
```
应用层 (Application Layer)
├── 主Agent交互 (立即响应、需求理解、工单创建)
│
编排层 (Orchestration Layer)  
├── 任务调度器 (智能复杂度判断、路由分发)
├── 工单管理器 (状态同步、生命周期管理)
│
执行层 (Execution Layer)
├── Agent池管理 (并行执行、负载均衡)
├── Skills/MCP集成 (能力扩展)
│
数据层 (Data Layer)
├── 飞书Bitable (工单存储、看板可视化)
├── 状态持久化 (任务状态、执行日志)
│
通信层 (Communication Layer)
├── 飞书消息推送 (状态通知、完成提醒)
├── 审批流程集成 (重要任务审批)
```

### 任务复杂度分级
- **L1简单任务**: 单Agent直接执行 (查询信息、生成简单报告)
- **L2单步任务**: 专业Agent处理 (分析文档、设计方案)  
- **L3复杂任务**: 多Agent协作 (系统设计、多轮迭代)

## 技术栈

- **核心框架**: OpenClaw (sessions_spawn, subagents)
- **数据存储**: 飞书Bitable (工单管理、看板可视化)
- **消息通知**: 飞书消息卡片、机器人
- **文档管理**: 飞书Docs、Wiki自动归档
- **扩展机制**: Skills + MCP双重支持

## 快速开始

### 环境要求
- OpenClaw运行环境
- 飞书应用权限配置
- Python 3.8+

### 安装部署
```bash
# 克隆项目
git clone <repository-url>
cd openclaw-task-orchestrator

# 安装依赖
pip install -r requirements.txt

# 配置飞书集成
cp config/feishu.example.json config/feishu.json
# 编辑config/feishu.json，填入app_token等配置

# 初始化飞书Bitable表结构
python scripts/init_bitable.py

# 启动任务调度器
python src/orchestrator/main.py
```

## 项目结构

```
openclaw-task-orchestrator/
├── README.md                 # 项目说明
├── requirements.txt          # Python依赖
├── config/                   # 配置文件
│   ├── feishu.example.json  # 飞书配置模板
│   └── orchestrator.yaml   # 调度器配置
├── src/                     # 源代码
│   ├── core/               # 核心模块
│   │   ├── task_manager.py # 任务管理器
│   │   ├── complexity.py   # 复杂度判断
│   │   └── scheduler.py    # 任务调度器
│   ├── integrations/       # 集成模块
│   │   ├── feishu/        # 飞书集成
│   │   └── openclaw/      # OpenClaw集成
│   ├── orchestrator/       # 编排器
│   │   └── main.py        # 主程序入口
│   └── utils/             # 工具函数
├── scripts/                # 脚本工具
│   ├── init_bitable.py    # 初始化Bitable
│   └── deploy.sh          # 部署脚本
├── tests/                  # 测试用例
└── docs/                   # 文档
    ├── architecture.md     # 架构设计
    ├── api.md             # API文档
    └── deployment.md      # 部署指南
```

## 开发计划

### Phase 1: 核心框架 (1-2周)
- [x] 项目结构搭建
- [ ] 异步工单机制实现
- [ ] 飞书Bitable集成
- [ ] 基础任务调度

### Phase 2: 智能编排 (3-4周)  
- [ ] 复杂度智能判断
- [ ] OpenSpec工作流集成
- [ ] 多Agent协作机制
- [ ] 状态同步优化

### Phase 3: 高级功能 (5-6周)
- [ ] 飞书原生审批集成
- [ ] 实时hooks同步
- [ ] 性能监控优化
- [ ] 扩展能力完善

## 参考项目

本项目融合了以下开源项目的最佳实践：
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) - 规范驱动开发
- [edict](https://github.com/cft0808/edict) - 异步工单机制
- [Magi](https://github.com/MistRipple/magi-docs) - 智能复杂度判断
- [CCG-workflow](https://github.com/fengshao1227/ccg-workflow) - 多模型协作
- 以及其他6个相关项目的核心洞察

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: OpenClaw Team
- 问题反馈: GitHub Issues
- 技术讨论: 项目Wiki
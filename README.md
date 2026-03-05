# OpenClaw Task Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-green.svg)](https://openclaw.ai)

基于OpenClaw和飞书深度集成的智能任务编排系统，解决主Agent阻塞问题，实现真正的异步多任务处理。

## 🚀 核心特性

- **🔄 异步工单机制**: 主Agent立即响应，后台Agent池并行执行，彻底解决阻塞问题
- **🧠 智能复杂度判断**: L1/L2/L3自动分流，基于Magi项目最佳实践，避免算力浪费
- **📱 飞书深度集成**: Bitable看板、拖拽操作、实时协作、移动端原生体验
- **📋 OpenSpec工作流**: propose→apply→archive标准流程，规范驱动开发
- **👁️ 可观测性**: 实时状态追踪，完整任务生命周期管理，Agent健康监控

## 🎯 解决的核心问题

**Before (阻塞模式)**:
```
Master: "设计用户注册系统"
系统: [30分钟后] "已完成，请查看结果"
Master: [只能等待，无法发起新任务] ❌
```

**After (异步工单模式)**:
```
Master: "设计用户注册系统"
主Agent: "已理解需求，工单#001已创建，预计30分钟完成"
Master: "再帮我分析一下竞品"
主Agent: "好的，工单#002已创建，将在工单#001完成后处理"
Master: [可以继续交互，查看进度，调整优先级] ✅
```

## 🏗️ 架构设计

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
- **L1简单任务**: 查询信息、生成简单报告 → 单Agent直接执行 (5-10分钟)
- **L2单步任务**: 分析文档、设计方案 → 专业Agent处理 (30-60分钟)  
- **L3复杂任务**: 系统设计、多轮迭代 → 多Agent协作 (2-4小时)

## 🚀 快速开始

### 环境要求
- Python 3.8+
- OpenClaw运行环境
- 飞书应用权限配置

### 安装部署

1. **克隆项目**
```bash
git clone https://github.com/Risker-C/openclaw-task-orchestrator.git
cd openclaw-task-orchestrator
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置飞书集成**
```bash
# 复制配置模板
cp config/feishu.example.json config/feishu.json

# 编辑配置文件，填入你的飞书应用信息
nano config/feishu.json
```

4. **初始化飞书Bitable表结构**
```bash
python scripts/init_bitable.py
```

5. **启动任务编排器**
```bash
python src/orchestrator/main.py
```

### 配置说明

**飞书应用配置** (`config/feishu.json`):
```json
{
  "app_id": "your_feishu_app_id",
  "app_secret": "your_feishu_app_secret", 
  "app_token": "your_bitable_app_token",
  "table_configs": {
    "tasks": {
      "table_id": "your_tasks_table_id"
    }
  }
}
```

**编排器配置** (`config/orchestrator.yaml`):
```yaml
orchestrator:
  scheduler:
    max_concurrent_tasks: 10
    polling_interval: 30
  complexity:
    auto_detect: true
    manual_override: true
```

## 📖 使用示例

### 基础API调用

```python
from src.orchestrator.main import TaskAPI

# 创建简单任务
result = await TaskAPI.create_task(
    title="生成项目文档",
    description="为当前项目生成完整的API文档",
    priority="medium"
)

# 创建复杂任务并指定复杂度
result = await TaskAPI.create_task(
    title="设计用户认证系统", 
    description="设计完整的JWT认证系统，包括登录、注册、权限管理",
    priority="high",
    complexity="L3"
)

# 查看任务状态
task = await TaskAPI.get_task(task_id)
print(f"任务状态: {task['status']}, 进度: {task['progress']}%")

# 列出所有进行中的任务
tasks = await TaskAPI.list_tasks(status="running")
```

### 飞书看板操作

1. **查看工单看板**: 在飞书Bitable中按状态分组查看所有任务
2. **拖拽更新状态**: 直接拖拽任务卡片到不同状态列
3. **实时协作**: 多人同时查看和操作，实时同步更新
4. **移动端管理**: 飞书App中完整的任务管理体验

### OpenClaw集成

```python
# 在OpenClaw主会话中使用
Master: "帮我设计一个博客系统的数据库架构"

# 系统自动判断为L2任务，调用architect agent
主Agent: "已创建工单#003，复杂度L2，分配给architect agent，预计45分钟完成"

# 可以继续发起新任务
Master: "同时帮我分析一下竞品的用户体验"
主Agent: "已创建工单#004，复杂度L2，分配给research-analyst，将在工单#003完成后处理"
```

## 🔧 开发指南

### 项目结构
```
openclaw-task-orchestrator/
├── src/
│   ├── core/                   # 核心模块
│   │   ├── task_manager.py     # 任务生命周期管理
│   │   ├── complexity.py       # 智能复杂度判断
│   │   └── scheduler.py        # 任务调度器
│   ├── integrations/           # 集成模块
│   │   ├── feishu/            # 飞书集成
│   │   └── openclaw/          # OpenClaw集成
│   └── orchestrator/           # 编排器
├── config/                     # 配置文件
├── scripts/                    # 工具脚本
└── tests/                      # 测试用例
```

### 扩展开发

**添加新的Agent类型**:
```python
# 在 src/core/scheduler.py 中注册
specialist_agents = {
    TaskComplexity.L2_SINGLE: [
        "research-analyst", "doc-engineer", "code-reviewer",
        "your-new-agent"  # 添加新Agent
    ]
}
```

**自定义复杂度判断**:
```python
# 在 src/core/complexity.py 中扩展
def _analyze_custom_keywords(self, text: str) -> float:
    custom_keywords = {
        "blockchain": 4.0,
        "machine-learning": 3.5,
        # 添加领域特定关键词
    }
    return self._calculate_keyword_score(text, custom_keywords)
```

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [Issues](https://github.com/Risker-C/openclaw-task-orchestrator/issues) 了解当前的开发计划。

### 开发流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### Issues 驱动开发
- 🐛 **Bug报告**: 使用 `bug` 标签
- 🚀 **功能请求**: 使用 `enhancement` 标签  
- 📚 **文档改进**: 使用 `documentation` 标签
- 🔧 **技术债务**: 使用 `tech-debt` 标签

## 📊 参考项目

本项目融合了以下开源项目的最佳实践：
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) - 规范驱动开发
- [edict](https://github.com/cft0808/edict) - 异步工单机制
- [Magi](https://github.com/MistRipple/magi-docs) - 智能复杂度判断
- [CCG-workflow](https://github.com/fengshao1227/ccg-workflow) - 多模型协作
- 以及其他6个相关项目的核心洞察

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [OpenClaw官网](https://openclaw.ai)
- [OpenClaw文档](https://docs.openclaw.ai)
- [飞书开放平台](https://open.feishu.cn)
- [项目Wiki](https://github.com/Risker-C/openclaw-task-orchestrator/wiki)

## 💬 社区支持

- 🐛 [报告Bug](https://github.com/Risker-C/openclaw-task-orchestrator/issues/new?template=bug_report.md)
- 💡 [功能建议](https://github.com/Risker-C/openclaw-task-orchestrator/issues/new?template=feature_request.md)
- 💬 [讨论交流](https://github.com/Risker-C/openclaw-task-orchestrator/discussions)

---

**让AI协作更智能，让任务管理更高效！** 🚀

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
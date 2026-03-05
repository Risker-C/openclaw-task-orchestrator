# Agent选择规则 v0.0.1

## 📋 版本说明

- **版本**: v0.0.1 (初始版本)
- **状态**: 基础选择规则，会根据使用反馈优化
- **目标**: 为AI提供清晰的Agent选择依据

## 🎯 选择原则

### 核心理念
1. **专业匹配**: 根据任务领域选择最合适的专业Agent
2. **能力互补**: 考虑Agent的核心能力和专长
3. **负载均衡**: 避免单个Agent过载
4. **备选机制**: 提供备选Agent以应对异常情况

### 选择流程
1. 分析任务的主要领域和技术要求
2. 匹配Agent的专业能力
3. 考虑Agent的当前工作负载
4. 选择最优Agent并提供备选方案

## 🤖 Agent能力矩阵

### 技术开发类Agent

#### architect (系统架构师)
- **核心能力**: 系统架构设计、技术选型、可行性评估
- **适用任务**: 
  - 系统架构设计
  - 技术方案评估
  - 性能优化分析
  - 技术选型建议
- **关键词**: 架构、系统、设计、技术方案、性能、扩展性
- **复杂度**: 主要处理L2-L3任务

#### code-reviewer (代码审查专家)
- **核心能力**: 代码质量审查、安全审计、最佳实践
- **适用任务**:
  - 代码审查和优化
  - 安全漏洞检测
  - 代码规范检查
  - 重构建议
- **关键词**: 代码、审查、优化、安全、规范、重构
- **复杂度**: 主要处理L1-L2任务

### 文档和内容类Agent

#### doc-engineer (文档工程师)
- **核心能力**: 技术文档编写、知识管理、飞书文档操作
- **适用任务**:
  - 技术文档编写
  - API文档生成
  - 用户手册制作
  - 飞书文档管理
- **关键词**: 文档、说明、手册、API、飞书、知识库
- **复杂度**: 主要处理L1-L2任务

### 研究和分析类Agent

#### research-analyst (研究分析师)
- **核心能力**: 数据分析、市场研究、技术调研、报告生成
- **适用任务**:
  - 技术调研分析
  - 市场趋势研究
  - 数据分析报告
  - 竞品分析
- **关键词**: 研究、分析、调研、数据、报告、趋势
- **复杂度**: 主要处理L2-L3任务

### 设计和用户体验类Agent

#### ui-designer (UI/UX设计师)
- **核心能力**: 界面设计、用户体验、交互原型、设计规范
- **适用任务**:
  - 界面设计
  - 用户体验优化
  - 交互原型制作
  - 设计规范制定
- **关键词**: 设计、界面、用户体验、UI、UX、原型
- **复杂度**: 主要处理L2-L3任务

### 项目管理类Agent

#### implementation-planner (实施规划师)
- **核心能力**: 项目规划、里程碑管理、资源分配、风险评估
- **适用任务**:
  - 项目实施规划
  - 里程碑设定
  - 资源需求分析
  - 风险识别和应对
- **关键词**: 规划、项目、里程碑、资源、风险、计划
- **复杂度**: 主要处理L2-L3任务

#### resource-manager (资源管理者)
- **核心能力**: 资源优化、成本控制、容量规划、性能监控
- **适用任务**:
  - 资源使用优化
  - 成本分析控制
  - 容量规划
  - 性能监控分析
- **关键词**: 资源、成本、容量、性能、优化、监控
- **复杂度**: 主要处理L1-L2任务

### 安全和监控类Agent

#### security-monitor (安全监控专家)
- **核心能力**: 安全审计、风险评估、监控告警、应急响应
- **适用任务**:
  - 安全风险评估
  - 安全策略制定
  - 监控告警配置
  - 安全事件响应
- **关键词**: 安全、风险、监控、告警、审计、防护
- **复杂度**: 主要处理L2-L3任务

### 协调和编排类Agent

#### task-orchestrator (任务编排者)
- **核心能力**: 多Agent协调、任务分解、状态跟踪、结果整合
- **适用任务**:
  - L3复杂任务的协调
  - 多Agent工作流编排
  - 任务状态跟踪
  - 结果整合汇总
- **关键词**: 协调、编排、多任务、整合、流程
- **复杂度**: 专门处理L3任务

#### strategic-advisor (战略顾问)
- **核心能力**: 战略决策、商业分析、长期规划、高层建议
- **适用任务**:
  - 重大战略决策
  - 商业模式分析
  - 长期发展规划
  - 高层决策支持
- **关键词**: 战略、决策、商业、规划、高层、长期
- **复杂度**: 处理关键L3任务 (高成本)

## 📊 选择规则矩阵

### 按任务类型选择

| 任务类型 | 首选Agent | 备选Agent | 说明 |
|---------|-----------|-----------|------|
| **技术架构** | architect | code-reviewer | 系统设计优先架构师 |
| **代码相关** | code-reviewer | architect | 代码质量优先审查专家 |
| **文档编写** | doc-engineer | research-analyst | 文档专业性优先 |
| **数据分析** | research-analyst | resource-manager | 分析能力优先 |
| **界面设计** | ui-designer | architect | 设计专业性优先 |
| **项目规划** | implementation-planner | task-orchestrator | 规划能力优先 |
| **安全相关** | security-monitor | architect | 安全专业性优先 |
| **资源优化** | resource-manager | architect | 资源管理优先 |
| **多任务协调** | task-orchestrator | implementation-planner | 协调能力优先 |
| **战略决策** | strategic-advisor | research-analyst | 战略高度优先 |

### 按关键词匹配

#### 技术关键词 → architect
- 架构、系统、设计、技术方案、性能、扩展性、微服务、分布式

#### 代码关键词 → code-reviewer  
- 代码、审查、优化、重构、规范、质量、安全漏洞

#### 文档关键词 → doc-engineer
- 文档、说明、手册、API、飞书、知识库、教程

#### 分析关键词 → research-analyst
- 研究、分析、调研、数据、报告、趋势、统计

#### 设计关键词 → ui-designer
- 设计、界面、用户体验、UI、UX、原型、交互

#### 规划关键词 → implementation-planner
- 规划、项目、计划、里程碑、排期、实施

#### 安全关键词 → security-monitor
- 安全、风险、监控、告警、审计、防护、漏洞

#### 资源关键词 → resource-manager
- 资源、成本、容量、性能、优化、监控、负载

## 🔄 选择算法

### 基础选择流程
```python
def select_agent(task_description, complexity):
    # 1. 关键词匹配
    keywords = extract_keywords(task_description)
    candidate_agents = match_by_keywords(keywords)
    
    # 2. 复杂度过滤
    suitable_agents = filter_by_complexity(candidate_agents, complexity)
    
    # 3. 负载均衡 (未来实现)
    # available_agents = check_agent_availability(suitable_agents)
    
    # 4. 选择最优Agent
    selected_agent = suitable_agents[0] if suitable_agents else "research-analyst"
    
    return selected_agent
```

### 特殊情况处理

#### L3任务的特殊处理
- 如果是L3任务，优先考虑task-orchestrator进行协调
- 如果涉及战略决策，考虑strategic-advisor
- 如果是技术架构类L3任务，architect + task-orchestrator组合

#### 默认选择
- 当无法明确匹配时，默认选择research-analyst
- research-analyst具有较强的通用分析能力
- 可以作为任务分析的起点

#### 备选机制
- 每个选择都提供备选Agent
- 当首选Agent不可用时，自动选择备选
- 记录选择原因，便于优化

## 📈 优化机制

### 反馈学习
- 收集任务执行效果反馈
- 分析Agent选择的准确性
- 调整关键词权重和匹配规则

### 性能监控
- 跟踪各Agent的任务完成质量
- 监控Agent的响应时间和可用性
- 基于性能数据优化选择策略

## 🔮 未来改进

### v0.1.0 计划
- 增加Agent负载监控
- 实现动态负载均衡
- 添加Agent能力评估机制

### v0.2.0 计划
- 引入机器学习优化选择
- 支持用户自定义Agent偏好
- 实现Agent协作效果分析

---

**这是Task Orchestrator v0.0.1的Agent选择核心规则，将根据使用效果持续优化。** 🤖
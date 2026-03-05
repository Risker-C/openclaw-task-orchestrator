# 使用示例 v0.0.1

## 📋 版本说明

- **版本**: v0.0.1 (初始版本)
- **状态**: 基础使用示例，涵盖主要功能场景
- **目标**: 帮助用户快速理解和使用Task Orchestrator

## 🎯 快速开始

### 基本使用流程
```
1. 用户描述任务
2. AI分析复杂度
3. 选择合适Agent
4. 执行任务
5. 返回结果
```

### 第一个示例
```
用户: "帮我查询服务器的CPU使用率"

AI处理过程:
1. 读取complexity-guide.md → 判断为L1任务 (简单查询)
2. 直接提供执行建议，无需分配Agent
3. 返回具体的查询方法和命令
```

## 📊 L1任务示例 (简单任务)

### 示例1: 系统状态查询
```
用户输入:
"检查数据库连接状态"

AI分析:
- 复杂度: L1 (简单查询操作)
- 处理方式: 直接执行
- 预计时间: 5-10分钟

AI回复:
您可以通过以下方式检查数据库连接状态:

1. **命令行检查**:
   ```bash
   # MySQL
   mysqladmin -u username -p status
   
   # PostgreSQL  
   pg_isready -h localhost -p 5432
   
   # Redis
   redis-cli ping
   ```

2. **应用层检查**:
   ```python
   # Python示例
   import psycopg2
   try:
       conn = psycopg2.connect("dbname=test user=postgres")
       print("数据库连接正常")
   except:
       print("数据库连接失败")
   ```

3. **监控工具**:
   - 使用Grafana/Prometheus监控面板
   - 查看应用日志中的连接错误
   - 使用数据库管理工具连接测试
```

### 示例2: 用户信息查询
```
用户输入:
"查询用户邮箱为john@example.com的账户信息"

AI分析:
- 复杂度: L1 (数据查询)
- 处理方式: 直接执行
- 预计时间: 5分钟

AI回复:
以下是查询用户账户信息的方法:

1. **数据库查询**:
   ```sql
   SELECT id, username, email, status, created_at, last_login
   FROM users 
   WHERE email = 'john@example.com';
   ```

2. **API调用**:
   ```bash
   curl -X GET "https://api.yoursite.com/users?email=john@example.com" \
        -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **管理后台操作**:
   - 登录管理后台
   - 进入用户管理页面
   - 使用邮箱搜索功能
   - 查看用户详细信息

**注意事项**:
- 确保有相应的查询权限
- 注意保护用户隐私信息
- 记录查询操作日志
```

## 📊 L2任务示例 (专业任务)

### 示例1: 性能分析任务
```
用户输入:
"分析我们网站的性能瓶颈，并提出优化建议"

AI分析:
- 复杂度: L2 (需要专业技术分析)
- 选择Agent: architect (系统架构师)
- 预计时间: 60-90分钟

AI处理流程:
1. 根据agent-selection.md选择architect
2. 使用execution-templates.md的L2模板
3. 通过sessions_send分配任务

发送给architect的消息:
---
任务分配通知

**任务标题**: 网站性能瓶颈分析
**复杂度级别**: L2
**预估时间**: 60-90分钟

**任务描述**: 
对网站进行全面的性能分析，识别主要瓶颈点，并提出具体的优化建议。

**具体要求**:
1. 分析前端性能 (页面加载速度、资源优化)
2. 分析后端性能 (API响应时间、数据库查询)
3. 分析基础设施 (服务器资源、网络延迟)
4. 提供具体的优化建议和实施方案

**交付标准**:
- 性能分析报告 (包含数据和图表)
- 优化建议清单 (按优先级排序)
- 实施计划 (包含时间估算)

**截止时间**: 2小时内
---

预期结果:
architect会提供详细的性能分析报告和优化建议
```

### 示例2: 技术文档编写
```
用户输入:
"为我们的REST API编写完整的技术文档"

AI分析:
- 复杂度: L2 (专业文档编写)
- 选择Agent: doc-engineer (文档工程师)
- 预计时间: 45-75分钟

AI处理流程:
发送给doc-engineer的消息:
---
任务分配通知

**任务标题**: REST API技术文档编写
**复杂度级别**: L2
**预估时间**: 45-75分钟

**任务描述**:
为现有的REST API编写完整的技术文档，包括接口说明、参数定义、示例代码等。

**具体要求**:
1. API概览和架构说明
2. 认证和授权机制
3. 所有接口的详细说明 (请求/响应格式)
4. 错误码和异常处理
5. SDK使用示例 (多种编程语言)
6. 最佳实践和注意事项

**交付标准**:
- 结构清晰的Markdown文档
- 包含完整的代码示例
- 提供在线文档链接 (如适用)

**参考资料**:
- 现有API代码库
- Swagger/OpenAPI规范文件
- 现有的简单文档
---

预期结果:
doc-engineer会提供完整、专业的API技术文档
```

## 📊 L3任务示例 (复杂任务)

### 示例1: 微服务架构设计
```
用户输入:
"为我们的电商平台设计完整的微服务架构"

AI分析:
- 复杂度: L3 (系统性设计，需要多领域协作)
- 协调Agent: task-orchestrator
- 预计时间: 4-6小时

AI处理流程:
1. 任务分解为多个子任务
2. 分配给task-orchestrator进行协调
3. 涉及多个专业Agent协作

发送给task-orchestrator的协调消息:
---
多Agent协调任务

**项目**: 电商平台微服务架构设计
**总体目标**: 设计可扩展、高可用的微服务架构
**复杂度**: L3
**预估时间**: 4-6小时

**子任务分解**:
1. 业务需求分析 → research-analyst (1小时)
   - 分析电商业务流程
   - 识别核心业务领域
   - 定义服务边界

2. 架构设计 → architect (2小时)
   - 设计微服务拆分方案
   - 定义服务间通信机制
   - 设计数据存储策略

3. 安全方案设计 → security-monitor (1小时)
   - 设计认证授权机制
   - 制定安全策略
   - 定义安全监控方案

4. 实施规划 → implementation-planner (1小时)
   - 制定迁移计划
   - 定义里程碑和时间表
   - 识别风险和应对措施

5. 文档整理 → doc-engineer (1小时)
   - 整合所有设计文档
   - 编写架构说明
   - 制作部署指南

**协调要求**:
- 确保各子任务的一致性
- 协调Agent间的信息共享
- 整合最终的架构方案
- 进行整体质量检查

**里程碑**:
- 2小时: 需求分析和初步架构完成
- 4小时: 详细设计和安全方案完成
- 6小时: 实施规划和文档整理完成
---

预期结果:
task-orchestrator会协调多个Agent，最终提供完整的微服务架构设计方案
```

### 示例2: 数字化转型规划
```
用户输入:
"制定我们公司的数字化转型技术规划"

AI分析:
- 复杂度: L3 (战略性规划，多领域协作)
- 协调Agent: task-orchestrator + strategic-advisor
- 预计时间: 6-8小时

AI处理流程:
这是一个高层次的战略规划任务，需要strategic-advisor参与

发送给task-orchestrator的协调消息:
---
战略级多Agent协调任务

**项目**: 公司数字化转型技术规划
**总体目标**: 制定全面的数字化转型技术路线图
**复杂度**: L3 (战略级)
**预估时间**: 6-8小时

**子任务分解**:
1. 现状调研 → research-analyst (2小时)
   - 分析当前技术架构
   - 评估数字化成熟度
   - 识别痛点和机会

2. 战略规划 → strategic-advisor (2小时)
   - 制定数字化愿景
   - 定义战略目标
   - 设计转型路径

3. 技术架构 → architect (2小时)
   - 设计目标技术架构
   - 制定技术选型方案
   - 规划基础设施升级

4. 实施计划 → implementation-planner (1.5小时)
   - 制定详细实施计划
   - 定义阶段性目标
   - 评估资源需求

5. 风险评估 → security-monitor (1小时)
   - 识别转型风险
   - 制定风险应对策略
   - 设计安全保障措施

6. 文档整合 → doc-engineer (1.5小时)
   - 整合规划文档
   - 制作执行手册
   - 准备汇报材料

**特殊要求**:
- strategic-advisor负责整体战略指导
- 各Agent需要与strategic-advisor保持密切沟通
- 重点关注商业价值和ROI分析

**交付物**:
- 数字化转型战略报告
- 技术架构规划图
- 详细实施路线图
- 风险评估和应对方案
---

预期结果:
多Agent协作完成企业级的数字化转型技术规划
```

## 🔧 飞书集成示例

### 示例1: 任务状态同步
```
场景: L2任务执行过程中的飞书同步

1. 任务开始时:
python scripts/feishu-sync.py --action create \
  --task-id "perf_analysis_001" \
  --title "网站性能瓶颈分析" \
  --complexity "L2" \
  --agent "architect"

2. 任务进行中:
python scripts/feishu-sync.py --action update \
  --task-id "perf_analysis_001" \
  --status "进行中" \
  --notes "正在分析前端性能指标"

3. 任务完成时:
python scripts/feishu-sync.py --action complete \
  --task-id "perf_analysis_001" \
  --result "发现3个主要性能瓶颈，已提供优化方案"

飞书Bitable中的记录:
| 任务ID | 任务标题 | 复杂度 | 状态 | 分配Agent | 执行结果 |
|--------|----------|--------|------|-----------|----------|
| perf_analysis_001 | 网站性能瓶颈分析 | L2 | 已完成 | architect | 发现3个主要性能瓶颈... |
```

### 示例2: 通知消息发送
```
场景: L3任务协调过程中的通知

1. 任务分配通知:
python scripts/feishu-notify.py \
  --template "task_assigned" \
  --data '{
    "task": "电商平台微服务架构设计",
    "agent": "task-orchestrator",
    "complexity": "L3",
    "deadline": "6小时内"
  }' \
  --target "oc_team_chat_id"

2. 里程碑完成通知:
python scripts/feishu-notify.py \
  --message "🎯 里程碑达成：需求分析和初步架构设计已完成，进入详细设计阶段" \
  --target "oc_project_chat_id"

3. 任务完成通知:
python scripts/feishu-notify.py \
  --template "task_completed" \
  --data '{
    "task": "电商平台微服务架构设计",
    "result": "完整的微服务架构方案已交付",
    "duration": "5.5小时"
  }' \
  --target "oc_management_chat_id"
```

## 🎯 最佳实践示例

### 示例1: 任务描述优化
```
❌ 模糊的任务描述:
"帮我优化一下系统"

✅ 清晰的任务描述:
"分析我们电商网站的页面加载速度，识别性能瓶颈，并提出具体的前端优化建议"

优化效果:
- AI能准确判断为L2任务
- 选择architect进行专业分析
- 提供明确的分析范围和目标
```

### 示例2: 复杂任务拆分
```
原始需求:
"帮我们建立一个完整的DevOps流水线"

AI智能拆分:
1. L2: 现有流程分析 → research-analyst
2. L2: CI/CD工具选型 → architect  
3. L2: 安全策略设计 → security-monitor
4. L2: 实施计划制定 → implementation-planner
5. L1: 文档编写 → doc-engineer

协调方式:
- 使用task-orchestrator进行整体协调
- 按依赖关系安排执行顺序
- 定期同步进度和结果
```

## 🔍 故障排除示例

### 示例1: Agent选择错误
```
问题: 文档编写任务被分配给了architect

原因分析:
- 任务描述中包含"技术架构"关键词
- AI优先匹配了architect而不是doc-engineer

解决方案:
1. 优化任务描述，明确是文档编写任务
2. 更新agent-selection.md中的关键词权重
3. 手动重新分配给doc-engineer

改进后的描述:
"为API接口编写技术文档" → "编写API接口的使用文档和开发指南"
```

### 示例2: 复杂度判断偏差
```
问题: 简单查询被判断为L2任务

原因分析:
- 任务描述中包含"分析"关键词
- AI误判为需要专业分析

解决方案:
1. 澄清任务是简单的数据查询
2. 更新complexity-guide.md中的判断标准
3. 提供更准确的任务描述

改进后的描述:
"分析用户数据" → "查询用户ID为123的基本信息"
```

## 📈 进阶使用技巧

### 技巧1: 批量任务处理
```
场景: 需要处理多个相似的L1任务

方法:
1. 将任务整理成清单
2. 使用统一的描述格式
3. 批量创建飞书工单记录

示例:
tasks = [
    "查询用户ID 001的订单历史",
    "查询用户ID 002的订单历史", 
    "查询用户ID 003的订单历史"
]

for task in tasks:
    # AI处理每个任务
    # 批量同步到飞书
```

### 技巧2: 模板化任务描述
```
创建常用任务模板:

性能分析模板:
"分析{系统名称}的{性能指标}，识别瓶颈并提出优化建议"

文档编写模板:
"为{项目名称}编写{文档类型}，包含{具体要求}"

架构设计模板:
"设计{项目名称}的{架构类型}，满足{业务需求}和{技术要求}"
```

---

**这些示例展示了Task Orchestrator v0.0.1在各种场景下的使用方法，帮助您快速掌握系统的核心功能。** 📚
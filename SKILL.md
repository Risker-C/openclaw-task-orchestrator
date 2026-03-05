# OpenClaw Task Orchestrator

**基于OpenClaw原生工具的智能任务编排系统**

## 🎯 核心价值

解决复杂任务的智能分解、Agent选择和执行编排问题，通过飞书Bitable提供可视化的任务管理界面。

## 🚀 设计理念

### 文档驱动架构
- **纯.md文档设计**：所有逻辑通过markdown文档描述
- **OpenClaw原生工具**：充分利用OpenClaw的feishu工具集
- **零外部依赖**：不引入额外的Python包或服务
- **AI驱动判断**：让AI来分析复杂度，而非复杂算法

### 异步工单机制
```
用户请求 → AI分析复杂度 → 选择Agent → 创建飞书工单 → 异步执行 → 状态同步
```

## 🔧 核心功能

### 1. 智能复杂度分析
基于任务描述，AI自动判断复杂度等级：
- **L1 (简单)**: 单一操作，5分钟内完成
- **L2 (中等)**: 多步骤任务，需要一定思考
- **L3 (复杂)**: 需要深度分析或多轮交互

### 2. Agent智能选择
根据任务类型和复杂度，选择最适合的Agent：
- **architect**: 系统架构设计
- **doc-engineer**: 文档编写和飞书操作
- **research-analyst**: 技术调研
- **ui-designer**: 界面设计
- 等等...

### 3. 飞书Bitable集成
利用OpenClaw的`feishu_bitable_*`工具实现：
- 任务记录创建和更新
- 状态实时同步
- 进度可视化管理
- 结果文档关联

### 4. 消息通知系统
使用OpenClaw的`message`工具：
- 任务分配通知
- 进度更新提醒
- 完成结果推送

## 📋 使用方式

### 基本调用
```markdown
请使用Task Orchestrator分析并执行以下任务：
[任务描述]
```

### 执行流程
1. **复杂度分析**: AI分析任务复杂度和所需技能
2. **Agent选择**: 根据分析结果选择最适合的Agent
3. **工单创建**: 在飞书Bitable中创建任务记录
4. **异步执行**: 通过sessions_send调用选定的Agent
5. **状态同步**: 实时更新任务状态和进度
6. **结果通知**: 完成后发送通知和结果文档

## 🛠️ OpenClaw工具使用

### Bitable操作
```javascript
// 创建任务记录
feishu_bitable_create_record({
  app_token: "your_app_token",
  table_id: "your_table_id", 
  fields: {
    "任务ID": task_id,
    "任务标题": title,
    "复杂度": complexity,
    "状态": "待处理",
    "分配Agent": selected_agent
  }
})

// 更新任务状态
feishu_bitable_update_record({
  app_token: "your_app_token",
  table_id: "your_table_id",
  record_id: record_id,
  fields: {
    "状态": "进行中",
    "进度百分比": 50
  }
})
```

### 消息通知
```javascript
// 发送任务通知
message({
  action: "send",
  message: `🎯 任务分配通知\n任务: ${task_title}\nAgent: ${agent}\n复杂度: ${complexity}`,
  target: "your_chat_id"
})
```

### Agent调用
```javascript
// 异步调用Agent执行任务
sessions_send({
  sessionKey: agent_session_key,
  message: `请执行以下${complexity}任务：\n${task_description}\n\n任务ID: ${task_id}`
})
```

## 📊 配置要求

### OpenClaw飞书配置
在OpenClaw配置文件中设置飞书账户：

```yaml
channels:
  feishu:
    accounts:
      main:
        appId: "cli_xxxxxxxxxx"
        appSecret: "your_app_secret"
        domain: "feishu"  # 或 "lark"
```

### Bitable表格字段
确保Bitable表格包含以下字段：
- 任务ID (单行文本)
- 任务标题 (单行文本) 
- 任务描述 (多行文本)
- 复杂度 (单选: L1/L2/L3)
- 状态 (单选: 待处理/进行中/已完成/失败)
- 优先级 (单选: 低/中/高/紧急)
- 分配Agent (单行文本)
- 创建时间 (日期时间)
- 更新时间 (日期时间)
- 进度百分比 (数字: 0-100)
- Token消耗 (数字)
- 结果文档 (超链接)

## 🎯 最佳实践

### 1. 任务描述规范
- **明确目标**: 清楚描述期望的结果
- **提供上下文**: 包含必要的背景信息
- **指定约束**: 明确时间、资源等限制

### 2. Agent选择策略
- **技能匹配**: 根据任务类型选择专业Agent
- **负载均衡**: 避免单个Agent过载
- **备选方案**: 为关键任务准备备选Agent

### 3. 状态管理
- **及时更新**: 确保状态变更及时同步到Bitable
- **详细记录**: 记录关键节点和决策过程
- **异常处理**: 对失败任务进行分析和重试

## 🔍 故障排除

### 常见问题
1. **Bitable记录创建失败**: 检查app_token和table_id配置
2. **Agent调用无响应**: 确认Agent会话状态和权限
3. **消息通知失败**: 验证chat_id和机器人权限

### 调试方法
- 检查OpenClaw日志中的feishu工具调用记录
- 验证飞书应用权限和配置
- 测试单个工具调用是否正常

## 📚 相关文档

- [复杂度判断指南](complexity-guide.md)
- [Agent选择规则](agent-selection.md) 
- [执行模板](execution-templates.md)
- [飞书配置说明](feishu-config.md)
- [使用示例](examples.md)

---

**OpenClaw Task Orchestrator - 让任务编排更智能，让协作更高效！** 🚀
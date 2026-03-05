# 执行模板 - OpenClaw原生工具版本

## 📋 概述

本文档提供基于OpenClaw原生工具的任务执行模板，用于标准化Task Orchestrator的工作流程。

## 🎯 核心执行流程

### 1. 任务接收与分析
```markdown
## 步骤1: 接收任务请求
- 解析用户任务描述
- 提取关键信息和约束条件
- 识别任务类型和领域

## 步骤2: 复杂度分析
基于以下维度进行AI判断：
- 技术难度：需要的专业知识深度
- 时间复杂度：预估完成时间
- 依赖关系：是否需要多个步骤或外部资源
- 创新程度：是否需要创造性思考

输出：L1/L2/L3复杂度等级
```

### 2. Agent选择与工单创建
```javascript
// 步骤3: 选择最适合的Agent
const selectedAgent = selectAgent({
  taskType: "技术架构设计",
  complexity: "L2", 
  requiredSkills: ["系统设计", "技术选型"],
  workload: "medium"
});

// 步骤4: 创建Bitable任务记录
const taskRecord = await feishu_bitable_create_record({
  app_token: "your_app_token",
  table_id: "your_table_id",
  fields: {
    "任务ID": `task-${Date.now()}`,
    "任务标题": taskTitle,
    "任务描述": taskDescription,
    "复杂度": complexity,
    "状态": "待处理",
    "优先级": priority,
    "分配Agent": selectedAgent,
    "创建时间": new Date().toISOString(),
    "进度百分比": 0
  }
});
```

### 3. 任务分配与通知
```javascript
// 步骤5: 发送任务分配通知
await message({
  action: "send",
  message: `🎯 任务分配通知
任务: ${taskTitle}
Agent: ${selectedAgent}
复杂度: ${complexity}
优先级: ${priority}
预估时间: ${estimatedTime}

任务详情: ${taskDescription}

请及时处理并更新进度。`,
  channel: "feishu",
  target: notificationChatId
});

// 步骤6: 异步调用Agent执行任务
await sessions_send({
  sessionKey: `agent-${selectedAgent}`,
  message: `请执行以下${complexity}任务：

任务标题: ${taskTitle}
任务描述: ${taskDescription}
任务ID: ${taskId}

请在完成后更新任务状态并提供结果文档。`
});
```

## 🔄 状态更新模板

### Agent执行中状态更新
```javascript
// Agent开始执行时
await feishu_bitable_update_record({
  app_token: "your_app_token",
  table_id: "your_table_id", 
  record_id: taskRecordId,
  fields: {
    "状态": "进行中",
    "更新时间": new Date().toISOString(),
    "进度百分比": 10
  }
});

// 进度更新通知
await message({
  action: "send",
  message: `📊 任务进度更新
任务: ${taskTitle}
状态: 进行中
进度: 10%
Agent: ${selectedAgent}`,
  channel: "feishu",
  target: notificationChatId
});
```

### 任务完成状态更新
```javascript
// Agent完成任务时
await feishu_bitable_update_record({
  app_token: "your_app_token",
  table_id: "your_table_id",
  record_id: taskRecordId,
  fields: {
    "状态": "已完成",
    "更新时间": new Date().toISOString(),
    "进度百分比": 100,
    "结果文档": resultDocumentUrl,
    "Token消耗": tokenUsage
  }
});

// 完成通知
await message({
  action: "send", 
  message: `✅ 任务完成通知
任务: ${taskTitle}
Agent: ${selectedAgent}
耗时: ${duration}
结果: ${resultSummary}

📄 结果文档: ${resultDocumentUrl}`,
  channel: "feishu",
  target: notificationChatId
});
```

## 🎨 Agent选择模板

### 基于任务类型的选择逻辑
```javascript
function selectAgent(taskInfo) {
  const { taskType, complexity, requiredSkills, domain } = taskInfo;
  
  // 技术架构类任务
  if (taskType.includes("架构") || taskType.includes("设计")) {
    return complexity === "L3" ? "architect" : "implementation-planner";
  }
  
  // 文档编写类任务
  if (taskType.includes("文档") || taskType.includes("说明")) {
    return "doc-engineer";
  }
  
  // 调研分析类任务
  if (taskType.includes("调研") || taskType.includes("分析")) {
    return "research-analyst";
  }
  
  // UI/UX设计类任务
  if (taskType.includes("界面") || taskType.includes("设计")) {
    return "ui-designer";
  }
  
  // 代码审查类任务
  if (taskType.includes("审查") || taskType.includes("重构")) {
    return "code-reviewer";
  }
  
  // 默认选择
  return complexity === "L3" ? "architect" : "task-orchestrator";
}
```

### Agent能力矩阵
```javascript
const AGENT_CAPABILITIES = {
  "architect": {
    skills: ["系统架构", "技术选型", "性能优化"],
    complexity: ["L2", "L3"],
    domains: ["后端", "基础设施", "微服务"]
  },
  "doc-engineer": {
    skills: ["技术文档", "API文档", "用户手册"],
    complexity: ["L1", "L2"],
    domains: ["文档", "知识管理", "飞书操作"]
  },
  "research-analyst": {
    skills: ["市场调研", "技术分析", "竞品分析"],
    complexity: ["L2", "L3"],
    domains: ["调研", "分析", "报告"]
  },
  "ui-designer": {
    skills: ["界面设计", "用户体验", "原型设计"],
    complexity: ["L1", "L2", "L3"],
    domains: ["前端", "设计", "用户体验"]
  }
};
```

## 📊 复杂度判断模板

### L1 (简单) 任务模板
```markdown
特征:
- 单一明确的操作
- 标准化流程
- 5-15分钟完成
- 无需深度思考

示例:
- 创建标准文档
- 简单配置修改
- 基础信息查询
- 常规格式转换

Agent选择: 通用Agent或专业Agent
```

### L2 (中等) 任务模板
```markdown
特征:
- 多步骤操作
- 需要一定分析判断
- 30分钟-2小时完成
- 涉及多个知识点

示例:
- 技术方案设计
- 复杂文档编写
- 系统集成配置
- 问题诊断分析

Agent选择: 专业领域Agent
```

### L3 (复杂) 任务模板
```markdown
特征:
- 需要深度分析
- 创新性解决方案
- 2小时以上完成
- 可能需要多轮迭代

示例:
- 架构重构设计
- 复杂算法实现
- 全新产品设计
- 深度技术调研

Agent选择: 高级专家Agent
```

## 🚨 异常处理模板

### 任务失败处理
```javascript
// 任务执行失败时
await feishu_bitable_update_record({
  app_token: "your_app_token",
  table_id: "your_table_id",
  record_id: taskRecordId,
  fields: {
    "状态": "失败",
    "更新时间": new Date().toISOString(),
    "任务描述": `${originalDescription}\n\n失败原因: ${errorReason}`
  }
});

// 失败通知和重试建议
await message({
  action: "send",
  message: `❌ 任务执行失败
任务: ${taskTitle}
Agent: ${selectedAgent}
失败原因: ${errorReason}

建议操作:
1. 检查任务描述是否清晰
2. 考虑降低复杂度或分解任务
3. 更换合适的Agent
4. 手动重试或寻求帮助`,
  channel: "feishu",
  target: notificationChatId
});
```

### 超时处理
```javascript
// 任务超时检查
function checkTaskTimeout(taskId, startTime, expectedDuration) {
  const currentTime = Date.now();
  const elapsed = currentTime - startTime;
  
  if (elapsed > expectedDuration * 1.5) {
    // 发送超时提醒
    message({
      action: "send",
      message: `⏰ 任务超时提醒
任务ID: ${taskId}
已用时: ${Math.round(elapsed / 60000)}分钟
预期时间: ${Math.round(expectedDuration / 60000)}分钟

请检查任务状态或考虑调整预期。`,
      channel: "feishu",
      target: notificationChatId
    });
  }
}
```

## 📈 性能监控模板

### Token使用统计
```javascript
// 记录Token消耗
await feishu_bitable_update_record({
  app_token: "your_app_token",
  table_id: "your_table_id",
  record_id: taskRecordId,
  fields: {
    "Token消耗": totalTokens,
    "成本估算": totalTokens * tokenPrice
  }
});
```

### 执行时间统计
```javascript
// 记录执行时间
const executionTime = endTime - startTime;
await feishu_bitable_update_record({
  app_token: "your_app_token", 
  table_id: "your_table_id",
  record_id: taskRecordId,
  fields: {
    "实际耗时": Math.round(executionTime / 60000), // 分钟
    "效率评分": calculateEfficiencyScore(executionTime, complexity)
  }
});
```

## 🔧 工具调用最佳实践

### 1. 错误处理
```javascript
try {
  const result = await feishu_bitable_create_record(params);
  return result;
} catch (error) {
  console.error("Bitable操作失败:", error);
  // 降级处理：记录到本地或发送简单通知
  await message({
    action: "send",
    message: `⚠️ 系统提醒：任务记录创建失败，请手动跟进任务: ${taskTitle}`,
    channel: "feishu"
  });
}
```

### 2. 批量操作
```javascript
// 批量更新多个任务状态
async function batchUpdateTasks(updates) {
  for (const update of updates) {
    try {
      await feishu_bitable_update_record(update);
      await new Promise(resolve => setTimeout(resolve, 100)); // 避免频率限制
    } catch (error) {
      console.error(`任务${update.record_id}更新失败:`, error);
    }
  }
}
```

### 3. 配置验证
```javascript
// 验证必要配置
function validateConfig() {
  const requiredFields = ["app_token", "table_id", "notification_chat_id"];
  const missingFields = requiredFields.filter(field => !config[field]);
  
  if (missingFields.length > 0) {
    throw new Error(`缺少必要配置: ${missingFields.join(", ")}`);
  }
}
```

---

**这些模板提供了使用OpenClaw原生工具的标准化执行流程，确保Task Orchestrator的可靠性和一致性！** 🚀
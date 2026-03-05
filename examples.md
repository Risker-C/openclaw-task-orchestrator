# 使用示例 - OpenClaw原生工具版本

## 📋 概述

本文档提供基于OpenClaw原生工具的Task Orchestrator使用示例，展示完整的任务编排流程。

## 🎯 基础使用示例

### 示例1: 简单文档创建任务 (L1)

**用户请求**:
```
请使用Task Orchestrator创建一份API接口文档，包含用户注册和登录接口的说明。
```

**执行流程**:

#### 1. 复杂度分析
```markdown
任务分析:
- 任务类型: 文档创建
- 技术难度: 低 (标准API文档格式)
- 时间复杂度: 15-30分钟
- 依赖关系: 无外部依赖
- 创新程度: 无需创新，标准化文档

复杂度判断: L1 (简单)
```

#### 2. Agent选择
```javascript
// 基于任务类型选择Agent
const selectedAgent = "doc-engineer"; // 文档工程师最适合
const taskId = `task-${Date.now()}`;
```

#### 3. 创建Bitable记录
```javascript
const taskRecord = await feishu_bitable_create_record({
  app_token: "bascnCMII2ORuAUfS8Gur5t",
  table_id: "tblxI2UvHxN5EV5c",
  fields: {
    "任务ID": taskId,
    "任务标题": "创建API接口文档",
    "任务描述": "创建用户注册和登录接口的API文档，包含请求参数、响应格式和错误码说明",
    "复杂度": "L1",
    "状态": "待处理",
    "优先级": "中",
    "分配Agent": "doc-engineer",
    "创建时间": new Date().toISOString(),
    "进度百分比": 0
  }
});
```

#### 4. 发送任务通知
```javascript
await message({
  action: "send",
  message: `🎯 任务分配通知
任务: 创建API接口文档
Agent: doc-engineer
复杂度: L1 (简单)
预估时间: 15-30分钟

任务详情: 创建用户注册和登录接口的API文档

请及时处理并更新进度。`,
  channel: "feishu",
  target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
});
```

#### 5. 调用Agent执行
```javascript
await sessions_send({
  sessionKey: "agent-doc-engineer",
  message: `请执行以下L1任务：

任务标题: 创建API接口文档
任务描述: 创建用户注册和登录接口的API文档，包含请求参数、响应格式和错误码说明
任务ID: ${taskId}

请创建完整的API文档，包含：
1. 用户注册接口 (/api/register)
2. 用户登录接口 (/api/login)
3. 请求参数说明
4. 响应格式定义
5. 错误码列表

完成后请更新任务状态。`
});
```

### 示例2: 技术架构设计任务 (L2)

**用户请求**:
```
请使用Task Orchestrator设计一个微服务架构，支持用户管理、订单处理和支付功能。
```

**执行流程**:

#### 1. 复杂度分析
```markdown
任务分析:
- 任务类型: 系统架构设计
- 技术难度: 中等 (需要微服务设计经验)
- 时间复杂度: 1-2小时
- 依赖关系: 需要考虑服务间通信、数据一致性
- 创新程度: 需要一定的设计思考

复杂度判断: L2 (中等)
```

#### 2. Agent选择与任务创建
```javascript
const selectedAgent = "architect"; // 架构师最适合
const taskId = `task-${Date.now()}`;

const taskRecord = await feishu_bitable_create_record({
  app_token: "bascnCMII2ORuAUfS8Gur5t",
  table_id: "tblxI2UvHxN5EV5c", 
  fields: {
    "任务ID": taskId,
    "任务标题": "微服务架构设计",
    "任务描述": "设计支持用户管理、订单处理和支付功能的微服务架构，包含服务拆分、通信方式、数据存储等",
    "复杂度": "L2",
    "状态": "待处理",
    "优先级": "高",
    "分配Agent": "architect",
    "创建时间": new Date().toISOString(),
    "进度百分比": 0
  }
});
```

#### 3. 执行过程中的状态更新
```javascript
// Agent开始执行
await feishu_bitable_update_record({
  app_token: "bascnCMII2ORuAUfS8Gur5t",
  table_id: "tblxI2UvHxN5EV5c",
  record_id: taskRecord.data.record.record_id,
  fields: {
    "状态": "进行中",
    "更新时间": new Date().toISOString(),
    "进度百分比": 25
  }
});

// 进度通知
await message({
  action: "send",
  message: `📊 任务进度更新
任务: 微服务架构设计
状态: 进行中 (25%)
Agent: architect

当前阶段: 服务拆分分析`,
  channel: "feishu",
  target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
});
```

#### 4. 任务完成
```javascript
// 任务完成更新
await feishu_bitable_update_record({
  app_token: "bascnCMII2ORuAUfS8Gur5t",
  table_id: "tblxI2UvHxN5EV5c",
  record_id: taskRecord.data.record.record_id,
  fields: {
    "状态": "已完成",
    "更新时间": new Date().toISOString(),
    "进度百分比": 100,
    "结果文档": "https://docs.example.com/microservice-architecture",
    "Token消耗": 1250
  }
});

// 完成通知
await message({
  action: "send",
  message: `✅ 任务完成通知
任务: 微服务架构设计
Agent: architect
耗时: 1.5小时
Token消耗: 1,250

📋 架构设计包含:
- 3个核心微服务 (用户、订单、支付)
- API网关设计
- 数据库分离策略
- 服务间通信方案
- 部署架构图

📄 详细文档: https://docs.example.com/microservice-architecture`,
  channel: "feishu",
  target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
});
```

### 示例3: 复杂技术调研任务 (L3)

**用户请求**:
```
请使用Task Orchestrator深度调研AI代码生成工具的技术发展趋势，包含市场分析、技术对比和未来预测。
```

**执行流程**:

#### 1. 复杂度分析
```markdown
任务分析:
- 任务类型: 深度技术调研
- 技术难度: 高 (需要多维度分析能力)
- 时间复杂度: 3-4小时
- 依赖关系: 需要大量外部信息收集
- 创新程度: 需要独到见解和预测

复杂度判断: L3 (复杂)
```

#### 2. 多Agent协作
```javascript
// 主任务创建
const mainTaskId = `task-${Date.now()}`;
await feishu_bitable_create_record({
  app_token: "bascnCMII2ORuAUfS8Gur5t",
  table_id: "tblxI2UvHxN5EV5c",
  fields: {
    "任务ID": mainTaskId,
    "任务标题": "AI代码生成工具深度调研",
    "任务描述": "深度调研AI代码生成工具的技术发展趋势，包含市场分析、技术对比和未来预测",
    "复杂度": "L3",
    "状态": "进行中",
    "优先级": "高",
    "分配Agent": "research-analyst",
    "创建时间": new Date().toISOString(),
    "进度百分比": 0
  }
});

// 分解为子任务
const subTasks = [
  {
    title: "市场现状分析",
    agent: "research-analyst",
    description: "分析当前AI代码生成工具的市场格局、主要玩家和用户采用情况"
  },
  {
    title: "技术对比评估", 
    agent: "architect",
    description: "对比主流工具的技术架构、能力特点和性能表现"
  },
  {
    title: "趋势预测报告",
    agent: "strategic-advisor", 
    description: "基于技术发展和市场数据，预测未来2-3年的发展趋势"
  }
];

// 创建子任务记录
for (const subTask of subTasks) {
  const subTaskId = `${mainTaskId}-${subTask.title}`;
  await feishu_bitable_create_record({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c",
    fields: {
      "任务ID": subTaskId,
      "任务标题": subTask.title,
      "任务描述": subTask.description,
      "复杂度": "L2",
      "状态": "待处理",
      "优先级": "高",
      "分配Agent": subTask.agent,
      "创建时间": new Date().toISOString(),
      "进度百分比": 0
    }
  });
}
```

#### 3. 并行执行管理
```javascript
// 启动并行子任务
for (const subTask of subTasks) {
  await sessions_send({
    sessionKey: `agent-${subTask.agent}`,
    message: `请执行以下L2子任务：

主任务: AI代码生成工具深度调研
子任务: ${subTask.title}
任务描述: ${subTask.description}
任务ID: ${mainTaskId}-${subTask.title}

这是L3复杂任务的一部分，请提供深度分析和专业见解。
完成后请更新任务状态并提供结果文档。`
  });
}

// 进度监控通知
await message({
  action: "send",
  message: `🚀 复杂任务启动
主任务: AI代码生成工具深度调研 (L3)
子任务数量: 3个
参与Agent: research-analyst, architect, strategic-advisor

预计完成时间: 3-4小时
当前状态: 并行执行中`,
  channel: "feishu",
  target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
});
```

## 🔄 状态管理示例

### 实时进度跟踪
```javascript
// 定期检查任务进度
async function checkTaskProgress(taskId) {
  const records = await feishu_bitable_list_records({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c"
  });
  
  const task = records.data.items.find(item => 
    item.fields["任务ID"] === taskId
  );
  
  if (task) {
    const progress = task.fields["进度百分比"] || 0;
    const status = task.fields["状态"];
    
    if (progress > 0 && progress < 100) {
      await message({
        action: "send",
        message: `📊 任务进度: ${task.fields["任务标题"]} - ${progress}% (${status})`,
        channel: "feishu",
        target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
      });
    }
  }
}
```

### 批量状态查询
```javascript
// 查询所有进行中的任务
async function getActiveTasks() {
  const records = await feishu_bitable_list_records({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c"
  });
  
  const activeTasks = records.data.items.filter(item => 
    ["待处理", "进行中"].includes(item.fields["状态"])
  );
  
  if (activeTasks.length > 0) {
    const taskList = activeTasks.map(task => 
      `- ${task.fields["任务标题"]} (${task.fields["状态"]}) - ${task.fields["分配Agent"]}`
    ).join("\n");
    
    await message({
      action: "send",
      message: `📋 当前活跃任务 (${activeTasks.length}个):
${taskList}`,
      channel: "feishu",
      target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
    });
  }
}
```

## 🚨 异常处理示例

### 任务超时处理
```javascript
// 检查超时任务
async function checkTimeoutTasks() {
  const records = await feishu_bitable_list_records({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c"
  });
  
  const now = new Date();
  const timeoutTasks = records.data.items.filter(item => {
    const createTime = new Date(item.fields["创建时间"]);
    const elapsed = now - createTime;
    const complexity = item.fields["复杂度"];
    const status = item.fields["状态"];
    
    // 根据复杂度设置超时阈值
    const timeoutThreshold = {
      "L1": 30 * 60 * 1000,  // 30分钟
      "L2": 3 * 60 * 60 * 1000,  // 3小时
      "L3": 6 * 60 * 60 * 1000   // 6小时
    };
    
    return status === "进行中" && elapsed > timeoutThreshold[complexity];
  });
  
  for (const task of timeoutTasks) {
    await message({
      action: "send",
      message: `⏰ 任务超时提醒
任务: ${task.fields["任务标题"]}
Agent: ${task.fields["分配Agent"]}
已用时: ${Math.round((now - new Date(task.fields["创建时间"])) / 60000)}分钟

请检查任务状态或考虑调整预期。`,
      channel: "feishu",
      target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
    });
  }
}
```

### 失败任务重试
```javascript
// 重试失败任务
async function retryFailedTask(taskId, newAgent = null) {
  const records = await feishu_bitable_list_records({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c"
  });
  
  const task = records.data.items.find(item => 
    item.fields["任务ID"] === taskId
  );
  
  if (task && task.fields["状态"] === "失败") {
    const retryAgent = newAgent || task.fields["分配Agent"];
    
    // 更新任务状态为重试
    await feishu_bitable_update_record({
      app_token: "bascnCMII2ORuAUfS8Gur5t",
      table_id: "tblxI2UvHxN5EV5c",
      record_id: task.record_id,
      fields: {
        "状态": "待处理",
        "分配Agent": retryAgent,
        "更新时间": new Date().toISOString(),
        "进度百分比": 0
      }
    });
    
    // 重新分配任务
    await sessions_send({
      sessionKey: `agent-${retryAgent}`,
      message: `请重试以下任务：

任务标题: ${task.fields["任务标题"]}
任务描述: ${task.fields["任务描述"]}
任务ID: ${taskId}
复杂度: ${task.fields["复杂度"]}

这是一个重试任务，请仔细分析之前的失败原因并采取相应措施。`
    });
    
    await message({
      action: "send",
      message: `🔄 任务重试
任务: ${task.fields["任务标题"]}
新Agent: ${retryAgent}
重试原因: 之前执行失败

已重新分配给Agent执行。`,
      channel: "feishu",
      target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
    });
  }
}
```

## 📊 性能监控示例

### 任务统计报告
```javascript
// 生成任务统计报告
async function generateTaskReport() {
  const records = await feishu_bitable_list_records({
    app_token: "bascnCMII2ORuAUfS8Gur5t",
    table_id: "tblxI2UvHxN5EV5c"
  });
  
  const tasks = records.data.items;
  const stats = {
    total: tasks.length,
    completed: tasks.filter(t => t.fields["状态"] === "已完成").length,
    inProgress: tasks.filter(t => t.fields["状态"] === "进行中").length,
    failed: tasks.filter(t => t.fields["状态"] === "失败").length,
    byComplexity: {
      L1: tasks.filter(t => t.fields["复杂度"] === "L1").length,
      L2: tasks.filter(t => t.fields["复杂度"] === "L2").length,
      L3: tasks.filter(t => t.fields["复杂度"] === "L3").length
    },
    totalTokens: tasks.reduce((sum, t) => sum + (t.fields["Token消耗"] || 0), 0)
  };
  
  await message({
    action: "send",
    message: `📊 Task Orchestrator 统计报告

总任务数: ${stats.total}
已完成: ${stats.completed} (${Math.round(stats.completed/stats.total*100)}%)
进行中: ${stats.inProgress}
失败: ${stats.failed}

按复杂度分布:
- L1 (简单): ${stats.byComplexity.L1}
- L2 (中等): ${stats.byComplexity.L2}  
- L3 (复杂): ${stats.byComplexity.L3}

总Token消耗: ${stats.totalTokens.toLocaleString()}`,
    channel: "feishu",
    target: "oc_ee8ba381032e7233b8f7cf25c9ccdb70"
  });
}
```

## 🎯 最佳实践示例

### 任务描述优化
```markdown
❌ 不好的任务描述:
"帮我做个网站"

✅ 好的任务描述:
"创建一个响应式的企业官网，包含首页、产品介绍、关于我们、联系方式四个页面。
技术要求: HTML5 + CSS3 + JavaScript，兼容主流浏览器。
设计风格: 简洁现代，主色调为蓝色。
交付物: 完整的前端代码和部署说明文档。"
```

### 复杂任务分解
```javascript
// 将复杂任务分解为多个子任务
function decomposeComplexTask(mainTask) {
  if (mainTask.complexity === "L3") {
    const subTasks = [];
    
    // 根据任务类型进行分解
    if (mainTask.type === "系统开发") {
      subTasks.push(
        { title: "需求分析", agent: "research-analyst", complexity: "L2" },
        { title: "架构设计", agent: "architect", complexity: "L2" },
        { title: "UI设计", agent: "ui-designer", complexity: "L2" },
        { title: "开发实现", agent: "code-reviewer", complexity: "L3" },
        { title: "测试部署", agent: "implementation-planner", complexity: "L2" }
      );
    }
    
    return subTasks;
  }
  
  return [mainTask]; // 简单任务不需要分解
}
```

---

**这些示例展示了如何使用OpenClaw原生工具实现完整的任务编排流程，确保系统的可靠性和可维护性！** 🚀
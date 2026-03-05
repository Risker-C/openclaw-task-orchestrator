# Phase 1 止血改造 - 实施指南

## 🎯 目标

解决OpenClaw Bug #21968导致的"假失败"问题：
- Sub-agent成功完成任务
- 但通知失败导致标记为"failed"
- 实际工作已完成但状态不正确

## 📋 核心改进

### 1. 状态解耦
- **执行状态**（execution_status）：任务实际执行结果
- **通知状态**（notification_status）：通知是否成功
- **最终状态**：由状态机裁决，执行状态优先级高于通知状态

### 2. 多信号裁决
- 信号源1：Sub-agent执行结果
- 信号源2：OpenClaw自动通知
- 信号源3：轮询会话状态（兜底）
- 裁决规则：completed > failed > timeout > notify_failed

### 3. 幂等更新
- 每次更新使用唯一的幂等键
- 防止重复更新导致状态抖动
- 保留7天更新历史

## 🔧 新增文件

### 1. `scripts/subagent-monitor-v2.js`
**功能**：增强的监控脚本
- 实现状态优先级判定
- 区分执行状态和通知状态
- 生成结构化通知

**关键函数**：
```javascript
resolveTaskStatus(tracked, sessionStatus)
// 输入：追踪状态 + 会话状态
// 输出：裁决结果（finalStatus, reason, shouldNotify）
```

### 2. `scripts/state-machine.js`
**功能**：状态机裁决器
- 定义状态优先级
- 实现状态转换规则
- 生成工单更新指令

**关键类**：
```javascript
class StateMachine {
  addEvent(event)           // 添加状态事件
  resolve(currentStatus)    // 裁决最终状态
  generateUpdateCommand()   // 生成更新指令
}
```

### 3. `scripts/ticket-updater.js`
**功能**：幂等工单更新器
- 执行Bitable更新
- 幂等性检查
- 更新历史记录

**关键类**：
```javascript
class TicketUpdater {
  isAlreadyExecuted(key)    // 幂等性检查
  executeUpdate(command)    // 执行更新
  batchUpdate(commands)     // 批量更新
}
```

## 📊 数据结构变更

### Tracker文件增强
```json
{
  "tracked_subagents": {
    "runId": {
      "execution_status": "completed",      // 新增：执行状态
      "notify_status": "failed",            // 新增：通知状态
      "notify_failed": true,                // 新增：通知失败标记
      "failure_reason": "...",              // 新增：失败原因
      "observability_alert": false          // 新增：观测告警
    }
  }
}
```

### 通知文件增强
```json
{
  "type": "completed",
  "execution_status": "completed",          // 新增：执行状态
  "notify_status": "failed",                // 新增：通知状态
  "reason": "任务执行成功（轮询确认）"
}
```

## 🚀 实施步骤

### Step 1: 部署新脚本（5分钟）
```bash
cd /root/.openclaw/workspace/openclaw-task-orchestrator

# 设置执行权限
chmod +x scripts/subagent-monitor-v2.js
chmod +x scripts/state-machine.js
chmod +x scripts/ticket-updater.js

# 测试状态机
node scripts/state-machine.js

# 测试更新器
node scripts/ticket-updater.js
```

### Step 2: 更新监控管理器（10分钟）
修改 `scripts/monitor-manager.sh`，使用新的监控脚本：
```bash
# 将 subagent-monitor.js 替换为 subagent-monitor-v2.js
/usr/bin/node /root/.openclaw/workspace/openclaw-task-orchestrator/scripts/subagent-monitor-v2.js
```

### Step 3: 集成状态机和更新器（15分钟）
创建集成脚本 `scripts/orchestrator-main.js`：
```javascript
const { StateMachine } = require('./state-machine.js');
const { TicketUpdater } = require('./ticket-updater.js');

// 读取通知 → 状态机裁决 → 幂等更新
```

### Step 4: 更新HEARTBEAT.md（5分钟）
修改heartbeat逻辑，使用新的处理流程：
```bash
# 检查通知
bash scripts/check-notifications.sh

# 如果有通知：
# 1. 读取通知内容
# 2. 调用状态机裁决
# 3. 执行幂等更新
# 4. 删除通知文件
```

### Step 5: 测试验证（30分钟）
```bash
# 创建测试任务
# 预期：即使OpenClaw标记failed，工单状态应为"已完成"

# 检查tracker文件
cat /root/.openclaw/workspace/subagent-tracker.json

# 检查更新历史
cat /root/.openclaw/workspace/ticket-update-history.json

# 验证工单状态
# 应该显示"已完成"而不是"已取消"
```

## ✅ 验收标准

### 1. 功能验收
- [ ] Sub-agent完成任务 + 通知失败 → 工单状态为"已完成"
- [ ] Sub-agent失败 → 工单状态为"已取消"
- [ ] Sub-agent超时 → 工单状态为"已取消"
- [ ] 重复通知 → 只更新一次（幂等性）

### 2. 性能验收
- [ ] 状态裁决延迟 < 5秒
- [ ] 工单更新延迟 < 10秒
- [ ] 无状态抖动（同一任务不会在完成/失败间反复切换）

### 3. 可观测性验收
- [ ] 通知失败时有明确日志
- [ ] 状态裁决过程可追踪
- [ ] 更新历史可查询

## 🐛 已知限制

### 1. 会话状态API未集成
当前版本的 `subagent-monitor-v2.js` 中，会话状态查询部分标记为 `TODO`：
```javascript
const sessionStatus = null; // 待集成API
```

**临时方案**：依赖超时检测和手动状态更新

**完整方案**：Phase 2 集成OpenClaw会话状态API

### 2. 事件存储未实现
当前版本使用内存状态，重启后丢失。

**临时方案**：依赖tracker文件持久化

**完整方案**：Phase 2 实现事件表存储

## 📈 后续计划

### Phase 2（2-4天）
- 集成OpenClaw会话状态API
- 实现事件表存储（Bitable或本地DB）
- 增加Reconciler定时任务

### Phase 3（2-3天）
- 实现Outbox重试队列
- 增加死信队列（DLQ）
- 完善监控指标和告警

## 🔗 相关文档

- [Bug #21968 解决方案](https://feishu.cn/wiki/IFXXdFwLFohBLDxMs7DcZiusnKb)
- [Task Orchestrator 系统说明](https://feishu.cn/wiki/QQaEdJ0JJoSA3GxdrKxcF3xfnyd)
- [时间记录改进方案](time-tracking-improvement.md)

---

**实施负责人**：Ikaros (伊卡洛斯)
**创建时间**：2026-03-05 23:26:00
**预计完成**：2026-03-06 (1-2天)

# Subagent监控系统

## 概述

Task Orchestrator集成了智能的subagent监控系统，能够第一时间发现subagent失败并自动处理，同时在没有任务时实现零资源消耗。

## 核心特性

- ✅ **按需启动** - 只在有活跃任务时运行监控
- ✅ **零token消耗** - 独立进程监控，不影响主Agent
- ✅ **实时通知** - 30秒内检测到状态变化
- ✅ **自动恢复** - 失败时自动更新工单状态并通知
- ✅ **智能停止** - 所有任务完成后自动停止监控

## 架构设计

```
启动subagent → 自动开启监控 → 检测状态变化 → 生成通知文件 → Heartbeat处理 → 更新工单
                                                                    ↓
                                              所有任务完成 ← 自动停止监控
```

## 脚本说明

### 1. subagent-monitor.js
- **功能**: 核心监控脚本，检测subagent状态变化
- **运行方式**: 后台独立进程
- **输出**: 生成通知文件 `/tmp/subagent-notifications.json`

### 2. monitor-manager.sh
- **功能**: 监控生命周期管理
- **命令**: 
  - `start` - 启动监控
  - `stop` - 停止监控  
  - `status` - 查看状态

### 3. check-notifications.sh
- **功能**: 轻量级通知检查（供Heartbeat使用）
- **特点**: 只读文件，几乎不消耗token

### 4. task-orchestrator-helpers.sh
- **功能**: Task Orchestrator辅助函数
- **用途**: 启动任务时自动管理监控

## 使用方法

### 启动任务时
```bash
# 自动启动监控
bash scripts/monitor-manager.sh start

# 然后启动subagent
sessions_spawn(...)
```

### 检查状态
```bash
# 查看监控状态
bash scripts/monitor-manager.sh status

# 检查通知
bash scripts/check-notifications.sh
```

### Heartbeat集成
在 `HEARTBEAT.md` 中已集成监控检查：
```bash
bash scripts/check-notifications.sh
```

## 文件结构

```
scripts/
├── subagent-monitor.js          # 核心监控脚本
├── monitor-manager.sh           # 监控管理器
├── check-notifications.sh       # 通知检查器
└── task-orchestrator-helpers.sh # 辅助函数
```

## 状态文件

- **追踪文件**: `subagent-tracker.json` - 记录所有subagent状态
- **通知文件**: `/tmp/subagent-notifications.json` - 临时通知文件
- **PID文件**: `/tmp/subagent-monitor.pid` - 监控进程PID

## 通知格式

```json
[
  {
    "type": "failure",
    "runId": "xxx",
    "workOrderId": "TASK-xxx",
    "recordId": "recxxx",
    "agent": "architect",
    "timestamp": 1772719200000
  }
]
```

## 资源消耗

- **没有任务时**: 0 CPU, 0 内存
- **有任务时**: 极低CPU（30秒检查一次）
- **Token消耗**: 几乎为0（只读文件）

## 故障排除

### 监控未启动
```bash
bash scripts/monitor-manager.sh start
```

### 监控进程卡死
```bash
bash scripts/monitor-manager.sh stop
bash scripts/monitor-manager.sh start
```

### 通知文件积累
```bash
rm -f /tmp/subagent-notifications.json
```
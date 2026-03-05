#!/bin/bash

# Task Orchestrator 辅助函数
# 在启动subagent时自动管理监控

function start_task_with_monitoring() {
  local agent_id=$1
  local task_description=$2
  local work_order_id=$3
  local record_id=$4
  
  echo "Starting task: $work_order_id"
  echo "Agent: $agent_id"
  
  # 启动监控（如果尚未运行）
  bash /root/.openclaw/workspace/monitor-manager.sh start
  
  # 返回成功，让主Agent继续启动subagent
  echo "Monitor started, ready to spawn subagent"
}

function check_task_status() {
  # 检查是否有通知
  if [ -f "/tmp/subagent-notifications.json" ]; then
    cat /tmp/subagent-notifications.json
    return 1  # 有通知需要处理
  else
    echo "No notifications"
    return 0
  fi
}

# 导出函数供其他脚本使用
export -f start_task_with_monitoring
export -f check_task_status
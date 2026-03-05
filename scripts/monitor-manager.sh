#!/bin/bash

# 动态监控管理脚本
# 根据是否有活跃任务来启停监控

MONITOR_PID_FILE="/tmp/subagent-monitor.pid"
TRACKER_FILE="/root/.openclaw/workspace/subagent-tracker.json"

function start_monitor() {
  if [ -f "$MONITOR_PID_FILE" ]; then
    echo "Monitor already running (PID: $(cat $MONITOR_PID_FILE))"
    return
  fi
  
  echo "Starting subagent monitor..."
  
  # 启动后台监控进程
  (
    while true; do
      /usr/bin/node /root/.openclaw/workspace/subagent-monitor.js
      
      # 检查是否还有活跃任务
      if [ -f "$TRACKER_FILE" ]; then
        active_count=$(jq '.tracked_subagents | to_entries | map(select(.value.status == "running" or .value.status == "active")) | length' "$TRACKER_FILE" 2>/dev/null || echo "0")
        
        if [ "$active_count" -eq 0 ]; then
          echo "No active tasks, stopping monitor"
          break
        fi
      fi
      
      sleep 30  # 30秒检查一次
    done
    
    # 清理PID文件
    rm -f "$MONITOR_PID_FILE"
  ) &
  
  # 记录PID
  echo $! > "$MONITOR_PID_FILE"
  echo "Monitor started with PID: $!"
}

function stop_monitor() {
  if [ -f "$MONITOR_PID_FILE" ]; then
    PID=$(cat "$MONITOR_PID_FILE")
    kill "$PID" 2>/dev/null
    rm -f "$MONITOR_PID_FILE"
    echo "Monitor stopped (PID: $PID)"
  else
    echo "Monitor not running"
  fi
}

function status_monitor() {
  if [ -f "$MONITOR_PID_FILE" ]; then
    PID=$(cat "$MONITOR_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      echo "Monitor running (PID: $PID)"
    else
      echo "Monitor PID file exists but process not running"
      rm -f "$MONITOR_PID_FILE"
    fi
  else
    echo "Monitor not running"
  fi
}

case "$1" in
  start)
    start_monitor
    ;;
  stop)
    stop_monitor
    ;;
  status)
    status_monitor
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
esac
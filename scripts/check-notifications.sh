#!/bin/bash

# 轻量级通知检查脚本 - 增强版
# 支持精确时间记录和Bitable字段更新

NOTIFICATION_FILE="/tmp/subagent-notifications.json"

if [ -f "$NOTIFICATION_FILE" ]; then
  # 有新通知，读取并处理
  echo "🔔 检测到subagent状态变化通知："
  cat "$NOTIFICATION_FILE"
  
  # 处理完后删除通知文件
  rm "$NOTIFICATION_FILE"
  
  exit 1  # 返回非0表示有通知需要处理
else
  # 没有通知
  echo "HEARTBEAT_OK"
  exit 0
fi
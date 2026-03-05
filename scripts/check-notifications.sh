#!/bin/bash

# 轻量级通知检查脚本
# 只检查通知文件，不调用任何API

NOTIFICATION_FILE="/tmp/subagent-notifications.json"

if [ -f "$NOTIFICATION_FILE" ]; then
  # 有新通知，读取并处理
  cat "$NOTIFICATION_FILE"
  
  # 处理完后删除通知文件
  rm "$NOTIFICATION_FILE"
  
  exit 1  # 返回非0表示有通知需要处理
else
  # 没有通知
  echo "HEARTBEAT_OK"
  exit 0
fi
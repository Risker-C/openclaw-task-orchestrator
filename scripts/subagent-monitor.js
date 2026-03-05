#!/usr/bin/env node

/**
 * Subagent Monitor - 按需监控脚本
 * 只在有活跃任务时运行，不消耗主Agent token
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const TRACKER_FILE = '/root/.openclaw/workspace/subagent-tracker.json';
const NOTIFICATION_FILE = '/tmp/subagent-notifications.json';

// 时间格式化函数
function formatDateTime(timestamp) {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// 计算任务时长
function calculateDuration(startTime, endTime) {
  const durationMs = endTime - startTime;
  const seconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`;
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`;
  } else {
    return `${seconds}秒`;
  }
}

async function checkSubagents() {
  try {
    // 读取当前追踪状态
    if (!fs.existsSync(TRACKER_FILE)) {
      console.log('Tracker file not found, creating empty tracker');
      const emptyTracker = {
        tracked_subagents: {},
        last_check: null,
        failed_history: []
      };
      fs.writeFileSync(TRACKER_FILE, JSON.stringify(emptyTracker, null, 2));
      return;
    }
    
    const tracker = JSON.parse(fs.readFileSync(TRACKER_FILE, 'utf8'));
    
    // 检查是否有需要追踪的subagent
    if (Object.keys(tracker.tracked_subagents).length === 0) {
      console.log('No subagents to track');
      return;
    }
    
    const notifications = [];
    const currentTime = Date.now();
    
    // 检查每个追踪的subagent
    for (const [runId, tracked] of Object.entries(tracker.tracked_subagents)) {
      // 检查是否超时（默认30分钟超时）
      const timeoutMs = 30 * 60 * 1000; // 30分钟
      const elapsedTime = currentTime - tracked.startedAt;
      
      if (tracked.status === 'running' && elapsedTime > timeoutMs) {
        // 任务超时
        const endTime = currentTime;
        const duration = calculateDuration(tracked.startedAt, endTime);
        
        notifications.push({
          type: 'timeout',
          runId: runId,
          workOrderId: tracked.workOrderId,
          recordId: tracked.recordId,
          agent: tracked.agent,
          timestamp: endTime,
          startTime: tracked.startedAt,
          endTime: endTime,
          duration: duration,
          reason: `任务执行超时（${duration}），超过最大允许时间30分钟`
        });
        
        // 更新状态为超时
        tracker.tracked_subagents[runId].status = 'timeout';
        tracker.tracked_subagents[runId].endedAt = endTime;
        tracker.tracked_subagents[runId].endedAtReadable = formatDateTime(endTime);
        tracker.tracked_subagents[runId].duration = duration;
        tracker.tracked_subagents[runId].failureNotified = true;
        
        // 添加到失败历史
        tracker.failed_history.push({
          runId: runId,
          workOrderId: tracked.workOrderId,
          agent: tracked.agent,
          failedAt: endTime,
          detectedAt: currentTime,
          reason: 'timeout',
          duration: duration
        });
        
        console.log(`Detected timeout for subagent: ${runId}, duration: ${duration}`);
      }
      
      // 这里可以添加其他状态检查逻辑
      // 例如通过API检查实际的subagent状态
    }
    
    // 保存通知
    if (notifications.length > 0) {
      fs.writeFileSync(NOTIFICATION_FILE, JSON.stringify(notifications, null, 2));
      console.log(`Generated ${notifications.length} notifications`);
    }
    
    // 更新追踪文件
    tracker.last_check = currentTime;
    tracker.last_check_readable = formatDateTime(currentTime);
    fs.writeFileSync(TRACKER_FILE, JSON.stringify(tracker, null, 2));
    
  } catch (error) {
    console.error('Monitor error:', error);
  }
}

// 执行检查
checkSubagents();
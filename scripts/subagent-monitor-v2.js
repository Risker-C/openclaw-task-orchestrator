#!/usr/bin/env node

/**
 * Subagent Monitor - Phase 1 止血改造
 * 核心改进：
 * 1. 增加notify_failed独立字段
 * 2. 实现多信号裁决逻辑
 * 3. 状态优先级：completed > notify_failed
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

// 状态优先级判定（核心改进）
function resolveTaskStatus(tracked, sessionStatus) {
  /**
   * 状态优先级规则：
   * 1. execution_completed > notify_failed
   * 2. execution_failed > notify_failed
   * 3. timeout > running
   * 4. notify_failed 仅作为观测信号，不改变业务状态
   */
  
  // 如果已有明确的执行状态，优先使用
  if (tracked.execution_status === 'completed') {
    return {
      finalStatus: 'completed',
      reason: '任务执行成功（已确认）',
      shouldNotify: false
    };
  }
  
  if (tracked.execution_status === 'failed') {
    return {
      finalStatus: 'failed',
      reason: tracked.failure_reason || '任务执行失败',
      shouldNotify: false
    };
  }
  
  // 检查会话状态（轮询获取）
  if (sessionStatus) {
    if (sessionStatus.status === 'completed') {
      return {
        finalStatus: 'completed',
        reason: '任务执行成功（轮询确认）',
        shouldNotify: true,
        updateExecution: true
      };
    }
    
    if (sessionStatus.status === 'failed') {
      return {
        finalStatus: 'failed',
        reason: sessionStatus.error || '任务执行失败（轮询确认）',
        shouldNotify: true,
        updateExecution: true
      };
    }
  }
  
  // 检查超时
  const currentTime = Date.now();
  const timeoutMs = tracked.timeoutThreshold || (30 * 60 * 1000); // 默认30分钟
  const elapsedTime = currentTime - tracked.startedAt;
  
  if (tracked.status === 'running' && elapsedTime > timeoutMs) {
    return {
      finalStatus: 'timeout',
      reason: `任务执行超时（${calculateDuration(tracked.startedAt, currentTime)}）`,
      shouldNotify: true,
      updateExecution: true
    };
  }
  
  // 如果有notify_failed但没有执行状态，标记为观测告警
  if (tracked.notify_failed && !tracked.execution_status) {
    return {
      finalStatus: 'running',
      reason: '通知失败但任务可能仍在执行',
      shouldNotify: false,
      observability_alert: true
    };
  }
  
  return {
    finalStatus: tracked.status || 'running',
    reason: '任务正常运行中',
    shouldNotify: false
  };
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
      // TODO: 这里应该调用OpenClaw API获取会话状态
      // 暂时使用本地状态判定
      const sessionStatus = null; // 待集成API
      
      // 使用状态优先级判定
      const resolution = resolveTaskStatus(tracked, sessionStatus);
      
      if (resolution.shouldNotify) {
        const endTime = currentTime;
        const duration = calculateDuration(tracked.startedAt, endTime);
        
        notifications.push({
          type: resolution.finalStatus,
          runId: runId,
          workOrderId: tracked.workOrderId,
          recordId: tracked.recordId,
          agent: tracked.agent,
          timestamp: endTime,
          startTime: tracked.startedAt,
          endTime: endTime,
          duration: duration,
          reason: resolution.reason,
          execution_status: resolution.finalStatus,
          notify_status: tracked.notify_failed ? 'failed' : 'unknown'
        });
        
        // 更新tracker状态
        if (resolution.updateExecution) {
          tracker.tracked_subagents[runId].execution_status = resolution.finalStatus;
          tracker.tracked_subagents[runId].endedAt = endTime;
          tracker.tracked_subagents[runId].endedAtReadable = formatDateTime(endTime);
          tracker.tracked_subagents[runId].duration = duration;
          tracker.tracked_subagents[runId].failure_reason = resolution.reason;
        }
        
        console.log(`Status resolved for ${runId}: ${resolution.finalStatus} (${resolution.reason})`);
      }
      
      // 记录观测告警
      if (resolution.observability_alert) {
        console.warn(`⚠️ Observability alert for ${runId}: notify failed but execution status unknown`);
      }
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
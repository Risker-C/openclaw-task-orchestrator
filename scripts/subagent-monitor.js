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

async function checkSubagents() {
  try {
    // 读取当前追踪状态
    const tracker = JSON.parse(fs.readFileSync(TRACKER_FILE, 'utf8'));
    
    // 调用OpenClaw API检查subagent状态
    exec('openclaw sessions list --format json', (error, stdout, stderr) => {
      if (error) {
        console.error('Failed to check subagents:', error);
        return;
      }
      
      const sessions = JSON.parse(stdout);
      const notifications = [];
      
      // 检查每个追踪的subagent
      for (const [runId, tracked] of Object.entries(tracker.tracked_subagents)) {
        const current = sessions.find(s => s.runId === runId);
        
        if (current && current.status !== tracked.status) {
          // 状态发生变化
          if (current.status === 'failed' && !tracked.failureNotified) {
            notifications.push({
              type: 'failure',
              runId: runId,
              workOrderId: tracked.workOrderId,
              recordId: tracked.recordId,
              agent: tracked.sessionKey.split(':')[1],
              timestamp: Date.now()
            });
            
            // 标记为已通知
            tracker.tracked_subagents[runId].failureNotified = true;
          }
          
          if (current.status === 'done' && tracked.status !== 'done') {
            notifications.push({
              type: 'completion',
              runId: runId,
              workOrderId: tracked.workOrderId,
              recordId: tracked.recordId,
              agent: tracked.sessionKey.split(':')[1],
              timestamp: Date.now()
            });
          }
          
          // 更新状态
          tracker.tracked_subagents[runId].status = current.status;
        }
      }
      
      // 保存通知
      if (notifications.length > 0) {
        fs.writeFileSync(NOTIFICATION_FILE, JSON.stringify(notifications, null, 2));
        console.log(`Generated ${notifications.length} notifications`);
      }
      
      // 更新追踪文件
      tracker.last_check = Date.now();
      fs.writeFileSync(TRACKER_FILE, JSON.stringify(tracker, null, 2));
      
    });
    
  } catch (error) {
    console.error('Monitor error:', error);
  }
}

// 执行检查
checkSubagents();
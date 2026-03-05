#!/usr/bin/env node

/**
 * State Machine - 任务状态裁决器
 * 
 * 核心职责：
 * 1. 接收多个信号源（执行状态、通知状态、轮询状态）
 * 2. 按优先级规则裁决最终状态
 * 3. 生成幂等的状态更新指令
 */

const fs = require('fs');

// 状态优先级定义
const STATUS_PRIORITY = {
  'completed': 100,      // 最高优先级：任务完成
  'failed': 90,          // 次高优先级：任务失败
  'timeout': 85,         // 超时失败
  'cancelled': 80,       // 用户取消
  'running': 50,         // 运行中
  'pending': 30,         // 等待中
  'notify_failed': 10    // 最低优先级：仅通知失败
};

// 状态转换规则
const STATE_TRANSITIONS = {
  'pending': ['running', 'cancelled'],
  'running': ['completed', 'failed', 'timeout', 'cancelled'],
  'completed': [],  // 终态，不可转换
  'failed': [],     // 终态，不可转换
  'timeout': [],    // 终态，不可转换
  'cancelled': []   // 终态，不可转换
};

class StateMachine {
  constructor() {
    this.events = [];
  }
  
  /**
   * 添加状态事件
   * @param {Object} event - 状态事件
   * @param {string} event.source - 事件来源（execution/notification/polling）
   * @param {string} event.status - 状态值
   * @param {number} event.timestamp - 时间戳
   * @param {string} event.reason - 原因说明
   */
  addEvent(event) {
    this.events.push({
      ...event,
      priority: STATUS_PRIORITY[event.status] || 0
    });
  }
  
  /**
   * 裁决最终状态
   * @param {string} currentStatus - 当前状态
   * @returns {Object} 裁决结果
   */
  resolve(currentStatus) {
    if (this.events.length === 0) {
      return {
        finalStatus: currentStatus,
        changed: false,
        reason: '无新事件'
      };
    }
    
    // 按优先级和时间戳排序
    const sortedEvents = this.events.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority; // 优先级高的在前
      }
      return b.timestamp - a.timestamp; // 时间新的在前
    });
    
    const highestPriorityEvent = sortedEvents[0];
    
    // 检查状态转换是否合法
    if (currentStatus && STATE_TRANSITIONS[currentStatus]) {
      const allowedTransitions = STATE_TRANSITIONS[currentStatus];
      
      // 如果当前是终态，不允许转换
      if (allowedTransitions.length === 0) {
        return {
          finalStatus: currentStatus,
          changed: false,
          reason: `当前状态${currentStatus}为终态，不可转换`,
          rejectedEvent: highestPriorityEvent
        };
      }
      
      // 检查是否允许转换到目标状态
      if (!allowedTransitions.includes(highestPriorityEvent.status)) {
        return {
          finalStatus: currentStatus,
          changed: false,
          reason: `不允许从${currentStatus}转换到${highestPriorityEvent.status}`,
          rejectedEvent: highestPriorityEvent
        };
      }
    }
    
    // 执行状态转换
    return {
      finalStatus: highestPriorityEvent.status,
      changed: highestPriorityEvent.status !== currentStatus,
      reason: highestPriorityEvent.reason,
      source: highestPriorityEvent.source,
      timestamp: highestPriorityEvent.timestamp,
      allEvents: sortedEvents
    };
  }
  
  /**
   * 生成工单更新指令
   * @param {Object} resolution - 裁决结果
   * @param {Object} taskInfo - 任务信息
   * @returns {Object} 更新指令
   */
  generateUpdateCommand(resolution, taskInfo) {
    if (!resolution.changed) {
      return null; // 无需更新
    }
    
    const statusMap = {
      'completed': '已完成',
      'failed': '已取消',
      'timeout': '已取消',
      'cancelled': '已取消',
      'running': '处理中',
      'pending': '待处理'
    };
    
    const progressMap = {
      'completed': 100,
      'failed': 0,
      'timeout': 0,
      'cancelled': 0,
      'running': 50,
      'pending': 0
    };
    
    return {
      app_token: taskInfo.app_token,
      table_id: taskInfo.table_id,
      record_id: taskInfo.record_id,
      fields: {
        '状态': statusMap[resolution.finalStatus] || '处理中',
        '进度百分比': progressMap[resolution.finalStatus] || 0,
        '完成时间': resolution.timestamp,
        '任务时长': taskInfo.duration,
        '失败原因': resolution.finalStatus === 'completed' ? null : resolution.reason
      },
      idempotency_key: `${taskInfo.workOrderId}_${resolution.finalStatus}_${resolution.timestamp}`
    };
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { StateMachine, STATUS_PRIORITY, STATE_TRANSITIONS };
}

// CLI测试
if (require.main === module) {
  const sm = new StateMachine();
  
  // 测试场景1：执行完成 + 通知失败
  console.log('\n=== 测试场景1：执行完成 + 通知失败 ===');
  sm.addEvent({
    source: 'execution',
    status: 'completed',
    timestamp: Date.now(),
    reason: '任务执行成功'
  });
  sm.addEvent({
    source: 'notification',
    status: 'notify_failed',
    timestamp: Date.now() + 1000,
    reason: 'unsupported channel: feishu'
  });
  
  const result1 = sm.resolve('running');
  console.log('裁决结果:', result1);
  console.log('预期：completed（执行状态优先级高于通知状态）');
  
  // 测试场景2：尝试修改终态
  console.log('\n=== 测试场景2：尝试修改终态 ===');
  const sm2 = new StateMachine();
  sm2.addEvent({
    source: 'polling',
    status: 'failed',
    timestamp: Date.now(),
    reason: '轮询发现失败'
  });
  
  const result2 = sm2.resolve('completed');
  console.log('裁决结果:', result2);
  console.log('预期：completed（终态不可转换）');
}
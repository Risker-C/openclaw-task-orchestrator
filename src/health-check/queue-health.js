/**
 * 任务队列健康检查 - 检查任务队列的状态
 * 轻量级设计，通过追踪文件检查队列状态
 */

const fs = require('fs');
const { paths } = require('../config/paths');

class QueueHealth {
  constructor(options = {}) {
    // 配置
    this.config = {
      trackerFile: options.trackerFile || paths.trackerFile,
      maxQueueSize: options.maxQueueSize || 1000,
      maxWaitTimeMs: options.maxWaitTimeMs || 10 * 60 * 1000, // 10分钟
      warningQueueSize: options.warningQueueSize || 500
    };

    // 队列历史（用于计算吞吐量）
    this.history = [];
    this.maxHistorySize = 10;
  }

  /**
   * 加载队列数据
   */
  loadQueueData() {
    try {
      if (fs.existsSync(this.config.trackerFile)) {
        const data = fs.readFileSync(this.config.trackerFile, 'utf8');
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('Failed to load queue data:', error);
    }
    return null;
  }

  /**
   * 兼容字段：获取创建时间
   */
  getCreatedAt(agent) {
    return agent.createdAt || agent.startedAt || agent.lastChecked || Date.now();
  }

  /**
   * 检查队列健康状态
   */
  checkQueueHealth() {
    const tracker = this.loadQueueData();
    if (!tracker || !tracker.tracked_subagents) {
      return {
        healthy: true,
        queueSize: 0,
        runningTasks: 0,
        pendingTasks: 0,
        completedTasks: 0,
        failedTasks: 0,
        issues: [],
        timestamp: Date.now()
      };
    }

    const agents = tracker.tracked_subagents;
    const now = Date.now();
    const issues = [];

    // 统计队列中的任务
    let queueSize = 0;
    let runningTasks = 0;
    let pendingTasks = 0;
    let completedTasks = 0;
    let failedTasks = 0;
    let oldestPendingTime = null;

    for (const agent of Object.values(agents)) {
      if (agent.status === 'running') {
        runningTasks += 1;
        queueSize += 1;
      } else if (agent.status === 'pending') {
        pendingTasks += 1;
        queueSize += 1;

        // 记录最老的待处理任务时间
        const createdAt = this.getCreatedAt(agent);
        if (!oldestPendingTime || createdAt < oldestPendingTime) {
          oldestPendingTime = createdAt;
        }
      } else if (agent.status === 'completed') {
        completedTasks += 1;
      } else if (agent.status === 'failed' || agent.status === 'timeout') {
        failedTasks += 1;
      }
    }

    // 检查队列大小
    if (queueSize > this.config.maxQueueSize) {
      issues.push({
        type: 'queue_overflow',
        level: 'critical',
        message: `队列溢出: ${queueSize} > ${this.config.maxQueueSize}`
      });
    } else if (queueSize > this.config.warningQueueSize) {
      issues.push({
        type: 'queue_overflow',
        level: 'warning',
        message: `队列接近满: ${queueSize} > ${this.config.warningQueueSize}`
      });
    }

    // 检查待处理任务等待时间
    if (oldestPendingTime) {
      const waitTime = now - oldestPendingTime;
      if (waitTime > this.config.maxWaitTimeMs) {
        issues.push({
          type: 'long_wait',
          level: 'warning',
          message: `任务等待时间过长: ${Math.round(waitTime / 1000 / 60)}分钟`
        });
      }
    }

    // 记录历史
    this.history.push({
      queueSize,
      runningTasks,
      pendingTasks,
      timestamp: now
    });

    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }

    return {
      healthy: issues.length === 0,
      queueSize,
      runningTasks,
      pendingTasks,
      completedTasks,
      failedTasks,
      issues,
      timestamp: now
    };
  }

  /**
   * 获取队列吞吐量
   */
  getQueueThroughput() {
    if (this.history.length < 2) {
      return {
        tasksPerMinute: 0,
        averageQueueSize: 0
      };
    }

    const firstRecord = this.history[0];
    const lastRecord = this.history[this.history.length - 1];

    const timeElapsedMs = lastRecord.timestamp - firstRecord.timestamp;
    const timeElapsedMinutes = timeElapsedMs / 1000 / 60;

    // 计算平均队列大小
    const avgQueueSize = Math.round(
      this.history.reduce((sum, r) => sum + r.queueSize, 0) / this.history.length
    );

    // 计算任务处理速度（完成的任务数 / 时间）
    const tasksProcessed = firstRecord.runningTasks - lastRecord.runningTasks;
    const tasksPerMinute = timeElapsedMinutes > 0 ? Math.round(tasksProcessed / timeElapsedMinutes) : 0;

    return {
      tasksPerMinute: Math.max(0, tasksPerMinute),
      averageQueueSize: avgQueueSize,
      timeElapsedMinutes: Math.round(timeElapsedMinutes * 100) / 100
    };
  }

  /**
   * 获取队列统计
   */
  getQueueStats() {
    const tracker = this.loadQueueData();
    if (!tracker || !tracker.tracked_subagents) {
      return {
        total: 0,
        running: 0,
        pending: 0,
        completed: 0,
        failed: 0
      };
    }

    const agents = tracker.tracked_subagents;
    const stats = {
      total: Object.keys(agents).length,
      running: 0,
      pending: 0,
      completed: 0,
      failed: 0
    };

    for (const agent of Object.values(agents)) {
      if (agent.status === 'running') {
        stats.running += 1;
      } else if (agent.status === 'pending') {
        stats.pending += 1;
      } else if (agent.status === 'completed') {
        stats.completed += 1;
      } else if (agent.status === 'failed' || agent.status === 'timeout') {
        stats.failed += 1;
      }
    }

    return stats;
  }

  /**
   * 获取长时间待处理的任务
   */
  getLongWaitingTasks(thresholdMs = null) {
    const threshold = thresholdMs || this.config.maxWaitTimeMs;
    const tracker = this.loadQueueData();
    if (!tracker || !tracker.tracked_subagents) {
      return [];
    }

    const agents = tracker.tracked_subagents;
    const now = Date.now();
    const longWaitingTasks = [];

    for (const [agentId, agentData] of Object.entries(agents)) {
      if (agentData.status === 'pending') {
        const createdAt = this.getCreatedAt(agentData);
        const waitTime = now - createdAt;
        if (waitTime > threshold) {
          longWaitingTasks.push({
            agentId,
            waitTimeMs: waitTime,
            waitTimeMinutes: Math.round(waitTime / 1000 / 60),
            workOrderId: agentData.workOrderId
          });
        }
      }
    }

    return longWaitingTasks.sort((a, b) => b.waitTimeMs - a.waitTimeMs);
  }
}

module.exports = QueueHealth;

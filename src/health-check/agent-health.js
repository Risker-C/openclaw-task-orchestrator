/**
 * Agent健康检查 - 检查Agent的运行状态
 * 轻量级设计，通过追踪文件检查Agent状态
 */

const fs = require('fs');
const { paths } = require('../config/paths');

class AgentHealth {
  constructor(options = {}) {
    // 配置
    this.config = {
      trackerFile: options.trackerFile || paths.trackerFile,
      agentTimeoutMs: options.agentTimeoutMs || 30 * 60 * 1000, // 30分钟
      maxFailureCount: options.maxFailureCount || 5
    };
  }

  /**
   * 加载Agent追踪信息
   */
  loadTrackerData() {
    try {
      if (fs.existsSync(this.config.trackerFile)) {
        const data = fs.readFileSync(this.config.trackerFile, 'utf8');
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('Failed to load tracker data:', error);
    }
    return null;
  }

  /**
   * 获取任务开始时间戳（兼容不同字段）
   */
  getStartedAt(trackedAgent) {
    return trackedAgent.startedAt || trackedAgent.createdAt || trackedAgent.lastChecked || 0;
  }

  /**
   * 检查单个Agent的健康状态
   */
  checkAgentHealth(agentId, trackedAgent) {
    const now = Date.now();
    const issues = [];

    if (!trackedAgent) {
      return {
        agentId,
        healthy: false,
        status: 'unknown',
        issues: ['Agent信息不存在']
      };
    }

    // 检查Agent状态
    if (trackedAgent.status === 'failed') {
      issues.push('Agent执行失败');
    }

    if (trackedAgent.status === 'timeout') {
      issues.push('Agent执行超时');
    }

    // 检查是否超时
    if (trackedAgent.status === 'running') {
      const elapsedTime = now - this.getStartedAt(trackedAgent);
      if (elapsedTime > this.config.agentTimeoutMs) {
        issues.push(`Agent运行超时（${Math.round(elapsedTime / 1000 / 60)}分钟）`);
      }
    }

    // 检查失败次数
    if (trackedAgent.failureCount && trackedAgent.failureCount > this.config.maxFailureCount) {
      issues.push(`Agent失败次数过多（${trackedAgent.failureCount}次）`);
    }

    return {
      agentId,
      healthy: issues.length === 0,
      status: trackedAgent.status || 'unknown',
      issues,
      failureCount: trackedAgent.failureCount || 0,
      lastUpdate: trackedAgent.endedAt || this.getStartedAt(trackedAgent),
      workOrderId: trackedAgent.workOrderId || null
    };
  }

  /**
   * 检查所有Agent的健康状态
   */
  checkAllAgentsHealth() {
    const tracker = this.loadTrackerData();
    if (!tracker || !tracker.tracked_subagents) {
      return {
        healthy: true,
        totalAgents: 0,
        healthyAgents: 0,
        unhealthyAgents: 0,
        agents: [],
        issues: []
      };
    }

    const agents = tracker.tracked_subagents;
    const agentHealths = [];
    const issues = [];
    let healthyCount = 0;

    for (const [agentId, agentData] of Object.entries(agents)) {
      const health = this.checkAgentHealth(agentId, agentData);
      agentHealths.push(health);

      if (health.healthy) {
        healthyCount += 1;
      } else {
        issues.push({
          agentId,
          issues: health.issues
        });
      }
    }

    return {
      healthy: issues.length === 0,
      totalAgents: agentHealths.length,
      healthyAgents: healthyCount,
      unhealthyAgents: agentHealths.length - healthyCount,
      agents: agentHealths,
      issues,
      timestamp: Date.now()
    };
  }

  /**
   * 获取Agent统计信息
   */
  getAgentStats() {
    const tracker = this.loadTrackerData();
    if (!tracker || !tracker.tracked_subagents) {
      return {
        total: 0,
        running: 0,
        completed: 0,
        failed: 0,
        timeout: 0
      };
    }

    const agents = tracker.tracked_subagents;
    const stats = {
      total: Object.keys(agents).length,
      running: 0,
      completed: 0,
      failed: 0,
      timeout: 0,
      pending: 0
    };

    for (const agent of Object.values(agents)) {
      if (agent.status === 'running') {
        stats.running += 1;
      } else if (agent.status === 'completed') {
        stats.completed += 1;
      } else if (agent.status === 'failed') {
        stats.failed += 1;
      } else if (agent.status === 'timeout') {
        stats.timeout += 1;
      } else if (agent.status === 'pending') {
        stats.pending += 1;
      }
    }

    return stats;
  }

  /**
   * 获取失败的Agent列表
   */
  getFailedAgents() {
    const tracker = this.loadTrackerData();
    if (!tracker || !tracker.tracked_subagents) {
      return [];
    }

    const agents = tracker.tracked_subagents;
    const failedAgents = [];

    for (const [agentId, agentData] of Object.entries(agents)) {
      if (agentData.status === 'failed' || agentData.status === 'timeout') {
        failedAgents.push({
          agentId,
          status: agentData.status,
          workOrderId: agentData.workOrderId,
          failureCount: agentData.failureCount || 0,
          lastUpdate: agentData.endedAt || this.getStartedAt(agentData)
        });
      }
    }

    return failedAgents;
  }
}

module.exports = AgentHealth;

/**
 * 核心健康检查模块 - 整合所有健康检查功能
 * 轻量级设计，支持定期检查和告警
 */

const AlertManager = require('./alert-manager');
const ResourceMonitor = require('./resource-monitor');
const AgentHealth = require('./agent-health');
const QueueHealth = require('./queue-health');

class HealthChecker {
  constructor(options = {}) {
    // 初始化各个检查模块
    this.alertManager = new AlertManager(options.alertManager || {});
    this.resourceMonitor = new ResourceMonitor(options.resourceMonitor || {});
    this.agentHealth = new AgentHealth(options.agentHealth || {});
    this.queueHealth = new QueueHealth(options.queueHealth || {});

    // 配置
    this.config = {
      checkIntervalMs: options.checkIntervalMs || 60 * 1000, // 1分钟
      enableAutoCheck: options.enableAutoCheck !== false
    };

    // 检查历史
    this.checkHistory = [];
    this.maxHistorySize = 100;
    this.isChecking = false;
  }

  /**
   * 执行完整的健康检查
   */
  async performHealthCheck() {
    if (this.isChecking) {
      console.log('Health check already in progress');
      return null;
    }

    this.isChecking = true;

    try {
      const checkResult = {
        timestamp: Date.now(),
        checks: {}
      };

      // 1. 检查系统资源
      const resourceHealth = await this.resourceMonitor.checkResourceHealth();
      checkResult.checks.resources = resourceHealth;

      // 处理资源告警
      for (const issue of resourceHealth.issues) {
        this.alertManager.createAlert(
          issue.type,
          issue.level,
          issue.message,
          {
            value: issue.value,
            threshold: issue.threshold
          }
        );
      }

      // 2. 检查Agent健康状态
      const agentHealth = this.agentHealth.checkAllAgentsHealth();
      checkResult.checks.agents = agentHealth;

      // 处理Agent告警
      for (const issue of agentHealth.issues) {
        for (const agentIssue of issue.issues) {
          this.alertManager.createAlert(
            'agent_unhealthy',
            'warning',
            `Agent ${issue.agentId}: ${agentIssue}`,
            {
              agentId: issue.agentId,
              issue: agentIssue
            }
          );
        }
      }

      // 3. 检查任务队列健康状态
      const queueHealth = this.queueHealth.checkQueueHealth();
      checkResult.checks.queue = queueHealth;

      // 处理队列告警
      for (const issue of queueHealth.issues) {
        this.alertManager.createAlert(
          issue.type,
          issue.level,
          issue.message,
          {
            queueSize: queueHealth.queueSize
          }
        );
      }

      // 4. 计算整体健康状态
      checkResult.overallHealth = {
        healthy: resourceHealth.healthy && agentHealth.healthy && queueHealth.healthy,
        resourcesHealthy: resourceHealth.healthy,
        agentsHealthy: agentHealth.healthy,
        queueHealthy: queueHealth.healthy,
        totalIssues: resourceHealth.issues.length + agentHealth.issues.length + queueHealth.issues.length
      };

      // 记录检查历史
      this.checkHistory.push(checkResult);
      if (this.checkHistory.length > this.maxHistorySize) {
        this.checkHistory.shift();
      }

      return checkResult;
    } catch (error) {
      console.error('Health check error:', error);
      this.alertManager.createAlert(
        'health_check_error',
        'error',
        `健康检查失败: ${error.message}`,
        { error: error.toString() }
      );
      return null;
    } finally {
      this.isChecking = false;
    }
  }

  /**
   * 启动定期健康检查
   */
  startPeriodicCheck() {
    if (this.checkInterval) {
      console.log('Periodic check already running');
      return;
    }

    console.log(`Starting periodic health check every ${this.config.checkIntervalMs}ms`);

    this.checkInterval = setInterval(async () => {
      await this.performHealthCheck();
    }, this.config.checkIntervalMs);
  }

  /**
   * 停止定期健康检查
   */
  stopPeriodicCheck() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
      console.log('Periodic health check stopped');
    }
  }

  /**
   * 获取健康检查报告
   */
  getHealthReport() {
    const activeAlerts = this.alertManager.getActiveAlerts();
    const alertStats = this.alertManager.getAlertStats();
    const resourceStats = this.resourceMonitor.getResourceStats();
    const agentStats = this.agentHealth.getAgentStats();
    const queueStats = this.queueHealth.getQueueStats();
    const queueThroughput = this.queueHealth.getQueueThroughput();

    return {
      timestamp: Date.now(),
      summary: {
        overallHealthy: activeAlerts.filter(a => a.level === 'critical').length === 0,
        activeAlerts: activeAlerts.length,
        criticalAlerts: activeAlerts.filter(a => a.level === 'critical').length,
        warningAlerts: activeAlerts.filter(a => a.level === 'warning').length
      },
      alerts: {
        stats: alertStats,
        active: activeAlerts.slice(-10) // 最近10条告警
      },
      resources: resourceStats,
      agents: agentStats,
      queue: {
        stats: queueStats,
        throughput: queueThroughput
      },
      lastCheck: this.checkHistory.length > 0 ? this.checkHistory[this.checkHistory.length - 1] : null
    };
  }

  /**
   * 获取详细的健康检查历史
   */
  getCheckHistory(limit = 10) {
    return this.checkHistory.slice(-limit);
  }

  /**
   * 获取失败的Agent列表
   */
  getFailedAgents() {
    return this.agentHealth.getFailedAgents();
  }

  /**
   * 获取长时间待处理的任务
   */
  getLongWaitingTasks() {
    return this.queueHealth.getLongWaitingTasks();
  }

  /**
   * 清空所有告警
   */
  clearAlerts() {
    this.alertManager.clearAlerts();
  }

  /**
   * 清空检查历史
   */
  clearCheckHistory() {
    this.checkHistory = [];
  }
}

module.exports = HealthChecker;

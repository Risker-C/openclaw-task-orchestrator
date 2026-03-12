/**
 * 告警管理器 - 处理健康检查告警
 * 轻量级设计，支持多种告警类型和级别
 */

const fs = require('fs');
const path = require('path');

class AlertManager {
  constructor(options = {}) {
    // 告警级别
    this.ALERT_LEVELS = {
      INFO: 'info',
      WARNING: 'warning',
      ERROR: 'error',
      CRITICAL: 'critical'
    };

    // 告警类型
    this.ALERT_TYPES = {
      AGENT_UNHEALTHY: 'agent_unhealthy',
      QUEUE_OVERFLOW: 'queue_overflow',
      HIGH_MEMORY: 'high_memory',
      HIGH_CPU: 'high_cpu',
      DISK_FULL: 'disk_full',
      TIMEOUT: 'timeout',
      FAILURE: 'failure'
    };

    // 配置
    this.config = {
      maxAlerts: options.maxAlerts || 1000,
      alertRetentionMs: options.alertRetentionMs || 24 * 60 * 60 * 1000, // 24小时
      alertFile: options.alertFile || '/tmp/health-check-alerts.json'
    };

    // 告警历史
    this.alerts = [];
    this.loadAlerts();
  }

  /**
   * 加载告警历史
   */
  loadAlerts() {
    try {
      if (fs.existsSync(this.config.alertFile)) {
        const data = fs.readFileSync(this.config.alertFile, 'utf8');
        this.alerts = JSON.parse(data);
        this.cleanupOldAlerts();
      }
    } catch (error) {
      console.error('Failed to load alerts:', error);
      this.alerts = [];
    }
  }

  /**
   * 清理过期的告警
   */
  cleanupOldAlerts() {
    const now = Date.now();
    this.alerts = this.alerts.filter(alert => {
      return (now - alert.timestamp) < this.config.alertRetentionMs;
    });

    // 限制告警数量
    if (this.alerts.length > this.config.maxAlerts) {
      this.alerts = this.alerts.slice(-this.config.maxAlerts);
    }
  }

  /**
   * 创建告警
   */
  createAlert(type, level, message, details = {}) {
    const alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: type,
      level: level,
      message: message,
      details: details,
      timestamp: Date.now(),
      resolved: false
    };

    this.alerts.push(alert);
    this.saveAlerts();

    return alert;
  }

  /**
   * 解决告警
   */
  resolveAlert(alertId) {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
      alert.resolvedAt = Date.now();
      this.saveAlerts();
      return true;
    }
    return false;
  }

  /**
   * 获取活跃告警
   */
  getActiveAlerts(type = null, level = null) {
    let filtered = this.alerts.filter(a => !a.resolved);

    if (type) {
      filtered = filtered.filter(a => a.type === type);
    }

    if (level) {
      filtered = filtered.filter(a => a.level === level);
    }

    return filtered;
  }

  /**
   * 获取告警统计
   */
  getAlertStats() {
    const stats = {
      total: this.alerts.length,
      active: 0,
      resolved: 0,
      byLevel: {},
      byType: {}
    };

    for (const alert of this.alerts) {
      if (alert.resolved) {
        stats.resolved++;
      } else {
        stats.active++;
      }

      // 按级别统计
      if (!stats.byLevel[alert.level]) {
        stats.byLevel[alert.level] = 0;
      }
      stats.byLevel[alert.level]++;

      // 按类型统计
      if (!stats.byType[alert.type]) {
        stats.byType[alert.type] = 0;
      }
      stats.byType[alert.type]++;
    }

    return stats;
  }

  /**
   * 保存告警到文件
   */
  saveAlerts() {
    try {
      fs.writeFileSync(
        this.config.alertFile,
        JSON.stringify(this.alerts, null, 2)
      );
    } catch (error) {
      console.error('Failed to save alerts:', error);
    }
  }

  /**
   * 清空所有告警
   */
  clearAlerts() {
    this.alerts = [];
    this.saveAlerts();
  }
}

module.exports = AlertManager;

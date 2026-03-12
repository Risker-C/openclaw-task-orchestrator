/**
 * 系统资源监控 - 监控CPU、内存、磁盘等系统资源
 * 轻量级设计，使用系统命令获取资源信息
 */

const os = require('os');
const fs = require('fs');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class ResourceMonitor {
  constructor(options = {}) {
    // 阈值配置
    this.thresholds = {
      memoryUsagePercent: options.memoryUsagePercent || 80,
      cpuUsagePercent: options.cpuUsagePercent || 80,
      diskUsagePercent: options.diskUsagePercent || 90
    };

    // 资源历史（用于计算平均值）
    this.history = {
      memory: [],
      cpu: [],
      disk: []
    };

    this.maxHistorySize = 10;
  }

  /**
   * 获取内存使用情况
   */
  getMemoryUsage() {
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;
    const usagePercent = (usedMemory / totalMemory) * 100;

    return {
      total: totalMemory,
      used: usedMemory,
      free: freeMemory,
      usagePercent: Math.round(usagePercent * 100) / 100,
      timestamp: Date.now()
    };
  }

  /**
   * 获取CPU使用情况
   */
  getCPUUsage() {
    const cpus = os.cpus();
    const cpuCount = cpus.length;

    // 计算平均CPU使用率
    let totalIdle = 0;
    let totalTick = 0;

    for (const cpu of cpus) {
      for (const type in cpu.times) {
        totalTick += cpu.times[type];
      }
      totalIdle += cpu.times.idle;
    }

    const idle = totalIdle / cpuCount;
    const total = totalTick / cpuCount;
    const usagePercent = 100 - ~~(100 * idle / total);

    return {
      cpuCount: cpuCount,
      usagePercent: usagePercent,
      timestamp: Date.now()
    };
  }

  /**
   * 获取磁盘使用情况
   */
  async getDiskUsage(path = '/') {
    try {
      const { stdout } = await execAsync(`df -B1 ${path} | tail -1`);
      const parts = stdout.trim().split(/\s+/);

      if (parts.length >= 5) {
        const total = parseInt(parts[1]);
        const used = parseInt(parts[2]);
        const available = parseInt(parts[3]);
        const usagePercent = (used / total) * 100;

        return {
          total: total,
          used: used,
          available: available,
          usagePercent: Math.round(usagePercent * 100) / 100,
          path: path,
          timestamp: Date.now()
        };
      }
    } catch (error) {
      console.error('Failed to get disk usage:', error);
    }

    return null;
  }

  /**
   * 获取进程数
   */
  getProcessCount() {
    return {
      count: os.cpus().length,
      timestamp: Date.now()
    };
  }

  /**
   * 检查资源健康状态
   */
  async checkResourceHealth() {
    const memory = this.getMemoryUsage();
    const cpu = this.getCPUUsage();
    const disk = await this.getDiskUsage();

    // 记录历史
    this.history.memory.push(memory.usagePercent);
    this.history.cpu.push(cpu.usagePercent);
    if (disk) {
      this.history.disk.push(disk.usagePercent);
    }

    // 限制历史大小
    if (this.history.memory.length > this.maxHistorySize) {
      this.history.memory.shift();
    }
    if (this.history.cpu.length > this.maxHistorySize) {
      this.history.cpu.shift();
    }
    if (this.history.disk.length > this.maxHistorySize) {
      this.history.disk.shift();
    }

    // 检查阈值
    const issues = [];

    if (memory.usagePercent > this.thresholds.memoryUsagePercent) {
      issues.push({
        type: 'high_memory',
        level: memory.usagePercent > 95 ? 'critical' : 'warning',
        message: `内存使用率过高: ${memory.usagePercent}%`,
        value: memory.usagePercent,
        threshold: this.thresholds.memoryUsagePercent
      });
    }

    if (cpu.usagePercent > this.thresholds.cpuUsagePercent) {
      issues.push({
        type: 'high_cpu',
        level: cpu.usagePercent > 95 ? 'critical' : 'warning',
        message: `CPU使用率过高: ${cpu.usagePercent}%`,
        value: cpu.usagePercent,
        threshold: this.thresholds.cpuUsagePercent
      });
    }

    if (disk && disk.usagePercent > this.thresholds.diskUsagePercent) {
      issues.push({
        type: 'disk_full',
        level: disk.usagePercent > 98 ? 'critical' : 'warning',
        message: `磁盘使用率过高: ${disk.usagePercent}%`,
        value: disk.usagePercent,
        threshold: this.thresholds.diskUsagePercent
      });
    }

    return {
      healthy: issues.length === 0,
      memory: memory,
      cpu: cpu,
      disk: disk,
      issues: issues,
      timestamp: Date.now()
    };
  }

  /**
   * 获取资源统计
   */
  getResourceStats() {
    const calculateAverage = (arr) => {
      if (arr.length === 0) return 0;
      return Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 100) / 100;
    };

    return {
      memory: {
        current: this.history.memory[this.history.memory.length - 1] || 0,
        average: calculateAverage(this.history.memory),
        max: Math.max(...this.history.memory, 0),
        min: Math.min(...this.history.memory, 0)
      },
      cpu: {
        current: this.history.cpu[this.history.cpu.length - 1] || 0,
        average: calculateAverage(this.history.cpu),
        max: Math.max(...this.history.cpu, 0),
        min: Math.min(...this.history.cpu, 0)
      },
      disk: {
        current: this.history.disk[this.history.disk.length - 1] || 0,
        average: calculateAverage(this.history.disk),
        max: Math.max(...this.history.disk, 0),
        min: Math.min(...this.history.disk, 0)
      }
    };
  }
}

module.exports = ResourceMonitor;

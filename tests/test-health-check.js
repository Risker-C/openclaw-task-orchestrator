/**
 * TASK-025: 健康检查系统v2 测试
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');

const AgentHealth = require('../src/health-check/agent-health');
const QueueHealth = require('../src/health-check/queue-health');
const AlertManager = require('../src/health-check/alert-manager');
const ResourceMonitor = require('../src/health-check/resource-monitor');
const HealthChecker = require('../src/health-check/health-checker');

function createTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'health-check-test-'));
}

function writeTrackerFile(trackerFile, payload) {
  fs.writeFileSync(trackerFile, JSON.stringify(payload, null, 2), 'utf8');
}

async function runTests() {
  console.log('=== TASK-025 健康检查系统测试开始 ===');

  const tmpDir = createTempDir();
  const trackerFile = path.join(tmpDir, 'subagent-tracker.json');
  const alertFile = path.join(tmpDir, 'alerts.json');

  const now = Date.now();
  writeTrackerFile(trackerFile, {
    tracked_subagents: {
      'agent-running': {
        status: 'running',
        startedAt: now - 3 * 60 * 1000,
        workOrderId: 'TASK-100'
      },
      'agent-completed': {
        status: 'completed',
        startedAt: now - 10 * 60 * 1000,
        endedAt: now - 2 * 60 * 1000,
        workOrderId: 'TASK-101'
      },
      'agent-failed': {
        status: 'failed',
        startedAt: now - 20 * 60 * 1000,
        failureCount: 2,
        workOrderId: 'TASK-102'
      },
      'agent-pending': {
        status: 'pending',
        createdAt: now - 25 * 60 * 1000,
        workOrderId: 'TASK-103'
      }
    }
  });

  // 1) AgentHealth
  const agentHealth = new AgentHealth({
    trackerFile,
    agentTimeoutMs: 5 * 60 * 1000,
    maxFailureCount: 1
  });

  const allAgentsHealth = agentHealth.checkAllAgentsHealth();
  assert.strictEqual(allAgentsHealth.totalAgents, 4, '应识别4个agent');
  assert.strictEqual(allAgentsHealth.healthy, false, '应检测到不健康agent');

  const failedAgents = agentHealth.getFailedAgents();
  assert.ok(failedAgents.length >= 1, '应返回失败agent列表');

  // 2) QueueHealth
  const queueHealth = new QueueHealth({
    trackerFile,
    maxQueueSize: 5,
    warningQueueSize: 1,
    maxWaitTimeMs: 5 * 60 * 1000
  });

  const queueResult = queueHealth.checkQueueHealth();
  assert.strictEqual(queueResult.queueSize, 2, '队列大小应包含running+pending');
  assert.strictEqual(queueResult.healthy, false, '应检测到队列告警（接近满/等待过长）');
  assert.ok(queueResult.issues.length >= 1, '应产生至少1条队列问题');

  const longWaitingTasks = queueHealth.getLongWaitingTasks();
  assert.ok(longWaitingTasks.length >= 1, '应检测到长等待任务');

  // 3) AlertManager
  const alertManager = new AlertManager({
    alertFile,
    maxAlerts: 100,
    alertRetentionMs: 60 * 60 * 1000
  });

  const a1 = alertManager.createAlert('queue_overflow', 'warning', '队列接近满');
  const a2 = alertManager.createAlert('agent_unhealthy', 'error', 'Agent失败');
  assert.ok(a1.id && a2.id, '告警应创建成功');

  const activeAlerts = alertManager.getActiveAlerts();
  assert.strictEqual(activeAlerts.length, 2, '活跃告警应为2');

  alertManager.resolveAlert(a1.id);
  const stats = alertManager.getAlertStats();
  assert.strictEqual(stats.resolved, 1, '应有1条已解决告警');

  // 4) ResourceMonitor
  const resourceMonitor = new ResourceMonitor({
    memoryUsagePercent: 100,
    cpuUsagePercent: 100,
    diskUsagePercent: 100
  });

  const resourceResult = await resourceMonitor.checkResourceHealth();
  assert.ok(resourceResult.memory && resourceResult.cpu, '资源检查应返回内存和CPU');
  assert.strictEqual(resourceResult.healthy, true, '高阈值下应健康');

  // 5) HealthChecker 集成测试
  const checker = new HealthChecker({
    alertManager: { alertFile },
    resourceMonitor: { memoryUsagePercent: 100, cpuUsagePercent: 100, diskUsagePercent: 100 },
    agentHealth: { trackerFile, agentTimeoutMs: 5 * 60 * 1000, maxFailureCount: 1 },
    queueHealth: { trackerFile, warningQueueSize: 1, maxWaitTimeMs: 5 * 60 * 1000 }
  });

  const fullResult = await checker.performHealthCheck();
  assert.ok(fullResult && fullResult.checks, '完整健康检查应返回结果');
  assert.ok(typeof fullResult.overallHealth.healthy === 'boolean', '应包含整体健康状态');

  const report = checker.getHealthReport();
  assert.ok(report.summary && report.alerts, '健康报告应包含summary和alerts');

  // 清理
  checker.stopPeriodicCheck();
  fs.rmSync(tmpDir, { recursive: true, force: true });

  console.log('✅ TASK-025 健康检查系统测试全部通过');
}

runTests().catch((error) => {
  console.error('❌ TASK-025 测试失败:', error);
  process.exit(1);
});

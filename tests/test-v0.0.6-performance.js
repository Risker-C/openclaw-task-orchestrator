/**
 * TASK-026: V0.0.6 性能回归测试
 * 目标：确保新增能力不会显著拖慢关键路径
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const QueueHealth = require('../src/health-check/queue-health');
const AgentHealth = require('../src/health-check/agent-health');

function createTrackerFile(agentCount = 1000) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'perf-v006-'));
  const trackerFile = path.join(tmpDir, 'subagent-tracker.json');

  const tracked_subagents = {};
  const now = Date.now();
  for (let i = 0; i < agentCount; i += 1) {
    tracked_subagents[`agent-${i}`] = {
      status: i % 5 === 0 ? 'pending' : 'running',
      createdAt: now - (i * 1000),
      startedAt: now - (i * 1000),
      workOrderId: `TASK-${i}`
    };
  }

  fs.writeFileSync(trackerFile, JSON.stringify({ tracked_subagents }), 'utf8');
  return { tmpDir, trackerFile };
}

function cleanup(tmpDir) {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

function benchmark(label, fn) {
  const start = Date.now();
  const result = fn();
  const duration = Date.now() - start;
  console.log(`${label}: ${duration}ms`);
  return { result, duration };
}

(function run() {
  console.log('=== V0.0.6 性能测试开始 ===');

  const { tmpDir, trackerFile } = createTrackerFile(1000);

  try {
    const queue = new QueueHealth({ trackerFile, warningQueueSize: 100, maxQueueSize: 3000 });
    const agent = new AgentHealth({ trackerFile, agentTimeoutMs: 60 * 60 * 1000 });

    const q1 = benchmark('QueueHealth.checkQueueHealth(1000 agents)', () => queue.checkQueueHealth());
    const a1 = benchmark('AgentHealth.checkAllAgentsHealth(1000 agents)', () => agent.checkAllAgentsHealth());

    assert.ok(q1.result.queueSize > 0, '队列结果应有效');
    assert.strictEqual(a1.result.totalAgents, 1000, '应识别1000个agent');

    // 轻量目标：单次检查应在1秒内完成
    assert.ok(q1.duration < 1000, `QueueHealth检查耗时过高: ${q1.duration}ms`);
    assert.ok(a1.duration < 1000, `AgentHealth检查耗时过高: ${a1.duration}ms`);

    console.log('✅ V0.0.6 性能测试通过');
  } finally {
    cleanup(tmpDir);
  }
})();

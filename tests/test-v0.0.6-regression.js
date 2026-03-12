/**
 * TASK-026: V0.0.6 回归测试套件
 * 覆盖 TASK-022 ~ TASK-025 的核心能力
 */

const { execSync } = require('child_process');

const testCases = [
  {
    id: 'TASK-022',
    name: '路径访问异常修复回归',
    command: 'node tests/test-paths.js'
  },
  {
    id: 'TASK-023',
    name: '超时配置灵活性增强回归',
    command: 'node tests/test-timeout-config.js'
  },
  {
    id: 'TASK-024',
    name: 'Agent协调机制回归（Python单元+集成）',
    command: 'python3 -m pytest tests/test_agent_coordinator.py tests/test_agent_coordinator_integration.py -q'
  },
  {
    id: 'TASK-025',
    name: '健康检查系统v2回归',
    command: 'node tests/test-health-check.js'
  }
];

function runCase(testCase) {
  const startedAt = Date.now();
  try {
    execSync(testCase.command, { stdio: 'pipe' });
    return {
      ...testCase,
      passed: true,
      durationMs: Date.now() - startedAt,
      error: null
    };
  } catch (error) {
    return {
      ...testCase,
      passed: false,
      durationMs: Date.now() - startedAt,
      error: error.stderr ? error.stderr.toString() : error.message
    };
  }
}

function printSummary(results) {
  const passed = results.filter(r => r.passed).length;
  const failed = results.length - passed;
  const passRate = Math.round((passed / results.length) * 100);
  const totalTime = results.reduce((sum, r) => sum + r.durationMs, 0);

  console.log('\n=== V0.0.6 回归测试总结 ===');
  results.forEach(r => {
    const flag = r.passed ? '✅' : '❌';
    console.log(`${flag} ${r.id} ${r.name} (${r.durationMs}ms)`);
    if (!r.passed) {
      console.log(`   错误: ${(r.error || '').split('\n')[0]}`);
    }
  });

  console.log('\n--- 统计 ---');
  console.log(`总用例: ${results.length}`);
  console.log(`通过: ${passed}`);
  console.log(`失败: ${failed}`);
  console.log(`通过率: ${passRate}%`);
  console.log(`总耗时: ${totalTime}ms`);

  if (failed > 0) {
    process.exit(1);
  }
}

console.log('=== 开始执行 V0.0.6 回归测试 ===');
const results = testCases.map(runCase);
printSummary(results);

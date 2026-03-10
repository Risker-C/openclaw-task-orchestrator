/**
 * Timeout Configuration Tests
 */

const { TimeoutConfig, getInstance, DEFAULT_TIMEOUTS } = require('../src/config/timeout-config.js');

console.log('=== Timeout Configuration Tests ===\n');

// Test 1: 创建实例
console.log('Test 1: Create Instance');
const config = getInstance();
console.log(`Instance created: ${config !== null}`);
console.log(`Config loaded: ${config.config !== null}\n`);

// Test 2: 获取默认超时
console.log('Test 2: Get Default Timeouts');
console.log(`Global timeout: ${config.getTimeout('global')} ms (expected: ${DEFAULT_TIMEOUTS.global})`);
console.log(`Subagent timeout: ${config.getTimeout('subagent')} ms (expected: ${DEFAULT_TIMEOUTS.subagent})`);
console.log(`Task timeout: ${config.getTimeout('task')} ms (expected: ${DEFAULT_TIMEOUTS.task})`);
console.log(`API timeout: ${config.getTimeout('api')} ms (expected: ${DEFAULT_TIMEOUTS.api})`);
console.log(`Database timeout: ${config.getTimeout('database')} ms (expected: ${DEFAULT_TIMEOUTS.database})`);
console.log(`File timeout: ${config.getTimeout('file')} ms (expected: ${DEFAULT_TIMEOUTS.file})\n`);

// Test 3: 获取任务级别的超时
console.log('Test 3: Get Task-Level Timeout');
const taskTimeout = config.getTimeout('task', { taskId: 'TASK-022' });
console.log(`TASK-022 timeout: ${taskTimeout} ms`);
console.log(`Pass: ${taskTimeout === 3600000}\n`);

// Test 4: 获取Agent级别的超时
console.log('Test 4: Get Agent-Level Timeout');
const agentTimeout = config.getTimeout('subagent', { agentId: 'implementation-planner' });
console.log(`implementation-planner timeout: ${agentTimeout} ms`);
console.log(`Pass: ${agentTimeout === 3600000}\n`);

// Test 5: 设置任务级别的超时
console.log('Test 5: Set Task-Level Timeout');
config.setTaskTimeout('TASK-999', 5400000);
const newTaskTimeout = config.getTimeout('task', { taskId: 'TASK-999' });
console.log(`TASK-999 timeout: ${newTaskTimeout} ms`);
console.log(`Pass: ${newTaskTimeout === 5400000}\n`);

// Test 6: 设置Agent级别的超时
console.log('Test 6: Set Agent-Level Timeout');
config.setAgentTimeout('test-agent', 2700000);
const newAgentTimeout = config.getTimeout('subagent', { agentId: 'test-agent' });
console.log(`test-agent timeout: ${newAgentTimeout} ms`);
console.log(`Pass: ${newAgentTimeout === 2700000}\n`);

// Test 7: 添加超时规则
console.log('Test 7: Add Timeout Rule');
config.addRule({
  name: '测试规则',
  conditions: [
    {
      field: 'taskType',
      operator: 'equals',
      value: 'test'
    }
  ],
  timeout: 900000
});
const ruleTimeout = config.getTimeout('task', { taskType: 'test' });
console.log(`Test rule timeout: ${ruleTimeout} ms`);
console.log(`Pass: ${ruleTimeout === 900000}\n`);

// Test 8: 设置分类超时
console.log('Test 8: Set Category Timeout');
config.setCategoryTimeout('api', 60000);
const newApiTimeout = config.getTimeout('api');
console.log(`New API timeout: ${newApiTimeout} ms`);
console.log(`Pass: ${newApiTimeout === 60000}\n`);

// Test 9: 获取完整配置
console.log('Test 9: Get Full Config');
const fullConfig = config.getFullConfig();
console.log(`Full config keys: ${Object.keys(fullConfig).join(', ')}`);
console.log(`Pass: ${fullConfig.global && fullConfig.categories && fullConfig.tasks}\n`);

console.log('=== All Tests Completed ===');

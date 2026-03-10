/**
 * Path Configuration Tests
 * 验证路径配置模块的正确性
 */

const path = require('path');
const { paths, getProjectRoot, getWorkspaceRoot, ensureDir } = require('../src/config/paths.js');

console.log('=== Path Configuration Tests ===\n');

// Test 1: 获取项目根目录
console.log('Test 1: Project Root');
console.log(`Project Root: ${paths.projectRoot}`);
console.log(`Expected: /root/.openclaw/workspace/openclaw-task-orchestrator`);
console.log(`Pass: ${paths.projectRoot.endsWith('openclaw-task-orchestrator')}\n`);

// Test 2: 获取工作空间根目录
console.log('Test 2: Workspace Root');
console.log(`Workspace Root: ${paths.workspaceRoot}`);
console.log(`Expected: /root/.openclaw/workspace`);
console.log(`Pass: ${paths.workspaceRoot === '/root/.openclaw/workspace'}\n`);

// Test 3: 解析相对路径
console.log('Test 3: Resolve Relative Path');
const relativePath = 'src/config/paths.js';
const resolvedPath = paths.resolve(relativePath);
console.log(`Relative Path: ${relativePath}`);
console.log(`Resolved Path: ${resolvedPath}`);
console.log(`Is Absolute: ${path.isAbsolute(resolvedPath)}`);
console.log(`Pass: ${path.isAbsolute(resolvedPath)}\n`);

// Test 4: 解析绝对路径
console.log('Test 4: Resolve Absolute Path');
const absolutePath = '/tmp/test.json';
const resolvedAbsolutePath = paths.resolve(absolutePath);
console.log(`Absolute Path: ${absolutePath}`);
console.log(`Resolved Path: ${resolvedAbsolutePath}`);
console.log(`Pass: ${resolvedAbsolutePath === absolutePath}\n`);

// Test 5: 常用路径
console.log('Test 5: Common Paths');
console.log(`Tracker File: ${paths.trackerFile}`);
console.log(`Notification File: ${paths.notificationFile}`);
console.log(`Ticket History File: ${paths.ticketHistoryFile}`);
console.log(`Logs Dir: ${paths.logsDir}`);
console.log(`Config Dir: ${paths.configDir}`);
console.log(`Scripts Dir: ${paths.scriptsDir}`);
console.log(`Src Dir: ${paths.srcDir}`);
console.log(`Tests Dir: ${paths.testsDir}\n`);

// Test 6: 环境变量设置
console.log('Test 6: Environment Variables');
console.log(`PROJECT_ROOT: ${process.env.PROJECT_ROOT}`);
console.log(`WORKSPACE_ROOT: ${process.env.WORKSPACE_ROOT}`);
console.log(`Pass: ${process.env.PROJECT_ROOT && process.env.WORKSPACE_ROOT}\n`);

console.log('=== All Tests Completed ===');

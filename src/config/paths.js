/**
 * Path Configuration Module
 * 统一管理所有路径，支持绝对路径和相对路径
 */

const path = require('path');
const fs = require('fs');

// 获取项目根目录
function getProjectRoot() {
  // 优先使用环境变量
  if (process.env.PROJECT_ROOT) {
    return process.env.PROJECT_ROOT;
  }
  
  // 其次使用 __dirname 推导
  // 假设此文件在 src/config/paths.js
  const currentDir = __dirname;
  const projectRoot = path.resolve(currentDir, '../../');
  
  return projectRoot;
}

// 获取工作空间根目录
function getWorkspaceRoot() {
  if (process.env.WORKSPACE_ROOT) {
    return process.env.WORKSPACE_ROOT;
  }
  
  // 默认为 /root/.openclaw/workspace
  return '/root/.openclaw/workspace';
}

// 路径配置对象
const paths = {
  // 项目根目录
  projectRoot: getProjectRoot(),
  
  // 工作空间根目录
  workspaceRoot: getWorkspaceRoot(),
  
  // 获取绝对路径的方法
  resolve: function(relativePath) {
    if (path.isAbsolute(relativePath)) {
      return relativePath;
    }
    return path.resolve(this.projectRoot, relativePath);
  },
  
  // 获取工作空间中的绝对路径
  resolveWorkspace: function(relativePath) {
    if (path.isAbsolute(relativePath)) {
      return relativePath;
    }
    return path.resolve(this.workspaceRoot, relativePath);
  },
  
  // 常用路径
  get trackerFile() {
    return this.resolveWorkspace('subagent-tracker.json');
  },
  
  get notificationFile() {
    return '/tmp/subagent-notifications.json';
  },
  
  get ticketHistoryFile() {
    return this.resolveWorkspace('ticket-update-history.json');
  },
  
  get logsDir() {
    return this.resolve('logs');
  },
  
  get configDir() {
    return this.resolve('config');
  },
  
  get scriptsDir() {
    return this.resolve('scripts');
  },
  
  get srcDir() {
    return this.resolve('src');
  },
  
  get testsDir() {
    return this.resolve('tests');
  },
};

// 确保目录存在
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// 初始化路径
function initializePaths() {
  // 确保关键目录存在
  ensureDir(paths.logsDir);
  ensureDir(paths.configDir);
  
  // 设置环境变量供子进程使用
  process.env.PROJECT_ROOT = paths.projectRoot;
  process.env.WORKSPACE_ROOT = paths.workspaceRoot;
}

module.exports = {
  paths,
  getProjectRoot,
  getWorkspaceRoot,
  ensureDir,
  initializePaths,
};

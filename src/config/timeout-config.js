/**
 * Timeout Configuration Module
 * 支持全局、任务级别、Agent级别的超时配置
 */

const fs = require('fs');
const path = require('path');
const { paths } = require('./paths.js');

// 默认超时配置（毫秒）
const DEFAULT_TIMEOUTS = {
  global: 30 * 60 * 1000,        // 全局默认: 30分钟
  subagent: 30 * 60 * 1000,      // Subagent默认: 30分钟
  task: 60 * 60 * 1000,          // 任务默认: 60分钟
  api: 30 * 1000,                // API调用默认: 30秒
  database: 10 * 1000,           // 数据库操作默认: 10秒
  file: 5 * 1000,                // 文件操作默认: 5秒
};

// 超时配置文件路径
const TIMEOUT_CONFIG_FILE = path.resolve(paths.configDir, 'timeout-config.json');

class TimeoutConfig {
  constructor() {
    this.config = this.loadConfig();
  }
  
  /**
   * 加载超时配置
   */
  loadConfig() {
    if (fs.existsSync(TIMEOUT_CONFIG_FILE)) {
      try {
        const config = JSON.parse(fs.readFileSync(TIMEOUT_CONFIG_FILE, 'utf8'));
        return this.mergeWithDefaults(config);
      } catch (error) {
        console.warn(`Failed to load timeout config: ${error.message}, using defaults`);
        return this.getDefaultConfig();
      }
    }
    return this.getDefaultConfig();
  }
  
  /**
   * 获取默认配置
   */
  getDefaultConfig() {
    return {
      global: DEFAULT_TIMEOUTS.global,
      categories: {
        subagent: DEFAULT_TIMEOUTS.subagent,
        task: DEFAULT_TIMEOUTS.task,
        api: DEFAULT_TIMEOUTS.api,
        database: DEFAULT_TIMEOUTS.database,
        file: DEFAULT_TIMEOUTS.file,
      },
      tasks: {},        // 任务级别的超时配置
      agents: {},       // Agent级别的超时配置
      rules: [],        // 超时规则（基于条件的动态配置）
    };
  }
  
  /**
   * 合并配置与默认值
   */
  mergeWithDefaults(config) {
    const merged = this.getDefaultConfig();
    
    if (config.global) {
      merged.global = config.global;
    }
    
    if (config.categories) {
      merged.categories = { ...merged.categories, ...config.categories };
    }
    
    if (config.tasks) {
      merged.tasks = { ...config.tasks };
    }
    
    if (config.agents) {
      merged.agents = { ...config.agents };
    }
    
    if (config.rules) {
      merged.rules = config.rules;
    }
    
    return merged;
  }
  
  /**
   * 获取超时时间
   * @param {string} type - 超时类型 (global, subagent, task, api, database, file)
   * @param {object} context - 上下文信息 (taskId, agentId, etc.)
   * @returns {number} 超时时间（毫秒）
   */
  getTimeout(type, context = {}) {
    // 1. 检查任务级别的超时配置
    if (context.taskId && this.config.tasks[context.taskId]) {
      return this.config.tasks[context.taskId];
    }
    
    // 2. 检查Agent级别的超时配置
    if (context.agentId && this.config.agents[context.agentId]) {
      return this.config.agents[context.agentId];
    }
    
    // 3. 检查规则
    for (const rule of this.config.rules) {
      if (this.matchesRule(rule, context)) {
        return rule.timeout;
      }
    }
    
    // 4. 使用分类超时配置
    if (this.config.categories[type]) {
      return this.config.categories[type];
    }
    
    // 5. 使用全局超时配置
    return this.config.global;
  }
  
  /**
   * 检查是否匹配规则
   */
  matchesRule(rule, context) {
    if (!rule.conditions) {
      return false;
    }
    
    for (const condition of rule.conditions) {
      const contextValue = this.getNestedValue(context, condition.field);
      
      switch (condition.operator) {
        case 'equals':
          if (contextValue !== condition.value) return false;
          break;
        case 'contains':
          if (!String(contextValue).includes(condition.value)) return false;
          break;
        case 'startsWith':
          if (!String(contextValue).startsWith(condition.value)) return false;
          break;
        case 'endsWith':
          if (!String(contextValue).endsWith(condition.value)) return false;
          break;
        case 'greaterThan':
          if (contextValue <= condition.value) return false;
          break;
        case 'lessThan':
          if (contextValue >= condition.value) return false;
          break;
        default:
          return false;
      }
    }
    
    return true;
  }
  
  /**
   * 获取嵌套对象的值
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, prop) => current?.[prop], obj);
  }
  
  /**
   * 设置任务级别的超时
   */
  setTaskTimeout(taskId, timeout) {
    this.config.tasks[taskId] = timeout;
    this.saveConfig();
  }
  
  /**
   * 设置Agent级别的超时
   */
  setAgentTimeout(agentId, timeout) {
    this.config.agents[agentId] = timeout;
    this.saveConfig();
  }
  
  /**
   * 添加超时规则
   */
  addRule(rule) {
    this.config.rules.push(rule);
    this.saveConfig();
  }
  
  /**
   * 设置分类超时
   */
  setCategoryTimeout(category, timeout) {
    if (this.config.categories[category] !== undefined) {
      this.config.categories[category] = timeout;
      this.saveConfig();
    }
  }
  
  /**
   * 保存配置到文件
   */
  saveConfig() {
    try {
      fs.writeFileSync(TIMEOUT_CONFIG_FILE, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error(`Failed to save timeout config: ${error.message}`);
    }
  }
  
  /**
   * 获取完整配置
   */
  getFullConfig() {
    return JSON.parse(JSON.stringify(this.config));
  }
  
  /**
   * 重置为默认配置
   */
  resetToDefaults() {
    this.config = this.getDefaultConfig();
    this.saveConfig();
  }
}

// 创建单例实例
let instance = null;

function getInstance() {
  if (!instance) {
    instance = new TimeoutConfig();
  }
  return instance;
}

module.exports = {
  TimeoutConfig,
  getInstance,
  DEFAULT_TIMEOUTS,
};

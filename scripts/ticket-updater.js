#!/usr/bin/env node

/**
 * Ticket Updater - 幂等工单更新器
 * 
 * 核心职责：
 * 1. 接收状态机的更新指令
 * 2. 执行幂等的Bitable更新
 * 3. 记录更新历史防止重复
 */

const fs = require('fs');
const path = require('path');

// 导入路径配置
const { paths, initializePaths } = require(path.resolve(__dirname, '../src/config/paths.js'));

// 初始化路径
initializePaths();

const UPDATE_HISTORY_FILE = paths.ticketHistoryFile;

class TicketUpdater {
  constructor() {
    this.history = this.loadHistory();
  }
  
  loadHistory() {
    if (fs.existsSync(UPDATE_HISTORY_FILE)) {
      return JSON.parse(fs.readFileSync(UPDATE_HISTORY_FILE, 'utf8'));
    }
    return {
      updates: {},
      last_cleanup: null
    };
  }
  
  saveHistory() {
    fs.writeFileSync(UPDATE_HISTORY_FILE, JSON.stringify(this.history, null, 2));
  }
  
  /**
   * 检查更新是否已执行（幂等性检查）
   * @param {string} idempotencyKey - 幂等键
   * @returns {boolean} 是否已执行
   */
  isAlreadyExecuted(idempotencyKey) {
    return this.history.updates[idempotencyKey] !== undefined;
  }
  
  /**
   * 记录更新历史
   * @param {string} idempotencyKey - 幂等键
   * @param {Object} result - 更新结果
   */
  recordUpdate(idempotencyKey, result) {
    this.history.updates[idempotencyKey] = {
      timestamp: Date.now(),
      result: result,
      success: result.success || false
    };
    
    // 清理7天前的历史记录
    this.cleanupOldHistory();
    this.saveHistory();
  }
  
  cleanupOldHistory() {
    const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    const updates = this.history.updates;
    
    for (const key in updates) {
      if (updates[key].timestamp < sevenDaysAgo) {
        delete updates[key];
      }
    }
    
    this.history.last_cleanup = Date.now();
  }
  
  /**
   * 执行工单更新
   * @param {Object} command - 更新指令
   * @returns {Promise<Object>} 更新结果
   */
  async executeUpdate(command) {
    const { idempotency_key, app_token, table_id, record_id, fields } = command;
    
    // 幂等性检查
    if (this.isAlreadyExecuted(idempotency_key)) {
      console.log(`⏭️  Skip: Update already executed (key: ${idempotency_key})`);
      return {
        success: true,
        skipped: true,
        reason: 'idempotent_skip',
        cached_result: this.history.updates[idempotency_key]
      };
    }
    
    try {
      // 这里应该调用实际的Bitable API
      // 暂时返回模拟结果
      console.log(`📝 Executing update for record ${record_id}:`);
      console.log(`   Status: ${fields['状态']}`);
      console.log(`   Progress: ${fields['进度百分比']}%`);
      console.log(`   Duration: ${fields['任务时长']}`);
      
      const result = {
        success: true,
        record_id: record_id,
        updated_fields: Object.keys(fields),
        timestamp: Date.now()
      };
      
      // 记录更新历史
      this.recordUpdate(idempotency_key, result);
      
      return result;
      
    } catch (error) {
      console.error(`❌ Update failed:`, error);
      
      const errorResult = {
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
      
      // 即使失败也记录，避免无限重试
      this.recordUpdate(idempotency_key, errorResult);
      
      return errorResult;
    }
  }
  
  /**
   * 批量更新工单
   * @param {Array<Object>} commands - 更新指令列表
   * @returns {Promise<Array<Object>>} 更新结果列表
   */
  async batchUpdate(commands) {
    const results = [];
    
    for (const command of commands) {
      const result = await this.executeUpdate(command);
      results.push(result);
    }
    
    return results;
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TicketUpdater };
}

// CLI测试
if (require.main === module) {
  const updater = new TicketUpdater();
  
  console.log('\n=== 测试幂等性 ===');
  
  const testCommand = {
    idempotency_key: 'TEST-001_completed_1234567890',
    app_token: 'test_token',
    table_id: 'test_table',
    record_id: 'test_record',
    fields: {
      '状态': '已完成',
      '进度百分比': 100,
      '任务时长': '5分钟'
    }
  };
  
  // 第一次执行
  console.log('\n第一次执行:');
  updater.executeUpdate(testCommand).then(result => {
    console.log('结果:', result);
    
    // 第二次执行（应该被跳过）
    console.log('\n第二次执行（测试幂等性）:');
    return updater.executeUpdate(testCommand);
  }).then(result => {
    console.log('结果:', result);
    console.log('\n预期：第二次执行应该被跳过（skipped: true）');
  });
}
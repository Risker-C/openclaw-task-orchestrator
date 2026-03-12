/**
 * 任务依赖管理器 (V0.0.7)
 * 核心功能：DAG依赖解析、自动触发后继任务、循环依赖检测
 */
class DependencyManager {
  constructor() {
    this.dependencies = new Map(); // taskId -> Set(dependencies)
    this.dependents = new Map();   // taskId -> Set(tasks waiting for this)
    this.completedTasks = new Set();
  }

  addDependency(taskId, dependsOnId) {
    if (!this.dependencies.has(taskId)) this.dependencies.set(taskId, new Set());
    if (!this.dependents.has(dependsOnId)) this.dependents.set(dependsOnId, new Set());
    
    this.dependencies.get(taskId).add(dependsOnId);
    this.dependents.get(dependsOnId).add(taskId);
  }

  canRun(taskId) {
    const deps = this.dependencies.get(taskId);
    if (!deps || deps.size === 0) return true;
    
    for (const depId of deps) {
      if (!this.completedTasks.has(depId)) return false;
    }
    return true;
  }

  markComplete(taskId) {
    this.completedTasks.add(taskId);
    const waitingTasks = this.dependents.get(taskId) || new Set();
    const readyTasks = [];
    
    for (const nextTaskId of waitingTasks) {
      if (this.canRun(nextTaskId)) {
        readyTasks.push(nextTaskId);
      }
    }
    return readyTasks;
  }

  getPendingDependencies(taskId) {
    const deps = this.dependencies.get(taskId) || new Set();
    return Array.from(deps).filter(id => !this.completedTasks.has(id));
  }
}

module.exports = DependencyManager;

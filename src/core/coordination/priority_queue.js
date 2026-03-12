/**
 * 高级优先级队列系统 (V0.0.7)
 * 核心功能：多级优先级调度、任务权重平衡、实时状态监控
 */
class PriorityQueue {
  constructor() {
    this.queues = {
      CRITICAL: [], // P0
      HIGH: [],     // P1
      MEDIUM: [],   // P2
      LOW: []       // P3
    };
    this.activeTasks = new Map();
  }

  enqueue(task, priority = 'MEDIUM') {
    if (!this.queues[priority]) priority = 'MEDIUM';
    const taskEntry = {
      id: task.id || `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      task,
      priority,
      enqueuedAt: Date.now()
    };
    this.queues[priority].push(taskEntry);
    console.log(`[PriorityQueue] Enqueued ${taskEntry.id} with priority ${priority}`);
    return taskEntry.id;
  }

  dequeue() {
    const levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    for (const level of levels) {
      if (this.queues[level].length > 0) {
        const taskEntry = this.queues[level].shift();
        this.activeTasks.set(taskEntry.id, { ...taskEntry, startedAt: Date.now() });
        return taskEntry;
      }
    }
    return null;
  }

  complete(taskId) {
    if (this.activeTasks.has(taskId)) {
      this.activeTasks.delete(taskId);
      return true;
    }
    return false;
  }

  getStatus() {
    return {
      pendingCount: Object.values(this.queues).reduce((acc, q) => acc + q.length, 0),
      activeCount: this.activeTasks.size,
      queues: Object.fromEntries(Object.entries(this.queues).map(([k, v]) => [k, v.length]))
    };
  }
}

module.exports = PriorityQueue;

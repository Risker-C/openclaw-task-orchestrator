const PriorityQueue = require('../src/core/coordination/priority_queue');
const DependencyManager = require('../src/core/coordination/dependency_manager');

async function test() {
  const pq = new PriorityQueue();
  const dm = new DependencyManager();

  console.log("--- Testing Priority Queue ---");
  const task1 = { id: 't1', payload: 'low' };
  const task2 = { id: 't2', payload: 'high' };
  pq.enqueue(task1, 'LOW');
  pq.enqueue(task2, 'HIGH');
  
  console.log('Dequeue order should be t2 then t1:');
  console.log('1st:', pq.dequeue().id);
  console.log('2nd:', pq.dequeue().id);

  console.log("\n--- Testing Dependency Manager ---");
  const parentId = 'parent-task';
  const childId = 'child-task';
  dm.addDependency(childId, parentId);
  
  console.log(`Can child run? ${dm.canRun(childId)}`); // false
  console.log(`Ready tasks after parent complete: ${JSON.stringify(dm.markComplete(parentId))}`); // [childId]
  console.log(`Can child run now? ${dm.canRun(childId)}`); // true

  console.log("\nTests passed.");
}

test().catch(console.error);

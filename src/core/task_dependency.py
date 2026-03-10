"""
任务依赖关系管理 - 支持任务间的依赖关系和工作流编排

支持顺序依赖、并行依赖、条件依赖等多种依赖类型
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio


class DependencyType(str, Enum):
    """依赖类型"""
    SEQUENTIAL = "sequential"      # 顺序依赖：前置任务完成后才能执行
    PARALLEL = "parallel"          # 并行依赖：可以与前置任务并行执行
    CONDITIONAL = "conditional"    # 条件依赖：根据前置任务结果决定是否执行
    OPTIONAL = "optional"          # 可选依赖：前置任务失败不影响当前任务


class DependencyCondition(str, Enum):
    """依赖条件"""
    SUCCESS = "success"            # 前置任务成功
    FAILURE = "failure"            # 前置任务失败
    ALWAYS = "always"              # 总是执行
    CUSTOM = "custom"              # 自定义条件


@dataclass
class TaskDependency:
    """任务依赖关系"""
    task_id: str                   # 当前任务ID
    depends_on: str                # 依赖的任务ID
    dependency_type: DependencyType = DependencyType.SEQUENTIAL
    condition: DependencyCondition = DependencyCondition.SUCCESS
    custom_condition: Optional[str] = None  # 自定义条件表达式
    
    # 依赖信息
    created_at: datetime = field(default_factory=datetime.now)
    satisfied: bool = False        # 依赖是否已满足
    satisfied_at: Optional[datetime] = None


@dataclass
class TaskDependencyGraph:
    """任务依赖图"""
    task_id: str
    dependencies: List[TaskDependency] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)  # 依赖此任务的其他任务
    
    def add_dependency(self, dependency: TaskDependency):
        """添加依赖"""
        self.dependencies.append(dependency)
    
    def add_dependent(self, task_id: str):
        """添加依赖者"""
        if task_id not in self.dependents:
            self.dependents.append(task_id)
    
    def get_blocking_tasks(self) -> List[str]:
        """获取阻塞当前任务的任务列表"""
        return [dep.depends_on for dep in self.dependencies if not dep.satisfied]


class DependencyManager:
    """任务依赖关系管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 依赖图存储
        self.dependency_graphs: Dict[str, TaskDependencyGraph] = {}
        
        # 任务状态缓存
        self.task_status_cache: Dict[str, Dict[str, Any]] = {}
        
        # 循环依赖检测
        self._cycle_detection_cache: Dict[str, Set[str]] = {}
    
    async def add_dependency(self, task_id: str, depends_on: str,
                            dependency_type: DependencyType = DependencyType.SEQUENTIAL,
                            condition: DependencyCondition = DependencyCondition.SUCCESS,
                            custom_condition: Optional[str] = None) -> bool:
        """
        添加任务依赖关系
        
        Args:
            task_id: 当前任务ID
            depends_on: 依赖的任务ID
            dependency_type: 依赖类型
            condition: 依赖条件
            custom_condition: 自定义条件
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 检查循环依赖
            if await self._has_circular_dependency(task_id, depends_on):
                self.logger.error(f"Circular dependency detected: {task_id} -> {depends_on}")
                return False
            
            # 创建依赖关系
            dependency = TaskDependency(
                task_id=task_id,
                depends_on=depends_on,
                dependency_type=dependency_type,
                condition=condition,
                custom_condition=custom_condition
            )
            
            # 添加到当前任务的依赖图
            if task_id not in self.dependency_graphs:
                self.dependency_graphs[task_id] = TaskDependencyGraph(task_id=task_id)
            
            self.dependency_graphs[task_id].add_dependency(dependency)
            
            # 添加到前置任务的依赖图
            if depends_on not in self.dependency_graphs:
                self.dependency_graphs[depends_on] = TaskDependencyGraph(task_id=depends_on)
            
            self.dependency_graphs[depends_on].add_dependent(task_id)
            
            self.logger.info(f"Dependency added: {task_id} depends on {depends_on} ({dependency_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding dependency: {e}")
            return False
    
    async def remove_dependency(self, task_id: str, depends_on: str) -> bool:
        """
        移除任务依赖关系
        
        Args:
            task_id: 当前任务ID
            depends_on: 依赖的任务ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if task_id not in self.dependency_graphs:
                return False
            
            graph = self.dependency_graphs[task_id]
            
            # 移除依赖
            graph.dependencies = [d for d in graph.dependencies if d.depends_on != depends_on]
            
            # 从前置任务的依赖图中移除
            if depends_on in self.dependency_graphs:
                self.dependency_graphs[depends_on].dependents.remove(task_id)
            
            self.logger.info(f"Dependency removed: {task_id} no longer depends on {depends_on}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing dependency: {e}")
            return False
    
    async def check_dependencies(self, task_id: str) -> Tuple[bool, List[str]]:
        """
        检查任务的依赖是否满足
        
        Args:
            task_id: 任务ID
            
        Returns:
            Tuple[bool, List[str]]: (是否满足所有依赖, 未满足的依赖列表)
        """
        try:
            if task_id not in self.dependency_graphs:
                return True, []
            
            graph = self.dependency_graphs[task_id]
            unsatisfied = []
            
            for dependency in graph.dependencies:
                satisfied = await self._check_single_dependency(dependency)
                
                if not satisfied:
                    unsatisfied.append(dependency.depends_on)
                    dependency.satisfied = False
                else:
                    dependency.satisfied = True
                    dependency.satisfied_at = datetime.now()
            
            all_satisfied = len(unsatisfied) == 0
            
            if all_satisfied:
                self.logger.debug(f"All dependencies satisfied for task {task_id}")
            else:
                self.logger.debug(f"Task {task_id} has unsatisfied dependencies: {unsatisfied}")
            
            return all_satisfied, unsatisfied
            
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {e}")
            return False, []
    
    async def mark_task_completed(self, task_id: str, success: bool = True,
                                 result: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        标记任务完成，并检查哪些任务的依赖现在满足
        
        Args:
            task_id: 任务ID
            success: 任务是否成功
            result: 任务结果
            
        Returns:
            List[str]: 现在可以执行的任务列表
        """
        try:
            # 更新任务状态缓存
            self.task_status_cache[task_id] = {
                "status": "completed",
                "success": success,
                "result": result,
                "completed_at": datetime.now()
            }
            
            # 获取依赖此任务的所有任务
            if task_id not in self.dependency_graphs:
                return []
            
            dependents = self.dependency_graphs[task_id].dependents
            ready_tasks = []
            
            # 检查每个依赖者的依赖是否满足
            for dependent_id in dependents:
                all_satisfied, _ = await self.check_dependencies(dependent_id)
                
                if all_satisfied:
                    ready_tasks.append(dependent_id)
                    self.logger.info(f"Task {dependent_id} is now ready to execute")
            
            return ready_tasks
            
        except Exception as e:
            self.logger.error(f"Error marking task completed: {e}")
            return []
    
    async def get_execution_order(self, task_ids: List[str]) -> Optional[List[str]]:
        """
        获取任务的执行顺序 (拓扑排序)
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            Optional[List[str]]: 排序后的任务列表，None表示存在循环依赖
        """
        try:
            # 构建依赖图
            in_degree = {task_id: 0 for task_id in task_ids}
            adjacency_list = {task_id: [] for task_id in task_ids}
            
            for task_id in task_ids:
                if task_id in self.dependency_graphs:
                    graph = self.dependency_graphs[task_id]
                    for dep in graph.dependencies:
                        if dep.depends_on in task_ids:
                            adjacency_list[dep.depends_on].append(task_id)
                            in_degree[task_id] += 1
            
            # 拓扑排序 (Kahn算法)
            queue = [task_id for task_id in task_ids if in_degree[task_id] == 0]
            result = []
            
            while queue:
                current = queue.pop(0)
                result.append(current)
                
                for neighbor in adjacency_list[current]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            # 检查是否存在循环依赖
            if len(result) != len(task_ids):
                self.logger.error("Circular dependency detected in task list")
                return None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting execution order: {e}")
            return None
    
    async def get_dependency_chain(self, task_id: str) -> List[str]:
        """
        获取任务的完整依赖链
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[str]: 依赖链（从最底层到当前任务）
        """
        try:
            chain = []
            visited = set()
            
            async def traverse(tid: str):
                if tid in visited:
                    return
                visited.add(tid)
                
                if tid in self.dependency_graphs:
                    graph = self.dependency_graphs[tid]
                    for dep in graph.dependencies:
                        await traverse(dep.depends_on)
                
                chain.append(tid)
            
            await traverse(task_id)
            return chain
            
        except Exception as e:
            self.logger.error(f"Error getting dependency chain: {e}")
            return []
    
    async def get_dependent_tasks(self, task_id: str, recursive: bool = True) -> List[str]:
        """
        获取依赖于指定任务的所有任务
        
        Args:
            task_id: 任务ID
            recursive: 是否递归获取
            
        Returns:
            List[str]: 依赖任务列表
        """
        try:
            dependents = []
            visited = set()
            
            async def traverse(tid: str):
                if tid in visited:
                    return
                visited.add(tid)
                
                if tid in self.dependency_graphs:
                    graph = self.dependency_graphs[tid]
                    for dependent_id in graph.dependents:
                        dependents.append(dependent_id)
                        if recursive:
                            await traverse(dependent_id)
            
            await traverse(task_id)
            return dependents
            
        except Exception as e:
            self.logger.error(f"Error getting dependent tasks: {e}")
            return []
    
    async def _check_single_dependency(self, dependency: TaskDependency) -> bool:
        """检查单个依赖是否满足"""
        try:
            # 获取前置任务的状态
            if dependency.depends_on not in self.task_status_cache:
                return False
            
            task_status = self.task_status_cache[dependency.depends_on]
            
            # 检查依赖条件
            if dependency.condition == DependencyCondition.SUCCESS:
                return task_status.get("status") == "completed" and task_status.get("success", False)
            elif dependency.condition == DependencyCondition.FAILURE:
                return task_status.get("status") == "completed" and not task_status.get("success", True)
            elif dependency.condition == DependencyCondition.ALWAYS:
                return task_status.get("status") == "completed"
            elif dependency.condition == DependencyCondition.CUSTOM:
                # 自定义条件评估
                return await self._evaluate_custom_condition(dependency, task_status)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking single dependency: {e}")
            return False
    
    async def _evaluate_custom_condition(self, dependency: TaskDependency,
                                        task_status: Dict[str, Any]) -> bool:
        """评估自定义条件"""
        try:
            if not dependency.custom_condition:
                return False
            
            # 简单的条件评估 (可以扩展为更复杂的表达式解析)
            # 示例: "result.status == 'success'"
            result = task_status.get("result", {})
            
            # 使用eval进行条件评估 (生产环境应使用更安全的方式)
            condition_context = {
                "result": result,
                "success": task_status.get("success", False),
                "status": task_status.get("status")
            }
            
            return eval(dependency.custom_condition, {"__builtins__": {}}, condition_context)
            
        except Exception as e:
            self.logger.error(f"Error evaluating custom condition: {e}")
            return False
    
    async def _has_circular_dependency(self, task_id: str, depends_on: str) -> bool:
        """检查是否存在循环依赖"""
        try:
            visited = set()
            
            async def has_path(current: str, target: str) -> bool:
                if current == target:
                    return True
                if current in visited:
                    return False
                
                visited.add(current)
                
                if current in self.dependency_graphs:
                    graph = self.dependency_graphs[current]
                    for dep in graph.dependencies:
                        if await has_path(dep.depends_on, target):
                            return True
                
                return False
            
            # 检查是否存在从depends_on到task_id的路径
            return await has_path(depends_on, task_id)
            
        except Exception as e:
            self.logger.error(f"Error checking circular dependency: {e}")
            return False
    
    def get_dependency_stats(self) -> Dict[str, Any]:
        """获取依赖关系统计信息"""
        total_tasks = len(self.dependency_graphs)
        total_dependencies = sum(len(graph.dependencies) for graph in self.dependency_graphs.values())
        
        dependency_types = {}
        for graph in self.dependency_graphs.values():
            for dep in graph.dependencies:
                dep_type = dep.dependency_type.value
                dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "total_dependencies": total_dependencies,
            "dependency_types": dependency_types,
            "tasks_with_dependencies": len([g for g in self.dependency_graphs.values() if g.dependencies])
        }


# 全局依赖管理器实例
dependency_manager = DependencyManager()

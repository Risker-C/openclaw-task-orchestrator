"""
OpenClaw Task Orchestrator - 任务管理API单元测试

测试基础任务管理API的CRUD操作和数据验证
"""

import pytest
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.main import TaskAPI
from src.core.task_manager import task_manager, TaskStatus, TaskPriority, TaskComplexity


class TestTaskAPI:
    """任务API测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清空任务管理器
        task_manager.tasks.clear()
    
    @pytest.mark.asyncio
    async def test_create_task_success(self):
        """测试成功创建任务"""
        result = await TaskAPI.create_task(
            title="测试任务",
            description="这是一个测试任务的描述",
            priority="high",
            complexity="L2"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "task_id" in result["data"]
        assert result["data"]["title"] == "测试任务"
        assert result["data"]["priority"] == "high"
        assert result["data"]["complexity"] == "L2"
        assert result["data"]["status"] == "ready"  # 手动指定复杂度时直接就绪
    
    @pytest.mark.asyncio
    async def test_create_task_validation_errors(self):
        """测试创建任务的验证错误"""
        # 空标题
        result = await TaskAPI.create_task("", "描述")
        assert result["success"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "title" in result["error"]
        
        # 空描述
        result = await TaskAPI.create_task("标题", "")
        assert result["success"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "description" in result["error"]
        
        # 标题过长
        long_title = "x" * 201
        result = await TaskAPI.create_task(long_title, "描述")
        assert result["success"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "too long" in result["error"]
        
        # 无效优先级
        result = await TaskAPI.create_task("标题", "描述", priority="invalid")
        assert result["success"] is False
        assert result["error_code"] == "INVALID_PRIORITY"
        
        # 无效复杂度
        result = await TaskAPI.create_task("标题", "描述", complexity="L4")
        assert result["success"] is False
        assert result["error_code"] == "INVALID_COMPLEXITY"
    
    @pytest.mark.asyncio
    async def test_get_task_success(self):
        """测试成功获取任务"""
        # 先创建一个任务
        create_result = await TaskAPI.create_task("测试任务", "测试描述")
        task_id = create_result["data"]["task_id"]
        
        # 获取任务
        result = await TaskAPI.get_task(task_id)
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["task_id"] == task_id
        assert result["data"]["title"] == "测试任务"
        assert result["data"]["description"] == "测试描述"
        assert "created_at" in result["data"]
        assert "updated_at" in result["data"]
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        """测试获取不存在的任务"""
        result = await TaskAPI.get_task("00000000-0000-0000-0000-000000000000")
        
        assert result["success"] is False
        assert result["error_code"] == "TASK_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_get_task_invalid_id(self):
        """测试无效的任务ID"""
        result = await TaskAPI.get_task("invalid-id")
        
        assert result["success"] is False
        assert result["error_code"] == "VALIDATION_ERROR"
        assert "Invalid task ID format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_task_success(self):
        """测试成功更新任务"""
        # 先创建一个任务
        create_result = await TaskAPI.create_task("原标题", "原描述")
        task_id = create_result["data"]["task_id"]
        
        # 更新任务
        result = await TaskAPI.update_task(
            task_id,
            title="新标题",
            description="新描述",
            priority="urgent"
        )
        
        assert result["success"] is True
        assert "data" in result
        assert "updated_fields" in result["data"]
        assert "title" in result["data"]["updated_fields"]
        assert "description" in result["data"]["updated_fields"]
        assert "priority" in result["data"]["updated_fields"]
        
        # 验证更新结果
        get_result = await TaskAPI.get_task(task_id)
        assert get_result["data"]["title"] == "新标题"
        assert get_result["data"]["description"] == "新描述"
        assert get_result["data"]["priority"] == "urgent"
    
    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """测试更新任务状态"""
        # 先创建一个任务
        create_result = await TaskAPI.create_task("测试任务", "测试描述")
        task_id = create_result["data"]["task_id"]
        
        # 更新状态和进度
        result = await TaskAPI.update_task(
            task_id,
            status="running",
            progress=50
        )
        
        assert result["success"] is True
        assert "status" in result["data"]["updated_fields"]
        assert "progress" in result["data"]["updated_fields"]
        
        # 验证更新结果
        get_result = await TaskAPI.get_task(task_id)
        assert get_result["data"]["status"] == "running"
        assert get_result["data"]["progress"] == 50
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self):
        """测试成功删除任务"""
        # 先创建一个任务
        create_result = await TaskAPI.create_task("待删除任务", "测试描述")
        task_id = create_result["data"]["task_id"]
        
        # 删除任务
        result = await TaskAPI.delete_task(task_id)
        
        assert result["success"] is True
        assert result["data"]["task_id"] == task_id
        assert "deleted_at" in result["data"]
        
        # 验证任务已删除
        get_result = await TaskAPI.get_task(task_id)
        assert get_result["success"] is False
        assert get_result["error_code"] == "TASK_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_delete_running_task(self):
        """测试删除运行中的任务（应该失败）"""
        # 先创建一个任务并设置为运行状态
        create_result = await TaskAPI.create_task("运行中任务", "测试描述")
        task_id = create_result["data"]["task_id"]
        
        # 设置为运行状态
        await TaskAPI.update_task(task_id, status="running")
        
        # 尝试删除（应该失败）
        result = await TaskAPI.delete_task(task_id)
        
        assert result["success"] is False
        assert result["error_code"] == "TASK_RUNNING"
        assert "Cannot delete running task" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self):
        """测试成功列出任务"""
        # 创建多个任务
        await TaskAPI.create_task("任务1", "描述1", priority="high", complexity="L1")
        await TaskAPI.create_task("任务2", "描述2", priority="medium", complexity="L2")
        await TaskAPI.create_task("任务3", "描述3", priority="low", complexity="L3")
        
        # 列出所有任务
        result = await TaskAPI.list_tasks()
        
        assert result["success"] is True
        assert "data" in result
        assert "tasks" in result["data"]
        assert "pagination" in result["data"]
        assert len(result["data"]["tasks"]) == 3
        assert result["data"]["pagination"]["total"] == 3
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self):
        """测试带过滤条件的任务列表"""
        # 创建不同类型的任务
        await TaskAPI.create_task("高优先级任务", "描述", priority="high", complexity="L1")
        await TaskAPI.create_task("中优先级任务", "描述", priority="medium", complexity="L2")
        await TaskAPI.create_task("低优先级任务", "描述", priority="low", complexity="L3")
        
        # 按优先级过滤
        result = await TaskAPI.list_tasks(priority="high")
        assert result["success"] is True
        assert len(result["data"]["tasks"]) == 1
        assert result["data"]["tasks"][0]["priority"] == "high"
        
        # 按复杂度过滤
        result = await TaskAPI.list_tasks(complexity="L2")
        assert result["success"] is True
        assert len(result["data"]["tasks"]) == 1
        assert result["data"]["tasks"][0]["complexity"] == "L2"
    
    @pytest.mark.asyncio
    async def test_list_tasks_pagination(self):
        """测试任务列表分页"""
        # 创建5个任务
        for i in range(5):
            await TaskAPI.create_task(f"任务{i+1}", f"描述{i+1}")
        
        # 测试分页
        result = await TaskAPI.list_tasks(limit=2, offset=0)
        assert result["success"] is True
        assert len(result["data"]["tasks"]) == 2
        assert result["data"]["pagination"]["total"] == 5
        assert result["data"]["pagination"]["has_more"] is True
        
        # 测试第二页
        result = await TaskAPI.list_tasks(limit=2, offset=2)
        assert result["success"] is True
        assert len(result["data"]["tasks"]) == 2
        assert result["data"]["pagination"]["has_more"] is True
        
        # 测试最后一页
        result = await TaskAPI.list_tasks(limit=2, offset=4)
        assert result["success"] is True
        assert len(result["data"]["tasks"]) == 1
        assert result["data"]["pagination"]["has_more"] is False
    
    @pytest.mark.asyncio
    async def test_list_tasks_invalid_parameters(self):
        """测试无效的列表参数"""
        # 无效的limit
        result = await TaskAPI.list_tasks(limit=0)
        assert result["success"] is False
        assert result["error_code"] == "INVALID_LIMIT"
        
        result = await TaskAPI.list_tasks(limit=1001)
        assert result["success"] is False
        assert result["error_code"] == "INVALID_LIMIT"
        
        # 无效的offset
        result = await TaskAPI.list_tasks(offset=-1)
        assert result["success"] is False
        assert result["error_code"] == "INVALID_OFFSET"
        
        # 无效的过滤参数
        result = await TaskAPI.list_tasks(status="invalid")
        assert result["success"] is False
        assert result["error_code"] == "INVALID_STATUS"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
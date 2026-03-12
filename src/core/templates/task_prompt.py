"""
Task Prompt Templates - 标准化任务提示词模板
"""

from typing import Dict, Any, Optional
from string import Template


class TaskPromptTemplate:
    """任务提示词模板类"""
    
    SYSTEM_PROMPT_BASE = Template("""你是一个专业的 OpenClaw Agent (ID: $agent_id)。
当前工作空间路径: $workspace_root
任务复杂度级别: $complexity

你的核心职责是高效、准确地完成分配给你的任务。
请严格遵守以下操作原则：
1. **预检先行**：在执行任何文件操作或工具调用前，先确认路径是否存在及权限是否正确。
2. **原子化操作**：将复杂任务分解为可控的小步骤，每步执行后验证结果。
3. **鲁棒性处理**：处理可能的工具超时或 API 错误，必要时进行重试。
4. **结果导向**：最终输出应直接回答任务需求，并提供清晰的执行总结。

$additional_instructions
""")

    USER_PROMPT_TEMPLATE = Template("""### 任务详情
任务 ID: $task_id
任务标题: $title
任务描述: $description

### 执行上下文
$context_info

### 交付要求
1. 完成上述任务描述中的所有要求。
2. 在工作空间中生成必要的产物文档。
3. 返回包含执行总结和产物路径的 JSON 结果。

请开始执行。
""")

    @classmethod
    def generate_prompts(cls, agent_id: str, task_id: str, title: str, 
                         description: str, complexity: str, 
                         workspace_root: str, context_info: str = "",
                         additional_instructions: str = "") -> Dict[str, str]:
        """生成系统提示词和用户提示词"""
        system_prompt = cls.SYSTEM_PROMPT_BASE.substitute(
            agent_id=agent_id,
            workspace_root=workspace_root,
            complexity=complexity,
            additional_instructions=additional_instructions
        )
        
        user_prompt = cls.USER_PROMPT_TEMPLATE.substitute(
            task_id=task_id,
            title=title,
            description=description,
            context_info=context_info
        )
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }

# 单例
task_prompt_template = TaskPromptTemplate()

"""
智能复杂度判断器 - 基于Magi项目的L1/L2/L3三级分流机制

参考Magi项目的智能复杂度判断，结合任务描述、历史数据、关键词分析等
实现自动化的任务复杂度分级，避免算力浪费，提高执行效率
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from .task_manager import TaskComplexity, Task


@dataclass
class ComplexityIndicator:
    """复杂度指标"""
    keyword_score: float = 0.0      # 关键词得分
    length_score: float = 0.0       # 长度得分  
    structure_score: float = 0.0    # 结构复杂度得分
    domain_score: float = 0.0       # 领域专业度得分
    dependency_score: float = 0.0   # 依赖关系得分
    
    @property
    def total_score(self) -> float:
        """总得分"""
        return (self.keyword_score * 0.3 + 
                self.length_score * 0.2 + 
                self.structure_score * 0.2 + 
                self.domain_score * 0.2 + 
                self.dependency_score * 0.1)


class ComplexityAnalyzer:
    """复杂度分析器 - 智能判断任务复杂度"""
    
    def __init__(self):
        # L1简单任务关键词（直接执行）
        self.l1_keywords = {
            "查询": 2.0, "搜索": 2.0, "获取": 1.5, "读取": 1.5,
            "列出": 1.5, "显示": 1.0, "查看": 1.0, "检查": 1.0,
            "简单": 1.5, "快速": 1.0, "基础": 1.0
        }
        
        # L2单步任务关键词（专业Agent）
        self.l2_keywords = {
            "分析": 3.0, "研究": 3.0, "评估": 2.5, "审查": 2.5,
            "总结": 2.0, "整理": 2.0, "编写": 2.5, "生成": 2.0,
            "优化": 2.5, "改进": 2.0, "测试": 2.0, "验证": 2.0,
            "方案": 2.5, "报告": 2.0, "文档": 2.0
        }
        
        # L3复杂任务关键词（多Agent协作）
        self.l3_keywords = {
            "设计": 4.0, "架构": 4.5, "系统": 3.5, "框架": 3.5,
            "开发": 3.0, "构建": 3.0, "实现": 3.0, "部署": 2.5,
            "集成": 3.0, "协作": 3.5, "编排": 4.0, "管理": 2.5,
            "多轮": 4.0, "迭代": 3.5, "阶段": 3.0, "流程": 3.0,
            "完整": 3.0, "全面": 3.0, "深度": 3.5, "复杂": 4.0
        }
        
        # 专业领域关键词
        self.domain_keywords = {
            # 技术领域
            "算法": 3.0, "数据结构": 3.5, "机器学习": 4.0, "AI": 3.5,
            "数据库": 3.0, "网络": 3.0, "安全": 3.5, "性能": 3.0,
            "API": 2.5, "接口": 2.5, "协议": 3.0, "标准": 3.0,
            
            # 业务领域  
            "业务": 2.5, "流程": 3.0, "规范": 3.0, "策略": 3.5,
            "运营": 3.0, "管理": 2.5, "监控": 3.0, "治理": 3.5
        }
        
        # 结构复杂度模式
        self.structure_patterns = [
            (r"第[一二三四五六七八九十\d]+[步阶段部分]", 2.0),  # 多步骤
            (r"[1-9]\d*[\.、]\s*", 1.5),                    # 编号列表
            (r"包括|涉及|需要.*?和.*?", 1.5),                # 多项要求
            (r"同时|并且|以及", 1.0),                        # 并列关系
            (r"然后|接着|最后", 1.0),                        # 顺序关系
        ]
    
    async def analyze_complexity(self, task: Task, 
                                manual_override: Optional[TaskComplexity] = None) -> TaskComplexity:
        """
        分析任务复杂度
        
        Args:
            task: 任务对象
            manual_override: 手动指定复杂度（可选）
            
        Returns:
            TaskComplexity: 判断的复杂度级别
        """
        # 如果手动指定了复杂度，需要二次确认
        if manual_override:
            auto_complexity = await self._auto_analyze(task)
            if await self._confirm_manual_override(task, manual_override, auto_complexity):
                return manual_override
            else:
                return auto_complexity
        
        # 自动分析复杂度
        return await self._auto_analyze(task)
    
    async def _auto_analyze(self, task: Task) -> TaskComplexity:
        """自动分析任务复杂度"""
        indicator = ComplexityIndicator()
        
        # 分析任务描述
        text = f"{task.title} {task.description}".lower()
        
        # 1. 关键词分析
        indicator.keyword_score = self._analyze_keywords(text)
        
        # 2. 长度分析
        indicator.length_score = self._analyze_length(text)
        
        # 3. 结构复杂度分析
        indicator.structure_score = self._analyze_structure(text)
        
        # 4. 领域专业度分析
        indicator.domain_score = self._analyze_domain(text)
        
        # 5. 依赖关系分析
        indicator.dependency_score = self._analyze_dependencies(text)
        
        # 根据总得分判断复杂度
        total_score = indicator.total_score
        
        if total_score >= 3.5:
            return TaskComplexity.L3_COMPLEX
        elif total_score >= 2.0:
            return TaskComplexity.L2_SINGLE
        else:
            return TaskComplexity.L1_SIMPLE
    
    def _analyze_keywords(self, text: str) -> float:
        """分析关键词得分"""
        l1_score = sum(weight for keyword, weight in self.l1_keywords.items() 
                      if keyword in text)
        l2_score = sum(weight for keyword, weight in self.l2_keywords.items() 
                      if keyword in text)
        l3_score = sum(weight for keyword, weight in self.l3_keywords.items() 
                      if keyword in text)
        
        # 归一化处理，避免关键词堆积
        max_score = max(l1_score, l2_score, l3_score)
        if max_score == 0:
            return 1.0  # 默认分数
        
        # L3得分最高返回高分，L1得分最高返回低分
        if l3_score == max_score:
            return min(4.0, l3_score * 0.8)
        elif l2_score == max_score:
            return min(3.0, l2_score * 0.6)
        else:
            return min(2.0, l1_score * 0.4)
    
    def _analyze_length(self, text: str) -> float:
        """分析文本长度得分"""
        length = len(text)
        
        if length > 1000:
            return 4.0
        elif length > 500:
            return 3.0
        elif length > 200:
            return 2.0
        elif length > 50:
            return 1.5
        else:
            return 1.0
    
    def _analyze_structure(self, text: str) -> float:
        """分析结构复杂度得分"""
        score = 1.0
        
        for pattern, weight in self.structure_patterns:
            matches = re.findall(pattern, text)
            if matches:
                score += len(matches) * weight * 0.3
        
        return min(4.0, score)
    
    def _analyze_domain(self, text: str) -> float:
        """分析领域专业度得分"""
        domain_score = sum(weight for keyword, weight in self.domain_keywords.items() 
                          if keyword in text)
        
        return min(4.0, domain_score * 0.5)
    
    def _analyze_dependencies(self, text: str) -> float:
        """分析依赖关系得分"""
        dependency_patterns = [
            r"依赖|基于|需要.*?完成",
            r"前置|先.*?再",
            r"集成|结合|配合",
            r"多.*?协作|团队|配合"
        ]
        
        score = 1.0
        for pattern in dependency_patterns:
            if re.search(pattern, text):
                score += 0.5
        
        return min(4.0, score)
    
    async def _confirm_manual_override(self, task: Task, 
                                     manual_complexity: TaskComplexity,
                                     auto_complexity: TaskComplexity) -> bool:
        """
        确认手动指定的复杂度
        
        Args:
            task: 任务对象
            manual_complexity: 手动指定的复杂度
            auto_complexity: 自动分析的复杂度
            
        Returns:
            bool: 是否确认使用手动指定的复杂度
        """
        # 如果手动指定与自动分析一致，直接确认
        if manual_complexity == auto_complexity:
            return True
        
        # 如果差异较大，需要二次确认
        complexity_levels = {
            TaskComplexity.L1_SIMPLE: 1,
            TaskComplexity.L2_SINGLE: 2, 
            TaskComplexity.L3_COMPLEX: 3
        }
        
        manual_level = complexity_levels[manual_complexity]
        auto_level = complexity_levels[auto_complexity]
        
        # 如果差异超过1级，需要确认
        if abs(manual_level - auto_level) > 1:
            # TODO: 这里应该发送确认消息到飞书，等待用户确认
            # 暂时返回True，表示接受手动指定
            return True
        
        return True
    
    def get_complexity_explanation(self, task: Task, complexity: TaskComplexity) -> str:
        """获取复杂度判断的解释说明"""
        explanations = {
            TaskComplexity.L1_SIMPLE: "简单任务，可由单个Agent直接执行，预计5-10分钟完成",
            TaskComplexity.L2_SINGLE: "单步任务，需要专业Agent处理，预计30-60分钟完成", 
            TaskComplexity.L3_COMPLEX: "复杂任务，需要多Agent协作，分阶段执行，预计2-4小时完成"
        }
        
        return explanations.get(complexity, "未知复杂度")


# 全局复杂度分析器实例
complexity_analyzer = ComplexityAnalyzer()
"""
智能复杂度判断器 - 基于Magi项目的L1/L2/L3三级分流机制

参考Magi项目的智能复杂度判断，结合任务描述、历史数据、关键词分析等
实现自动化的任务复杂度分级，避免算力浪费，提高执行效率
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

from .task_manager import TaskComplexity, Task


@dataclass
class ComplexityIndicator:
    """复杂度指标"""
    keyword_score: float = 0.0      # 关键词得分
    length_score: float = 0.0       # 长度得分  
    structure_score: float = 0.0    # 结构复杂度得分
    domain_score: float = 0.0       # 领域专业度得分
    dependency_score: float = 0.0   # 依赖关系得分
    context_score: float = 0.0      # 上下文复杂度得分
    
    @property
    def total_score(self) -> float:
        """总得分 - 优化权重分配，增加关键词和领域权重"""
        return (self.keyword_score * 0.35 + 
                self.length_score * 0.10 + 
                self.structure_score * 0.15 + 
                self.domain_score * 0.25 + 
                self.dependency_score * 0.10 +
                self.context_score * 0.05)


@dataclass
class ComplexityExplanation:
    """复杂度判断解释"""
    complexity: TaskComplexity
    confidence: float
    reasons: List[str]
    indicators: ComplexityIndicator
    suggestions: List[str]
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "complexity": self.complexity.value,
            "confidence": round(self.confidence, 2),
            "reasons": self.reasons,
            "indicators": {
                "keyword_score": round(self.indicators.keyword_score, 2),
                "length_score": round(self.indicators.length_score, 2),
                "structure_score": round(self.indicators.structure_score, 2),
                "domain_score": round(self.indicators.domain_score, 2),
                "dependency_score": round(self.indicators.dependency_score, 2),
                "context_score": round(self.indicators.context_score, 2),
                "total_score": round(self.indicators.total_score, 2)
            },
            "suggestions": self.suggestions
        }


class ComplexityAnalyzer:
    """复杂度分析器 - 智能判断任务复杂度"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 扩展的L1简单任务关键词（直接执行）
        self.l1_keywords = {
            # 查询类
            "查询": 2.0, "搜索": 2.0, "获取": 1.5, "读取": 1.5, "查找": 1.8,
            "列出": 1.5, "显示": 1.0, "查看": 1.0, "检查": 1.0, "浏览": 1.2,
            
            # 简单操作
            "简单": 1.5, "快速": 1.0, "基础": 1.0, "直接": 1.2, "立即": 1.3,
            "复制": 1.0, "粘贴": 1.0, "下载": 1.2, "上传": 1.2, "保存": 1.0,
            
            # 状态检查
            "状态": 1.3, "情况": 1.2, "信息": 1.0, "数据": 1.2, "结果": 1.0,
            "统计": 1.5, "计数": 1.3, "汇总": 1.4
        }
        
        # 扩展的L2单步任务关键词（专业Agent）
        self.l2_keywords = {
            # 分析类
            "分析": 3.0, "研究": 3.0, "评估": 2.5, "审查": 2.5, "调研": 2.8,
            "诊断": 2.7, "识别": 2.3, "判断": 2.4, "比较": 2.2, "对比": 2.2,
            
            # 创作类
            "总结": 2.0, "整理": 2.0, "编写": 2.5, "生成": 2.0, "创建": 2.3,
            "制作": 2.2, "撰写": 2.4, "起草": 2.1, "草拟": 2.1, "拟定": 2.2,
            
            # 优化类
            "优化": 2.5, "改进": 2.0, "完善": 2.3, "增强": 2.2, "提升": 2.1,
            "修复": 2.4, "调整": 2.0, "修改": 1.9, "更新": 1.8, "升级": 2.1,
            
            # 验证类
            "测试": 2.0, "验证": 2.0, "检验": 2.1, "确认": 1.8, "校验": 2.0,
            
            # 文档类
            "方案": 2.5, "报告": 2.0, "文档": 2.0, "说明": 1.9, "手册": 2.1,
            "指南": 2.2, "教程": 2.3, "演示": 2.0
        }
        
        # 扩展的L3复杂任务关键词（多Agent协作）
        self.l3_keywords = {
            # 设计类
            "设计": 4.0, "架构": 4.5, "规划": 3.8, "策划": 3.5, "构思": 3.2,
            "建模": 3.6, "原型": 3.3, "蓝图": 3.7, "方案设计": 4.2,
            
            # 系统类
            "系统": 3.5, "框架": 3.5, "平台": 3.4, "基础设施": 3.8, "生态": 3.6,
            "环境": 3.0, "工具链": 3.3, "流水线": 3.4, "管道": 3.1,
            
            # 开发类
            "开发": 3.0, "构建": 3.0, "实现": 3.0, "部署": 2.5, "发布": 2.3,
            "上线": 2.4, "交付": 2.6, "投产": 2.7, "落地": 2.8,
            
            # 集成类
            "集成": 3.0, "整合": 3.2, "融合": 3.1, "对接": 2.8, "连接": 2.6,
            "协作": 3.5, "编排": 4.0, "调度": 3.3, "协调": 3.1,
            
            # 管理类
            "管理": 2.5, "治理": 3.2, "监控": 2.8, "运维": 2.9, "运营": 2.7,
            
            # 复杂度指示词
            "多轮": 4.0, "迭代": 3.5, "阶段": 3.0, "流程": 3.0, "工作流": 3.4,
            "完整": 3.0, "全面": 3.0, "深度": 3.5, "复杂": 4.0, "综合": 3.3,
            "端到端": 3.8, "全链路": 3.9, "一体化": 3.6
        }
        
        # 扩展的专业领域关键词
        self.domain_keywords = {
            # 技术领域
            "算法": 3.0, "数据结构": 3.5, "机器学习": 4.0, "AI": 3.5, "人工智能": 4.0,
            "深度学习": 4.2, "神经网络": 4.0, "大模型": 4.1, "LLM": 3.8,
            "数据库": 3.0, "SQL": 2.5, "NoSQL": 2.8, "缓存": 2.6, "存储": 2.7,
            "网络": 3.0, "协议": 3.0, "TCP": 2.8, "HTTP": 2.5, "WebSocket": 2.9,
            "安全": 3.5, "加密": 3.2, "认证": 2.9, "授权": 2.8, "防护": 3.1,
            "性能": 3.0, "优化": 2.8, "并发": 3.2, "异步": 3.1, "分布式": 3.8,
            "微服务": 3.6, "容器": 3.2, "Docker": 2.9, "Kubernetes": 3.4,
            "云原生": 3.7, "DevOps": 3.3, "CI/CD": 3.1,
            
            # API和接口
            "API": 2.5, "接口": 2.5, "REST": 2.6, "GraphQL": 3.0, "RPC": 2.8,
            "SDK": 2.7, "库": 2.3, "框架": 2.8, "中间件": 3.0,
            
            # 前端技术
            "前端": 2.8, "React": 2.6, "Vue": 2.6, "Angular": 2.7, "JavaScript": 2.5,
            "TypeScript": 2.7, "CSS": 2.2, "HTML": 2.0, "UI": 2.4, "UX": 2.6,
            
            # 后端技术
            "后端": 2.8, "服务器": 2.6, "数据库": 2.8, "缓存": 2.5, "队列": 2.7,
            "消息": 2.6, "事件": 2.5, "流": 2.8, "批处理": 2.9,
            
            # 业务领域  
            "业务": 2.5, "流程": 3.0, "规范": 3.0, "策略": 3.5, "规则": 2.8,
            "运营": 3.0, "管理": 2.5, "监控": 3.0, "治理": 3.5, "合规": 3.2,
            "风控": 3.4, "审计": 3.1, "财务": 2.9, "人事": 2.7,
            
            # 数据领域
            "数据": 2.5, "分析": 2.8, "挖掘": 3.2, "建模": 3.4, "预测": 3.3,
            "统计": 2.9, "报表": 2.6, "可视化": 2.8, "仪表盘": 2.7,
            "ETL": 3.1, "数据仓库": 3.3, "数据湖": 3.4, "大数据": 3.6
        }
        
        # 扩展的结构复杂度模式
        self.structure_patterns = [
            # 多步骤标识
            (r"第[一二三四五六七八九十\d]+[步阶段部分章节]", 2.0),
            (r"步骤[一二三四五六七八九十\d]+", 1.8),
            (r"[1-9]\d*[\.、]\s*", 1.5),
            (r"[一二三四五六七八九十][\.、]\s*", 1.6),
            
            # 多项要求
            (r"包括|涉及|需要.*?和.*?", 1.5),
            (r"包含.*?、.*?、", 1.4),
            (r"具备.*?和.*?", 1.3),
            
            # 并列关系
            (r"同时|并且|以及|还要|另外", 1.0),
            (r"既要.*?又要", 1.8),
            (r"不仅.*?还要", 1.7),
            
            # 顺序关系
            (r"然后|接着|最后|随后|之后", 1.0),
            (r"首先.*?然后.*?最后", 2.2),
            (r"先.*?再.*?后", 2.0),
            
            # 条件关系
            (r"如果.*?则", 1.6),
            (r"当.*?时", 1.4),
            (r"基于.*?进行", 1.5),
            
            # 范围限定
            (r"全部|所有|整个|完整", 1.3),
            (r"各种|多种|不同", 1.2),
            (r"各个|每个|逐一", 1.4)
        ]
        
        # 上下文复杂度关键词
        self.context_keywords = {
            "历史": 1.5, "背景": 1.3, "现状": 1.2, "环境": 1.4,
            "依赖": 2.0, "关联": 1.8, "影响": 1.6, "约束": 1.7,
            "兼容": 1.9, "适配": 1.8, "迁移": 2.1, "升级": 1.7
        }
        
        # 阈值配置 - 调整后的分级标准
        self.thresholds = {
            "l3_min": 2.8,  # L3最低阈值（进一步降低）
            "l2_min": 1.6,  # L2最低阈值（进一步降低）
            "confidence_high": 0.8,  # 高置信度阈值
            "confidence_medium": 0.6  # 中等置信度阈值
        }
    
    async def analyze_complexity(self, task: Task, 
                                manual_override: Optional[TaskComplexity] = None) -> Tuple[TaskComplexity, ComplexityExplanation]:
        """
        分析任务复杂度 - 返回复杂度和详细解释
        
        Args:
            task: 任务对象
            manual_override: 手动指定复杂度（可选）
            
        Returns:
            Tuple[TaskComplexity, ComplexityExplanation]: 复杂度级别和详细解释
        """
        # 自动分析复杂度
        auto_complexity, explanation = await self._auto_analyze_with_explanation(task)
        
        # 如果手动指定了复杂度，需要二次确认
        if manual_override:
            confirmed = await self._confirm_manual_override(task, manual_override, auto_complexity, explanation)
            if confirmed:
                # 更新解释信息
                explanation.complexity = manual_override
                explanation.reasons.insert(0, f"手动指定复杂度为 {manual_override.value}")
                explanation.suggestions.append("已采用手动指定的复杂度级别")
                return manual_override, explanation
        
        return auto_complexity, explanation
    
    async def _auto_analyze_with_explanation(self, task: Task) -> Tuple[TaskComplexity, ComplexityExplanation]:
        """自动分析任务复杂度并生成详细解释"""
        indicator = ComplexityIndicator()
        reasons = []
        suggestions = []
        
        # 分析任务描述
        text = f"{task.title} {task.description}".lower()
        
        # 1. 关键词分析
        indicator.keyword_score, keyword_reasons = self._analyze_keywords_detailed(text)
        reasons.extend(keyword_reasons)
        
        # 2. 长度分析
        indicator.length_score, length_reason = self._analyze_length_detailed(text)
        if length_reason:
            reasons.append(length_reason)
        
        # 3. 结构复杂度分析
        indicator.structure_score, structure_reasons = self._analyze_structure_detailed(text)
        reasons.extend(structure_reasons)
        
        # 4. 领域专业度分析
        indicator.domain_score, domain_reasons = self._analyze_domain_detailed(text)
        reasons.extend(domain_reasons)
        
        # 5. 依赖关系分析
        indicator.dependency_score, dependency_reasons = self._analyze_dependencies_detailed(text)
        reasons.extend(dependency_reasons)
        
        # 6. 上下文复杂度分析
        indicator.context_score, context_reasons = self._analyze_context_detailed(text)
        reasons.extend(context_reasons)
        
        # 根据总得分判断复杂度
        total_score = indicator.total_score
        
        if total_score >= self.thresholds["l3_min"]:
            complexity = TaskComplexity.L3_COMPLEX
            confidence = min(0.95, (total_score - self.thresholds["l3_min"]) / 2 + 0.7)
            suggestions.extend([
                "建议分配多个专业Agent协作处理",
                "可考虑分阶段执行，降低单次执行复杂度",
                "预留充足的执行时间和资源"
            ])
        elif total_score >= self.thresholds["l2_min"]:
            complexity = TaskComplexity.L2_SINGLE
            confidence = min(0.9, (total_score - self.thresholds["l2_min"]) / 1.4 + 0.6)
            suggestions.extend([
                "建议分配专业Agent处理",
                "可能需要专业领域知识",
                "预计执行时间30-60分钟"
            ])
        else:
            complexity = TaskComplexity.L1_SIMPLE
            confidence = min(0.85, (self.thresholds["l2_min"] - total_score) / 1.8 + 0.5)
            suggestions.extend([
                "可由通用Agent直接处理",
                "预计快速完成",
                "适合立即执行"
            ])
        
        # 添加总体评估原因
        reasons.insert(0, f"综合得分 {total_score:.2f}，判定为 {complexity.value} 级别")
        
        explanation = ComplexityExplanation(
            complexity=complexity,
            confidence=confidence,
            reasons=reasons,
            indicators=indicator,
            suggestions=suggestions
        )
        
        return complexity, explanation
    
    def _analyze_keywords_detailed(self, text: str) -> Tuple[float, List[str]]:
        """详细分析关键词得分"""
        reasons = []
        
        # 计算各级别关键词得分
        l1_matches = [(kw, weight) for kw, weight in self.l1_keywords.items() if kw in text]
        l2_matches = [(kw, weight) for kw, weight in self.l2_keywords.items() if kw in text]
        l3_matches = [(kw, weight) for kw, weight in self.l3_keywords.items() if kw in text]
        
        l1_score = sum(weight for _, weight in l1_matches)
        l2_score = sum(weight for _, weight in l2_matches)
        l3_score = sum(weight for _, weight in l3_matches)
        
        # 记录匹配的关键词
        if l1_matches:
            reasons.append(f"包含L1关键词: {', '.join([kw for kw, _ in l1_matches[:3]])}")
        if l2_matches:
            reasons.append(f"包含L2关键词: {', '.join([kw for kw, _ in l2_matches[:3]])}")
        if l3_matches:
            reasons.append(f"包含L3关键词: {', '.join([kw for kw, _ in l3_matches[:3]])}")
        
        # 归一化处理，避免关键词堆积
        max_score = max(l1_score, l2_score, l3_score)
        if max_score == 0:
            reasons.append("未匹配到特定关键词，使用默认评分")
            return 1.0, reasons
        
        # 根据最高得分类别确定分数 - 调整系数提高L3识别
        if l3_score == max_score:
            score = min(4.0, l3_score * 0.9)  # 提高L3系数
            reasons.append(f"L3关键词得分最高 ({l3_score:.1f})，倾向复杂任务")
        elif l2_score == max_score:
            score = min(3.0, l2_score * 0.7)  # 提高L2系数
            reasons.append(f"L2关键词得分最高 ({l2_score:.1f})，倾向单步任务")
        else:
            score = min(2.0, l1_score * 0.3)
            reasons.append(f"L1关键词得分最高 ({l1_score:.1f})，倾向简单任务")
        
        return score, reasons
    
    def _analyze_length_detailed(self, text: str) -> Tuple[float, Optional[str]]:
        """详细分析文本长度得分"""
        length = len(text)
        
        if length > 1000:
            return 4.0, f"文本长度 {length} 字符，属于长文本，通常涉及复杂需求"
        elif length > 500:
            return 3.0, f"文本长度 {length} 字符，属于中长文本，可能需要专业处理"
        elif length > 200:
            return 2.0, f"文本长度 {length} 字符，属于中等文本"
        elif length > 50:
            return 1.5, f"文本长度 {length} 字符，属于短文本"
        else:
            return 1.0, f"文本长度 {length} 字符，属于极短文本，通常为简单任务"
    
    def _analyze_structure_detailed(self, text: str) -> Tuple[float, List[str]]:
        """详细分析结构复杂度得分"""
        reasons = []
        score = 1.0
        
        for pattern, weight in self.structure_patterns:
            matches = re.findall(pattern, text)
            if matches:
                match_count = len(matches)
                added_score = match_count * weight * 0.3
                score += added_score
                
                if "步骤" in pattern or "阶段" in pattern:
                    reasons.append(f"检测到 {match_count} 个步骤/阶段标识，增加结构复杂度")
                elif "包括|涉及" in pattern:
                    reasons.append(f"检测到 {match_count} 个多项要求，增加任务复杂度")
                elif "同时|并且" in pattern:
                    reasons.append(f"检测到 {match_count} 个并列关系，任务有多个维度")
                elif "然后|接着" in pattern:
                    reasons.append(f"检测到 {match_count} 个顺序关系，任务有先后依赖")
        
        final_score = min(4.0, score)
        if final_score > 2.5:
            reasons.append(f"结构复杂度较高 ({final_score:.1f})，任务结构复杂")
        elif final_score > 1.5:
            reasons.append(f"结构复杂度中等 ({final_score:.1f})，任务有一定结构")
        
        return final_score, reasons
    
    def _analyze_domain_detailed(self, text: str) -> Tuple[float, List[str]]:
        """详细分析领域专业度得分"""
        reasons = []
        matched_domains = []
        
        domain_score = 0
        for keyword, weight in self.domain_keywords.items():
            if keyword in text:
                domain_score += weight
                matched_domains.append((keyword, weight))
        
        if matched_domains:
            # 按权重排序，取前3个
            top_domains = sorted(matched_domains, key=lambda x: x[1], reverse=True)[:3]
            domain_names = [kw for kw, _ in top_domains]
            reasons.append(f"涉及专业领域: {', '.join(domain_names)}")
            
            final_score = min(4.0, domain_score * 0.4)  # 调整系数
            if final_score > 3.0:
                reasons.append("专业度很高，需要深度专业知识")
            elif final_score > 2.0:
                reasons.append("有一定专业度，需要相关领域知识")
            else:
                reasons.append("专业度较低，通用知识可处理")
        else:
            final_score = 1.0
            reasons.append("未检测到特定专业领域")
        
        return final_score, reasons
    
    def _analyze_dependencies_detailed(self, text: str) -> Tuple[float, List[str]]:
        """详细分析依赖关系得分"""
        reasons = []
        score = 1.0
        
        dependency_patterns = [
            (r"依赖|基于|需要.*?完成", "外部依赖"),
            (r"前置|先.*?再", "顺序依赖"),
            (r"集成|结合|配合", "系统集成"),
            (r"多.*?协作|团队|配合", "协作依赖"),
            (r"同步|异步|并行", "执行依赖"),
            (r"兼容|适配|迁移", "兼容性依赖")
        ]
        
        found_dependencies = []
        for pattern, dep_type in dependency_patterns:
            if re.search(pattern, text):
                score += 0.4
                found_dependencies.append(dep_type)
        
        if found_dependencies:
            reasons.append(f"检测到依赖关系: {', '.join(found_dependencies)}")
            final_score = min(4.0, score)
            if final_score > 3.0:
                reasons.append("依赖关系复杂，需要协调多个组件")
            elif final_score > 2.0:
                reasons.append("存在一定依赖关系，需要考虑协调")
        else:
            final_score = 1.0
            reasons.append("依赖关系简单，可独立执行")
        
        return final_score, reasons
    
    def _analyze_context_detailed(self, text: str) -> Tuple[float, List[str]]:
        """详细分析上下文复杂度得分"""
        reasons = []
        score = 1.0
        
        matched_contexts = []
        for keyword, weight in self.context_keywords.items():
            if keyword in text:
                score += weight * 0.3
                matched_contexts.append(keyword)
        
        if matched_contexts:
            reasons.append(f"涉及上下文因素: {', '.join(matched_contexts[:3])}")
            final_score = min(4.0, score)
            if final_score > 2.5:
                reasons.append("上下文复杂，需要考虑历史和环境因素")
        else:
            final_score = 1.0
        
        return final_score, reasons
    
    async def _confirm_manual_override(self, task: Task, 
                                     manual_complexity: TaskComplexity,
                                     auto_complexity: TaskComplexity,
                                     explanation: ComplexityExplanation) -> bool:
        """
        确认手动指定的复杂度 - 增强版
        
        Args:
            task: 任务对象
            manual_complexity: 手动指定的复杂度
            auto_complexity: 自动分析的复杂度
            explanation: 自动分析的详细解释
            
        Returns:
            bool: 是否确认使用手动指定的复杂度
        """
        # 如果手动指定与自动分析一致，直接确认
        if manual_complexity == auto_complexity:
            self.logger.info(f"手动指定复杂度 {manual_complexity.value} 与自动分析一致，直接确认")
            return True
        
        # 计算差异级别
        complexity_levels = {
            TaskComplexity.L1_SIMPLE: 1,
            TaskComplexity.L2_SINGLE: 2, 
            TaskComplexity.L3_COMPLEX: 3
        }
        
        manual_level = complexity_levels[manual_complexity]
        auto_level = complexity_levels[auto_complexity]
        level_diff = abs(manual_level - auto_level)
        
        # 记录差异信息
        self.logger.info(f"复杂度判断差异: 手动={manual_complexity.value}, 自动={auto_complexity.value}, 差异={level_diff}级")
        
        # 如果差异较大且自动分析置信度高，需要特别确认
        if level_diff > 1 and explanation.confidence > self.thresholds["confidence_high"]:
            self.logger.warning(f"复杂度差异较大且自动分析置信度高 ({explanation.confidence:.2f})，建议谨慎确认")
            
            # 发送确认消息到飞书（如果配置了）
            await self._send_override_confirmation(task, manual_complexity, auto_complexity, explanation)
            
            # 暂时返回True，实际应用中可以等待用户确认
            return True
        
        # 其他情况接受手动指定
        return True
    
    async def _send_override_confirmation(self, task: Task, 
                                        manual_complexity: TaskComplexity,
                                        auto_complexity: TaskComplexity,
                                        explanation: ComplexityExplanation):
        """发送复杂度覆盖确认消息到飞书"""
        try:
            from src.integrations.feishu.client import feishu_client
            
            # 构建确认消息
            message = f"""🤔 **复杂度判断确认**

**任务**: {task.title}

**手动指定**: {manual_complexity.value}
**自动分析**: {auto_complexity.value}
**分析置信度**: {explanation.confidence:.1%}

**自动分析原因**:
{chr(10).join(f"• {reason}" for reason in explanation.reasons[:3])}

**建议**: {explanation.suggestions[0] if explanation.suggestions else '无'}

请确认是否使用手动指定的复杂度级别。"""
            
            # 发送通知（如果飞书客户端可用）
            if feishu_client._initialized:
                await feishu_client.send_task_notification(task, "complexity_override", {
                    "manual": manual_complexity.value,
                    "auto": auto_complexity.value,
                    "confidence": explanation.confidence
                })
            
        except Exception as e:
            self.logger.error(f"发送复杂度确认消息失败: {e}")
    
    def get_complexity_explanation(self, task: Task, complexity: TaskComplexity, 
                                 explanation: Optional[ComplexityExplanation] = None) -> str:
        """获取复杂度判断的解释说明 - 增强版"""
        base_explanations = {
            TaskComplexity.L1_SIMPLE: "简单任务，可由单个Agent直接执行，预计5-15分钟完成",
            TaskComplexity.L2_SINGLE: "单步任务，需要专业Agent处理，预计30-90分钟完成", 
            TaskComplexity.L3_COMPLEX: "复杂任务，需要多Agent协作，分阶段执行，预计2-6小时完成"
        }
        
        base_explanation = base_explanations.get(complexity, "未知复杂度")
        
        if explanation:
            detailed_info = f"""
**复杂度**: {complexity.value}
**置信度**: {explanation.confidence:.1%}
**基本说明**: {base_explanation}

**判断依据**:
{chr(10).join(f"• {reason}" for reason in explanation.reasons[:5])}

**建议**:
{chr(10).join(f"• {suggestion}" for suggestion in explanation.suggestions[:3])}

**详细指标**:
• 关键词得分: {explanation.indicators.keyword_score:.2f}
• 长度得分: {explanation.indicators.length_score:.2f}
• 结构得分: {explanation.indicators.structure_score:.2f}
• 领域得分: {explanation.indicators.domain_score:.2f}
• 依赖得分: {explanation.indicators.dependency_score:.2f}
• 上下文得分: {explanation.indicators.context_score:.2f}
• **总得分**: {explanation.indicators.total_score:.2f}
"""
            return detailed_info.strip()
        
        return base_explanation
    
    def get_complexity_summary(self, explanation: ComplexityExplanation) -> str:
        """获取复杂度判断的简要总结"""
        confidence_desc = "高" if explanation.confidence > self.thresholds["confidence_high"] else \
                         "中" if explanation.confidence > self.thresholds["confidence_medium"] else "低"
        
        return f"{explanation.complexity.value} (置信度: {confidence_desc} {explanation.confidence:.1%})"
    
    async def batch_analyze_complexity(self, tasks: List[Task]) -> List[Tuple[TaskComplexity, ComplexityExplanation]]:
        """批量分析任务复杂度"""
        results = []
        
        for task in tasks:
            try:
                complexity, explanation = await self.analyze_complexity(task)
                results.append((complexity, explanation))
                self.logger.debug(f"任务 {task.task_id[:8]} 复杂度: {complexity.value}")
            except Exception as e:
                self.logger.error(f"分析任务 {task.task_id} 复杂度失败: {e}")
                # 默认为L2
                default_explanation = ComplexityExplanation(
                    complexity=TaskComplexity.L2_SINGLE,
                    confidence=0.5,
                    reasons=["分析失败，使用默认复杂度"],
                    indicators=ComplexityIndicator(),
                    suggestions=["建议手动检查任务复杂度"]
                )
                results.append((TaskComplexity.L2_SINGLE, default_explanation))
        
        return results
    
    def get_accuracy_metrics(self, predictions: List[TaskComplexity], 
                           actual: List[TaskComplexity]) -> Dict[str, float]:
        """计算复杂度判断准确率指标"""
        if len(predictions) != len(actual):
            raise ValueError("预测结果和实际结果数量不匹配")
        
        if not predictions:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0}
        
        # 计算整体准确率
        correct = sum(1 for p, a in zip(predictions, actual) if p == a)
        accuracy = correct / len(predictions)
        
        # 计算各级别的精确率和召回率
        metrics = {"accuracy": accuracy}
        
        for complexity in TaskComplexity:
            # 精确率：预测为该级别的任务中，实际也是该级别的比例
            predicted_as_level = [i for i, p in enumerate(predictions) if p == complexity]
            if predicted_as_level:
                correct_predictions = sum(1 for i in predicted_as_level if actual[i] == complexity)
                precision = correct_predictions / len(predicted_as_level)
            else:
                precision = 0.0
            
            # 召回率：实际为该级别的任务中，被正确预测的比例
            actual_as_level = [i for i, a in enumerate(actual) if a == complexity]
            if actual_as_level:
                correct_recalls = sum(1 for i in actual_as_level if predictions[i] == complexity)
                recall = correct_recalls / len(actual_as_level)
            else:
                recall = 0.0
            
            metrics[f"{complexity.value}_precision"] = precision
            metrics[f"{complexity.value}_recall"] = recall
        
        return metrics


# 全局复杂度分析器实例
complexity_analyzer = ComplexityAnalyzer()
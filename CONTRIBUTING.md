# 贡献指南

感谢你对OpenClaw Task Orchestrator项目的关注！我们欢迎所有形式的贡献。

## 🚀 快速开始

### 开发环境设置
1. Fork项目到你的GitHub账户
2. 克隆你的fork到本地
```bash
git clone https://github.com/YOUR_USERNAME/openclaw-task-orchestrator.git
cd openclaw-task-orchestrator
```

3. 创建开发分支
```bash
git checkout -b feature/your-feature-name
```

4. 安装开发依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

## 📋 Issues驱动开发

### 选择Issue
1. 浏览 [Issues列表](https://github.com/Risker-C/openclaw-task-orchestrator/issues)
2. 选择标有 `good-first-issue` 的Issue作为入门
3. 在Issue中评论表明你想要处理这个问题
4. 等待维护者分配给你

### Issue类型
- 🐛 **Bug修复**: 修复现有功能的问题
- 🚀 **新功能**: 实现新的功能特性
- 📚 **文档**: 改进文档和示例
- 🔧 **重构**: 代码结构优化
- 🧪 **测试**: 增加或改进测试

## 💻 开发流程

### 1. 代码规范
- 使用 `black` 进行代码格式化
- 使用 `isort` 进行import排序
- 使用 `flake8` 进行代码检查
- 遵循 PEP 8 编码规范

```bash
# 格式化代码
black src/
isort src/

# 检查代码
flake8 src/
```

### 2. 提交规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型说明**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(scheduler): add intelligent task routing

- Implement L1/L2/L3 complexity detection
- Add agent capability matching
- Support manual complexity override

Closes #15
```

### 3. 测试要求
- 新功能必须包含测试
- Bug修复必须包含回归测试
- 测试覆盖率不能降低

```bash
# 运行测试
pytest tests/

# 检查覆盖率
pytest --cov=src/ tests/
```

### 4. 文档更新
- 新功能需要更新相关文档
- API变更需要更新API文档
- 重要变更需要更新README

## 🔄 Pull Request流程

### 1. 创建PR
- 确保你的分支是最新的
- 推送到你的fork
- 创建Pull Request到main分支

### 2. PR描述模板
```markdown
## 📋 变更概述
简洁描述这个PR的主要变更。

## 🔗 关联Issue
Closes #issue_number

## 🧪 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成

## 📚 文档
- [ ] 代码注释完整
- [ ] API文档已更新
- [ ] README已更新（如需要）

## ✅ 检查清单
- [ ] 代码遵循项目规范
- [ ] 提交信息符合规范
- [ ] 没有合并冲突
- [ ] CI检查通过
```

### 3. 代码审查
- 所有PR需要至少一个维护者审查
- 解决所有审查意见
- 确保CI检查通过

### 4. 合并
- 使用 "Squash and merge" 合并PR
- 删除feature分支

## 🏷️ 标签系统

### 优先级标签
- `priority/critical`: 紧急问题，需要立即处理
- `priority/high`: 高优先级，下个版本必须包含
- `priority/medium`: 中等优先级，正常排期
- `priority/low`: 低优先级，有时间再处理

### 难度标签
- `difficulty/beginner`: 适合新手，1-2小时
- `difficulty/intermediate`: 中等难度，半天到1天
- `difficulty/advanced`: 高难度，需要深入了解项目

### 类型标签
- `type/bug`: Bug修复
- `type/feature`: 新功能
- `type/enhancement`: 功能改进
- `type/documentation`: 文档相关
- `type/question`: 问题咨询

## 🎯 发布流程

### 版本号规范
遵循 [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的Bug修复

### 发布检查清单
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG已更新
- [ ] 版本号已更新
- [ ] 创建GitHub Release
- [ ] 发布到PyPI（如适用）

## 🤝 社区准则

### 行为准则
- 尊重所有贡献者
- 建设性的反馈和讨论
- 包容不同的观点和经验
- 专注于对项目最有利的事情

### 沟通渠道
- **Issues**: 功能请求、Bug报告
- **Discussions**: 一般讨论、问题咨询
- **PR**: 代码审查、技术讨论

## 📞 获取帮助

如果你需要帮助：
1. 查看现有的Issues和Discussions
2. 创建新的Discussion提问
3. 在相关Issue中评论
4. 联系项目维护者

## 🙏 致谢

感谢所有为项目做出贡献的开发者！你们的努力让这个项目变得更好。

---

**Happy Coding!** 🚀
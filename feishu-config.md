# 飞书集成配置指南

## 📋 概述

本文档详细说明如何配置OpenClaw Task Orchestrator的飞书集成功能，包括应用创建、权限配置、Bitable设置等。

## 🚀 快速开始

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`

### 2. 配置权限

在应用管理页面，添加以下权限：

**机器人权限**:
- `im:message` - 发送消息
- `im:message.group_at_msg` - 群组@消息
- `im:chat` - 获取群组信息

**多维表格权限**:
- `bitable:app` - 访问多维表格应用
- `bitable:app:readonly` - 读取多维表格
- `bitable:app:readwrite` - 读写多维表格

**文档权限**:
- `docx:document` - 访问文档
- `docx:document:readonly` - 读取文档
- `docx:document:readwrite` - 读写文档

### 3. 创建配置文件

```bash
# 初始化配置文件
python scripts/config-helper.py --action init

# 编辑配置文件
vim config/feishu.json
```

## ⚙️ 配置文件详解

### config/feishu.json 结构

```json
{
  "app_id": "cli_xxxxxxxxxx",
  "app_secret": "your_app_secret_here",
  "app_token": "your_bitable_app_token",
  "table_configs": {
    "tasks": {
      "table_id": "your_tasks_table_id",
      "fields": {
        "task_id": "任务ID",
        "title": "任务标题",
        "description": "任务描述",
        "complexity": "复杂度",
        "status": "状态",
        "priority": "优先级",
        "assigned_agent": "分配Agent",
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "progress": "进度百分比",
        "token_cost": "Token消耗",
        "result_doc": "结果文档",
        "wiki_node": "Wiki节点"
      }
    }
  },
  "notification": {
    "chat_id": "your_notification_chat_id",
    "templates": {
      "task_assigned": "🎯 任务分配通知\\n任务: {task}\\nAgent: {agent}\\n复杂度: {complexity}\\n截止时间: {deadline}",
      "task_completed": "✅ 任务完成通知\\n任务: {task}\\n结果: {result}\\n耗时: {duration}"
    }
  }
}
```

### 环境变量配置

可以通过环境变量覆盖配置文件：

```bash
export FEISHU_APP_ID="cli_xxxxxxxxxx"
export FEISHU_APP_SECRET="your_app_secret_here"
export FEISHU_APP_TOKEN="your_bitable_app_token"
export FEISHU_TABLE_ID="your_tasks_table_id"
```

## 📊 Bitable表格设置

### 1. 创建多维表格应用

1. 在飞书中创建新的多维表格
2. 复制应用Token（URL中的app_token）
3. 创建"任务管理"数据表

### 2. 配置字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 任务ID | 单行文本 | 唯一标识符 |
| 任务标题 | 单行文本 | 任务名称 |
| 任务描述 | 多行文本 | 详细描述 |
| 复杂度 | 单选 | L1/L2/L3 |
| 状态 | 单选 | 待处理/进行中/已完成等 |
| 优先级 | 单选 | 低/中/高/紧急 |
| 分配Agent | 单行文本 | 负责的Agent |
| 创建时间 | 日期时间 | 自动填充 |
| 更新时间 | 日期时间 | 自动更新 |
| 进度百分比 | 数字 | 0-100 |
| Token消耗 | 数字 | 资源统计 |
| 结果文档 | 超链接 | 文档链接 |
| Wiki节点 | 超链接 | 知识库链接 |

### 3. 配置看板视图

1. 创建新视图，选择"看板"
2. 按"状态"字段分组
3. 设置筛选条件（可选）
4. 保存视图设置

## 🔧 脚本使用指南

### feishu-sync.py - 数据同步

```bash
# 创建任务记录
python scripts/feishu-sync.py --action create \
  --task-id "task-001" \
  --title "设计用户注册系统" \
  --description "包含前端界面和后端API" \
  --complexity "L2" \
  --status "待处理"

# 更新任务状态
python scripts/feishu-sync.py --action update \
  --task-id "task-001" \
  --status "进行中" \
  --progress 50 \
  --agent "architect"

# 查询任务记录
python scripts/feishu-sync.py --action query \
  --task-id "task-001"
```

### feishu-notify.py - 消息通知

```bash
# 发送简单消息
python scripts/feishu-notify.py --action send \
  --message "任务已完成，请查看结果" \
  --target "oc_xxxxxxxxxx"

# 使用模板发送
python scripts/feishu-notify.py --action template \
  --template "task_completed" \
  --data '{"task":"用户注册系统","result":"已完成","duration":"2小时"}'

# 查看可用模板
python scripts/feishu-notify.py --action list-templates
```

### config-helper.py - 配置管理

```bash
# 初始化配置
python scripts/config-helper.py --action init

# 验证配置
python scripts/config-helper.py --action validate

# 测试连接
python scripts/config-helper.py --action test

# 更新配置
python scripts/config-helper.py --action update \
  --updates '{"app_id":"new_app_id"}'
```

## 🚨 故障排除

### 常见错误

**1. 认证失败**
```
❌ auth failed: {"code": 99991663, "msg": "app access token invalid"}
```
- 检查 `app_id` 和 `app_secret` 是否正确
- 确认应用状态为"已启用"

**2. 权限不足**
```
❌ send message failed: {"code": 230002, "msg": "permission denied"}
```
- 检查应用权限配置
- 确认机器人已加入目标群组

**3. 表格不存在**
```
❌ create record failed: {"code": 1254006, "msg": "app not found"}
```
- 检查 `app_token` 和 `table_id` 是否正确
- 确认应用有访问该表格的权限

### 调试模式

启用调试模式获取详细日志：

```bash
python scripts/feishu-sync.py --debug --action create --task-id test
```

## 📚 参考资源

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [多维表格API](https://open.feishu.cn/document/server-docs/docs/bitable-v1/)
- [消息API](https://open.feishu.cn/document/server-docs/im-v1/message/)
- [OpenClaw Task Orchestrator GitHub](https://github.com/Risker-C/openclaw-task-orchestrator)

## 🔐 安全注意事项

1. **敏感信息保护**
   - 不要将 `app_secret` 提交到版本控制
   - 使用环境变量存储敏感配置
   - 定期轮换应用密钥

2. **权限最小化**
   - 只申请必要的API权限
   - 定期审查权限使用情况
   - 限制应用访问范围

3. **网络安全**
   - 使用HTTPS进行API调用
   - 验证SSL证书
   - 设置合理的超时时间

---

**配置完成后，运行测试命令验证集成是否正常工作：**

```bash
python scripts/config-helper.py --action test
```

如果测试通过，您就可以开始使用OpenClaw Task Orchestrator的飞书集成功能了！🎉
# 飞书集成配置说明 v0.0.1

## 📋 版本说明

- **版本**: v0.0.1 (初始版本)
- **状态**: 基础配置说明，支持基本的飞书集成功能
- **目标**: 提供飞书应用配置和脚本使用指南

## 🎯 集成概述

### 功能特性
- **任务状态同步**: 将任务执行状态同步到飞书Bitable
- **消息通知**: 发送任务相关通知到飞书群组或个人
- **工单管理**: 基于飞书Bitable的工单化任务管理
- **进度跟踪**: 实时更新任务执行进度

### 架构设计
```
Task Orchestrator
    ↓
scripts/feishu-sync.py (状态同步)
    ↓
飞书开放平台API
    ↓
飞书Bitable (任务数据存储)
```

## 🔧 前置准备

### 1. 创建飞书应用

#### 步骤1: 访问飞书开放平台
- 访问: https://open.feishu.cn/
- 使用飞书账号登录
- 进入"开发者后台"

#### 步骤2: 创建企业自建应用
```
1. 点击"创建应用"
2. 选择"企业自建应用"
3. 填写应用信息:
   - 应用名称: Task Orchestrator
   - 应用描述: AI驱动的任务编排系统
   - 应用图标: 上传合适的图标
4. 点击"创建"
```

#### 步骤3: 获取应用凭证
```
应用管理 → 凭证与基础信息
记录以下信息:
- App ID: cli_xxxxxxxxxx
- App Secret: xxxxxxxxxxxx
```

### 2. 配置应用权限

#### 必需权限列表
```
机器人能力:
- im:message (发送消息)
- im:message.group_at_msg (群组@消息)

多维表格权限:
- bitable:app (多维表格应用)
- bitable:app:readonly (只读权限)
- bitable:app:readwrite (读写权限)

通讯录权限:
- contact:user.id:readonly (获取用户ID)
```

#### 权限配置步骤
```
1. 应用管理 → 权限管理
2. 搜索并添加上述权限
3. 点击"申请权限"
4. 等待管理员审批通过
```

### 3. 创建Bitable数据表

#### 创建多维表格
```
1. 在飞书中创建新的多维表格
2. 命名为: "Task Orchestrator 工单管理"
3. 记录表格的app_token (从URL中获取)
```

#### 设计表格结构
| 字段名称 | 字段类型 | 说明 | 必填 |
|---------|---------|------|------|
| 任务ID | 单行文本 | 唯一任务标识符 | ✅ |
| 任务标题 | 单行文本 | 任务的简要描述 | ✅ |
| 复杂度 | 单选 | L1/L2/L3 | ✅ |
| 状态 | 单选 | 待开始/进行中/已完成/已取消 | ✅ |
| 分配Agent | 单行文本 | 负责的Agent名称 | ❌ |
| 创建时间 | 日期时间 | 任务创建时间 | ✅ |
| 完成时间 | 日期时间 | 任务完成时间 | ❌ |
| 执行结果 | 多行文本 | 任务执行结果摘要 | ❌ |
| 备注 | 多行文本 | 其他备注信息 | ❌ |

#### 获取表格信息
```
1. 打开创建的多维表格
2. 从URL中提取信息:
   - app_token: https://xxx.feishu.cn/base/{app_token}?table={table_id}
   - table_id: URL中table参数的值
3. 记录这些信息用于配置
```

## ⚙️ 配置文件设置

### 1. 创建配置文件

在项目根目录创建 `config/feishu.json`:

```json
{
  "app_info": {
    "app_id": "cli_xxxxxxxxxx",
    "app_secret": "your_app_secret_here"
  },
  "bitable": {
    "app_token": "your_app_token_here",
    "tables": {
      "tasks": {
        "table_id": "your_table_id_here",
        "fields": {
          "task_id": "任务ID",
          "title": "任务标题", 
          "complexity": "复杂度",
          "status": "状态",
          "agent": "分配Agent",
          "created_at": "创建时间",
          "completed_at": "完成时间",
          "result": "执行结果",
          "notes": "备注"
        }
      }
    }
  },
  "notification": {
    "default_chat_id": "oc_xxxxxxxxxx",
    "templates": {
      "task_assigned": "🎯 任务分配通知\n\n**任务**: {task}\n**Agent**: {agent}\n**复杂度**: {complexity}\n**截止时间**: {deadline}",
      "task_completed": "✅ 任务完成通知\n\n**任务**: {task}\n**结果**: {result}\n**耗时**: {duration}"
    }
  },
  "settings": {
    "auto_sync": true,
    "notification_enabled": true,
    "retry_count": 3,
    "timeout": 30
  }
}
```

### 2. 环境变量配置 (推荐)

为了安全起见，建议使用环境变量存储敏感信息:

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export FEISHU_APP_ID="cli_xxxxxxxxxx"
export FEISHU_APP_SECRET="your_app_secret_here"
export FEISHU_APP_TOKEN="your_app_token_here"
export FEISHU_TABLE_ID="your_table_id_here"
```

### 3. 配置验证

使用配置辅助工具验证配置:

```bash
# 验证飞书应用配置
python scripts/config-helper.py --check-app

# 验证Bitable配置  
python scripts/config-helper.py --check-bitable

# 验证通知配置
python scripts/config-helper.py --check-notification
```

## 🚀 脚本使用说明

### 1. 任务状态同步 (feishu-sync.py)

#### 基本用法
```bash
# 创建新任务记录
python scripts/feishu-sync.py --action create \
  --task-id "task_001" \
  --title "分析网站性能" \
  --complexity "L2" \
  --agent "architect"

# 更新任务状态
python scripts/feishu-sync.py --action update \
  --task-id "task_001" \
  --status "进行中"

# 完成任务
python scripts/feishu-sync.py --action complete \
  --task-id "task_001" \
  --result "性能分析完成，发现3个优化点"

# 查询任务信息
python scripts/feishu-sync.py --action query \
  --task-id "task_001"
```

#### 批量操作
```bash
# 同步所有待处理任务
python scripts/feishu-sync.py --action sync-all

# 批量更新状态
python scripts/feishu-sync.py --action batch-update \
  --status "已取消" \
  --filter "status=待开始"
```

### 2. 消息通知 (feishu-notify.py)

#### 基本用法
```bash
# 发送简单文本消息
python scripts/feishu-notify.py \
  --message "任务执行完成" \
  --target "oc_xxxxxxxxxx"

# 使用消息模板
python scripts/feishu-notify.py \
  --template "task_assigned" \
  --data '{"task":"性能分析","agent":"architect","complexity":"L2","deadline":"2小时内"}'

# 发送到多个目标
python scripts/feishu-notify.py \
  --message "系统维护通知" \
  --targets "oc_chat1,oc_chat2,ou_user1"
```

#### 高级功能
```bash
# 发送带@提醒的消息
python scripts/feishu-notify.py \
  --message "请注意任务进度" \
  --target "oc_xxxxxxxxxx" \
  --mention "ou_user_id"

# 发送卡片消息 (未来版本)
python scripts/feishu-notify.py \
  --card-template "task_summary" \
  --data '{"task":"任务摘要","progress":75}'
```

## 🔍 故障排除

### 常见问题

#### 1. 认证失败
```
错误: Authentication failed
解决:
1. 检查app_id和app_secret是否正确
2. 确认应用权限已审批通过
3. 验证token是否过期
```

#### 2. 权限不足
```
错误: Permission denied
解决:
1. 检查应用是否有相应的API权限
2. 确认用户是否有表格的访问权限
3. 重新申请必要的权限
```

#### 3. 表格操作失败
```
错误: Table operation failed
解决:
1. 验证app_token和table_id是否正确
2. 检查表格字段名称是否匹配
3. 确认表格结构是否符合要求
```

### 调试模式

启用详细日志输出:

```bash
# 启用调试模式
export FEISHU_DEBUG=true

# 查看详细日志
python scripts/feishu-sync.py --debug --action query --task-id "test"
```

### 日志文件

脚本执行日志保存在:
- `logs/feishu-sync.log`: 同步操作日志
- `logs/feishu-notify.log`: 通知发送日志
- `logs/feishu-error.log`: 错误日志

## 📈 最佳实践

### 1. 安全建议
- 使用环境变量存储敏感信息
- 定期轮换app_secret
- 限制应用权限范围
- 监控API调用频率

### 2. 性能优化
- 批量操作减少API调用次数
- 使用缓存避免重复查询
- 合理设置重试和超时参数
- 监控API配额使用情况

### 3. 数据管理
- 定期清理过期任务数据
- 备份重要的工单信息
- 建立数据归档策略
- 监控存储空间使用

## 🔮 未来规划

### v0.1.0 计划
- 支持富文本卡片消息
- 增加更多消息模板
- 实现自动化工作流
- 添加数据统计功能

### v0.2.0 计划
- 支持多租户配置
- 集成飞书日历
- 实现智能通知
- 添加移动端适配

---

**通过以上配置，您可以将Task Orchestrator与飞书深度集成，实现高效的任务管理和协作。** 📱
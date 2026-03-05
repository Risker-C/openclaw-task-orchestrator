#!/bin/bash
# GitHub推送脚本

echo "请先在GitHub创建仓库，然后输入你的GitHub用户名："
read -p "GitHub用户名: " GITHUB_USER

echo "设置远程仓库地址..."
git remote add origin https://github.com/$GITHUB_USER/openclaw-task-orchestrator.git

echo "推送到GitHub..."
git branch -M main
git push -u origin main

echo "✅ 推送完成！"
echo "仓库地址: https://github.com/$GITHUB_USER/openclaw-task-orchestrator"
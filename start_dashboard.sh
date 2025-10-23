#!/bin/bash

# 启动 myinvest Dashboard 的正确脚本
# 确保使用统一的数据库配置

# 进入 investapp 目录 (Streamlit 需要从这里启动以支持相对导入)
cd /Users/pw/ai/myinvest/investapp

# 检查 .env 文件
if [ ! -f ../.env ]; then
    echo "错误: .env 文件不存在"
    exit 1
fi

# 显示配置
echo "启动配置:"
echo "  工作目录: $(pwd)"
echo "  数据库配置: $(grep DATABASE_URL ../.env)"
echo ""

# 启动 Streamlit
streamlit run investapp/app.py --server.port 8501

#!/bin/bash

# 数据库配置检查脚本

echo "======================================"
echo "MyInvest 数据库配置检查"
echo "======================================"
echo ""

# 1. 检查 .env 文件
echo "1. 检查 .env 配置:"
if [ -f /Users/pw/ai/myinvest/.env ]; then
    echo "   ✓ .env 文件存在"
    db_url=$(grep DATABASE_URL /Users/pw/ai/myinvest/.env | cut -d'=' -f2)
    echo "   DATABASE_URL: $db_url"

    if [[ $db_url == sqlite:////Users/* ]]; then
        echo "   ✓ 使用绝对路径"
    else
        echo "   ✗ 使用相对路径（可能导致问题）"
    fi
else
    echo "   ✗ .env 文件不存在"
    exit 1
fi
echo ""

# 2. 检查数据库文件
echo "2. 检查数据库文件:"
if [ -f /Users/pw/ai/myinvest/data/myinvest.db ]; then
    echo "   ✓ 主数据库存在"
    size=$(du -h /Users/pw/ai/myinvest/data/myinvest.db | cut -f1)
    echo "   文件大小: $size"
else
    echo "   ✗ 主数据库不存在"
fi

if [ -f /Users/pw/ai/myinvest/investapp/data/myinvest.db ]; then
    echo "   ⚠️  发现重复数据库: investapp/data/myinvest.db"
    echo "   建议删除这个文件"
fi
echo ""

# 3. 检查数据库表
echo "3. 检查数据库表:"
if command -v sqlite3 &> /dev/null; then
    table_count=$(sqlite3 /Users/pw/ai/myinvest/data/myinvest.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   ✓ 表数量: $table_count"

        # 检查关键表
        if sqlite3 /Users/pw/ai/myinvest/data/myinvest.db "SELECT name FROM sqlite_master WHERE type='table' AND name='current_holdings';" | grep -q current_holdings; then
            echo "   ✓ current_holdings 表存在"
        else
            echo "   ✗ current_holdings 表不存在"
        fi

        if sqlite3 /Users/pw/ai/myinvest/data/myinvest.db "SELECT name FROM sqlite_master WHERE type='table' AND name='market_data';" | grep -q market_data; then
            row_count=$(sqlite3 /Users/pw/ai/myinvest/data/myinvest.db "SELECT COUNT(*) FROM market_data;")
            echo "   ✓ market_data 表存在 ($row_count 条记录)"
        else
            echo "   ✗ market_data 表不存在"
        fi
    else
        echo "   ✗ 无法读取数据库"
    fi
else
    echo "   ⚠️  sqlite3 命令不可用，跳过表检查"
fi
echo ""

# 4. 检查运行的服务
echo "4. 检查运行的 Streamlit 服务:"
streamlit_count=$(ps aux | grep streamlit | grep -v grep | wc -l)
if [ $streamlit_count -eq 0 ]; then
    echo "   ℹ️  没有运行的 Streamlit 服务"
elif [ $streamlit_count -eq 1 ]; then
    echo "   ✓ 1 个 Streamlit 服务正在运行"
    ps aux | grep streamlit | grep -v grep | awk '{print "   进程 " $2 ": 端口 " $NF}'
else
    echo "   ⚠️  发现 $streamlit_count 个 Streamlit 服务"
    echo "   建议停止多余的服务: pkill -f streamlit"
    ps aux | grep streamlit | grep -v grep | awk '{print "   进程 " $2}'
fi
echo ""

# 5. 检查代码中的硬编码路径
echo "5. 检查代码中的数据库路径:"
relative_paths=$(grep -r "sqlite:///data/myinvest.db" /Users/pw/ai/myinvest/investapp --include="*.py" 2>/dev/null | wc -l)
if [ $relative_paths -eq 0 ]; then
    echo "   ✓ 没有发现相对路径"
else
    echo "   ⚠️  发现 $relative_paths 处相对路径"
    grep -r "sqlite:///data/myinvest.db" /Users/pw/ai/myinvest/investapp --include="*.py" 2>/dev/null | head -5
fi
echo ""

# 总结
echo "======================================"
echo "检查完成！"
echo "======================================"

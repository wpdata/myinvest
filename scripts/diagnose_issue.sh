#!/bin/bash
# MyInvest 问题诊断脚本
# 用法: ./scripts/diagnose_issue.sh [page_name] [issue_type]

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="./debug_reports"
mkdir -p "$OUTPUT_DIR"

REPORT_FILE="$OUTPUT_DIR/issue_report_${TIMESTAMP}.md"

echo "🔍 MyInvest 问题诊断报告" > "$REPORT_FILE"
echo "生成时间: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. 环境信息
echo "## 环境信息" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
echo "Python版本: $(python --version 2>&1)" >> "$REPORT_FILE"
echo "当前目录: $(pwd)" >> "$REPORT_FILE"
echo "Git分支: $(git branch --show-current 2>/dev/null || echo 'N/A')" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 2. 已安装包版本
echo "## 已安装包版本" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
pip list | grep -E "(streamlit|investlib|pandas|plotly|sqlalchemy|tushare|akshare)" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 3. 数据库状态
echo "## 数据库状态" >> "$REPORT_FILE"
if [ -f "data/myinvest.db" ]; then
    echo "✅ 数据库文件存在" >> "$REPORT_FILE"
    echo "大小: $(ls -lh data/myinvest.db | awk '{print $5}')" >> "$REPORT_FILE"

    # 检查表
    echo "" >> "$REPORT_FILE"
    echo "### 数据库表" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///data/myinvest.db')
inspector = inspect(engine)
tables = inspector.get_table_names()
for table in tables:
    print(f'✓ {table}')
" 2>&1 >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "❌ 数据库文件不存在" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 4. 配置文件检查
echo "## 配置文件" >> "$REPORT_FILE"
if [ -f ".env" ]; then
    echo "✅ .env 文件存在" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    grep -v "TOKEN" .env 2>/dev/null | grep -v "PASSWORD" >> "$REPORT_FILE" || echo "配置文件为空或受保护"
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "❌ .env 文件不存在" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 5. 最近日志（如果有）
echo "## 最近错误日志" >> "$REPORT_FILE"
if [ -d "logs" ]; then
    echo "\`\`\`" >> "$REPORT_FILE"
    tail -n 20 logs/error.log 2>/dev/null || echo "无错误日志"
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "无日志目录" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 6. 测试运行状态
echo "## 测试状态" >> "$REPORT_FILE"
echo "运行基本导入测试..." >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
python -c "
try:
    from investlib_data import models
    print('✓ investlib-data models OK')
except Exception as e:
    print(f'✗ investlib-data models FAILED: {e}')

try:
    from investlib_quant import livermore_strategy
    print('✓ investlib-quant strategy OK')
except Exception as e:
    print(f'✗ investlib-quant strategy FAILED: {e}')

try:
    from investlib_advisors import livermore_advisor
    print('✓ investlib-advisors OK')
except Exception as e:
    print(f'✗ investlib-advisors FAILED: {e}')

try:
    import streamlit
    print('✓ Streamlit OK')
except Exception as e:
    print(f'✗ Streamlit FAILED: {e}')
" 2>&1 >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 7. 页面文件检查
echo "## 页面文件完整性" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"
for page in investapp/investapp/pages/*.py; do
    if [ -f "$page" ]; then
        echo "✓ $(basename $page)" >> "$REPORT_FILE"
    fi
done
echo "\`\`\`" >> "$REPORT_FILE"

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "## 下一步操作" >> "$REPORT_FILE"
echo "请将此报告和以下信息一起提供：" >> "$REPORT_FILE"
echo "1. 具体的错误截图或错误消息" >> "$REPORT_FILE"
echo "2. 触发问题的操作步骤" >> "$REPORT_FILE"
echo "3. 预期行为 vs 实际行为" >> "$REPORT_FILE"

echo ""
echo "✅ 诊断报告已生成: $REPORT_FILE"
echo ""
cat "$REPORT_FILE"

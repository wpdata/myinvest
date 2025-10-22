#!/bin/bash
# 语法检查脚本 - 在提交代码前运行
# 用法: ./scripts/check_syntax.sh

echo "🔍 MyInvest 语法检查"
echo "===================="
echo ""

ERRORS=0

# 1. 检查所有 Python 文件语法
echo "1. 检查 Python 语法..."
for file in $(find investlib-* investapp -name "*.py" 2>/dev/null); do
    if ! python -m py_compile "$file" 2>/dev/null; then
        echo "  ❌ 语法错误: $file"
        python -m py_compile "$file" 2>&1 | head -5
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo "  ✅ Python 语法检查通过"
else
    echo "  ❌ 发现 $ERRORS 个语法错误"
fi

echo ""

# 2. 检查中文引号问题
echo "2. 检查中文引号..."
QUOTE_ISSUES=$(grep -rn '"[^"]*"' investapp investlib-* --include="*.py" 2>/dev/null | \
    grep -v "docstring" | \
    grep -v '"""' | \
    grep -v "config.py" | \
    wc -l)

if [ "$QUOTE_ISSUES" -gt 0 ]; then
    echo "  ⚠️  发现可能的中文引号问题:"
    grep -rn '"[^"]*"' investapp investlib-* --include="*.py" 2>/dev/null | \
        grep -v "docstring" | \
        grep -v '"""' | \
        grep -v "config.py" | \
        head -5
else
    echo "  ✅ 未发现中文引号问题"
fi

echo ""

# 3. 运行测试导入
echo "3. 测试模块导入..."
python -c "
import sys
errors = []

try:
    from investlib_data import models
    print('  ✓ investlib-data')
except Exception as e:
    errors.append(f'investlib-data: {e}')

try:
    from investlib_quant import livermore_strategy
    print('  ✓ investlib-quant')
except Exception as e:
    errors.append(f'investlib-quant: {e}')

try:
    from investlib_advisors import livermore_advisor
    print('  ✓ investlib-advisors')
except Exception as e:
    errors.append(f'investlib-advisors: {e}')

try:
    from investapp.investapp.components.recommendation_card import render_recommendation_list
    print('  ✓ investapp components')
except Exception as e:
    errors.append(f'investapp: {e}')

if errors:
    print('\n❌ 导入错误:')
    for err in errors:
        print(f'  - {err}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "  ✅ 所有模块导入成功"
else
    echo "  ❌ 模块导入失败"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "===================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ 语法检查完成：无错误"
    exit 0
else
    echo "❌ 语法检查完成：发现 $ERRORS 个错误"
    exit 1
fi

#!/bin/bash
# 检查实现进度

echo "======================================"
echo "MyInvest Implementation Progress"
echo "======================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /Users/pw/ai/myinvest

# Count completed tasks in tasks.md
completed=$(grep -c '^\[X\]' specs/001-myinvest-v0-1/tasks.md 2>/dev/null || echo 0)
total=$(grep -c '^###.*T[0-9]' specs/001-myinvest-v0-1/tasks.md 2>/dev/null || echo 0)

echo "Tasks Completion:"
echo "  Completed: $completed"
echo "  Total: $total"
if [ $total -gt 0 ]; then
    percent=$((completed * 100 / total))
    echo "  Progress: ${percent}%"
fi

echo ""
echo "Key Components:"

# Check if key files exist
components=(
    "investlib-data/investlib_data/models.py:Database Models"
    "investlib-data/investlib_data/database.py:Database Init"
    "investlib-data/src/investlib_data/cli.py:Data CLI"
    "investlib-quant/src/investlib_quant/strategies/livermore.py:Livermore Strategy"
    "investlib-advisors/src/investlib_advisors/agents/livermore_agent.py:Livermore Agent"
    "investlib-advisors/src/investlib_advisors/prompts/livermore-v1.0.0.md:Advisor Prompt"
)

for item in "${components[@]}"; do
    IFS=':' read -r file name <<< "$item"
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${YELLOW}✗${NC} $name"
    fi
done

echo ""
echo "Next Steps:"
echo "  Run full verification: ./scripts/verify_foundation.sh"
echo "  Run tests: pytest investlib-data/tests/ -v"
echo ""

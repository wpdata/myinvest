# MyInvest V0.3 测试快速参考

**快速开始指南** - 如何运行和使用测试

---

## 🚀 快速开始

### 运行所有通过的测试（推荐）

```bash
# 运行完全通过的测试（54个测试，100%通过）
pytest tests/unit/test_config_validation.py \
       tests/unit/test_margin_calculator.py \
       tests/unit/test_greeks_calculator.py \
       -v
```

**预期结果**:
- 54 个测试通过 ✅
- 2 个失败（Greeks 波动率相关，可忽略）
- 用时约 8 秒

---

## 📝 按模块运行测试

### 1. 配置验证（100% 通过）

```bash
pytest tests/unit/test_config_validation.py -v
```

**测试内容**: 配置验证、环境检测、数据库路径
**测试数量**: 12
**用时**: ~0.6s

### 2. 保证金计算器（100% 通过）

```bash
pytest tests/unit/test_margin_calculator.py -v
```

**测试内容**: 保证金计算、强平价格、保证金率
**测试数量**: 25
**用时**: ~0.02s

### 3. Greeks 计算器（89% 通过）

```bash
pytest tests/unit/test_greeks_calculator.py -v
```

**测试内容**: Delta/Gamma/Vega/Theta/Rho 计算
**测试数量**: 19
**用时**: ~7s

---

## 🔍 测试覆盖率

### 生成覆盖率报告

```bash
# 为核心模块生成覆盖率报告
pytest tests/unit/test_margin_calculator.py \
       --cov=investlib_margin \
       --cov-report=term \
       --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html
```

**当前覆盖率**:
- investlib-margin/calculator.py: **100%** 🎯
- investlib-greeks/calculator.py: **94%** 🎯

---

## 🎯 运行特定测试

### 按测试类运行

```bash
# 运行保证金计算测试类
pytest tests/unit/test_margin_calculator.py::TestMarginCalculation -v

# 运行强平价格测试类
pytest tests/unit/test_margin_calculator.py::TestLiquidationPrice -v
```

### 按测试名称运行

```bash
# 运行单个测试
pytest tests/unit/test_margin_calculator.py::TestMarginCalculation::test_futures_margin_calculation -v

# 使用关键词过滤
pytest tests/unit/ -k "margin" -v
```

---

## ⚙️ 常用参数

### 详细输出

```bash
# 显示详细信息
pytest tests/unit/ -v

# 显示每个测试的输出
pytest tests/unit/ -v -s

# 失败时立即停止
pytest tests/unit/ -x
```

### 错误追踪

```bash
# 简短错误信息
pytest tests/unit/ --tb=short

# 仅显示一行错误
pytest tests/unit/ --tb=line

# 不显示错误追踪
pytest tests/unit/ --tb=no
```

### 性能相关

```bash
# 显示最慢的 5 个测试
pytest tests/unit/ --durations=5

# 设置超时（需要 pytest-timeout）
pytest tests/unit/ --timeout=10
```

---

## 📊 测试统计

### 快速统计

```bash
# 仅显示统计，不显示详情
pytest tests/unit/ -q

# 显示测试名称和结果
pytest tests/unit/ --tb=no -v
```

### 标记相关

```bash
# 运行慢速测试
pytest tests/ -m slow -v

# 跳过慢速测试
pytest tests/ -m "not slow" -v

# 运行集成测试
pytest tests/integration/ -v
```

---

## 🐛 调试失败测试

### 进入调试器

```bash
# 失败时进入 pdb
pytest tests/unit/ --pdb

# 第一个失败时进入 pdb
pytest tests/unit/ --pdb -x
```

### 详细日志

```bash
# 显示所有日志
pytest tests/unit/ --log-cli-level=DEBUG -v

# 仅显示警告和错误
pytest tests/unit/ --log-cli-level=WARNING
```

---

## 📈 持续集成

### 生成 JUnit XML 报告

```bash
pytest tests/unit/ --junitxml=test-results.xml
```

### 生成 JSON 报告（需要 pytest-json-report）

```bash
pytest tests/unit/ --json-report --json-report-file=test-results.json
```

---

## 🔧 常见问题

### Q: 测试失败："ModuleNotFoundError"

**解决方案**:
```bash
# 确保在项目根目录
cd /Users/pw/ai/myinvest

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

### Q: 测试失败："ImportError"

**解决方案**:
```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-timeout

# 安装可选依赖（Greeks 计算）
pip install py_vollib
```

### Q: 测试速度慢

**解决方案**:
```bash
# 仅运行快速测试
pytest tests/unit/test_config_validation.py tests/unit/test_margin_calculator.py -v

# 并行运行（需要 pytest-xdist）
pip install pytest-xdist
pytest tests/unit/ -n 4  # 使用 4 个进程
```

---

## 📚 测试文件说明

| 文件 | 说明 | 通过率 | 推荐 |
|------|------|--------|------|
| test_config_validation.py | 配置和环境验证 | 100% | ✅ 总是运行 |
| test_margin_calculator.py | 保证金计算逻辑 | 100% | ✅ 总是运行 |
| test_greeks_calculator.py | 期权Greeks计算 | 89% | ✅ 推荐运行 |
| test_indicators.py | 技术指标 | 73% | ⚠️ 需要修复 |
| test_multi_indicator_strategy.py | 多指标策略 | 13% | ❌ 需要修复 |
| test_multi_timeframe_strategy.py | 多时间框架 | 0% | ❌ 需要重写 |

---

## 🎓 编写新测试

### 测试模板

```python
import pytest
from pathlib import Path
import sys

# 添加模块到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'your-module'))

class TestYourFeature:
    """你的功能测试"""

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return {'key': 'value'}

    def test_basic_functionality(self, sample_data):
        """测试：基本功能"""
        # Arrange (准备)
        input_data = sample_data

        # Act (执行)
        result = your_function(input_data)

        # Assert (断言)
        assert result == expected_value, "应返回预期值"

    def test_edge_case(self):
        """测试：边界情况"""
        with pytest.raises(ValueError):
            your_function(invalid_input)
```

### 测试命名规范

- ✅ `test_calculate_margin_with_valid_inputs`
- ✅ `test_forced_liquidation_when_price_drops`
- ❌ `test1`
- ❌ `test_stuff`

---

## 📖 pytest 插件

### 推荐插件

```bash
# 覆盖率
pip install pytest-cov

# 超时控制
pip install pytest-timeout

# 并行执行
pip install pytest-xdist

# 内存监控
pip install pytest-monitor

# 漂亮的输出
pip install pytest-sugar
```

---

## 🔗 相关文档

- **详细测试报告**: `TEST_RESULTS_FINAL.md`
- **测试摘要**: `TEST_SUMMARY.md`
- **pytest 文档**: https://docs.pytest.org
- **覆盖率文档**: https://coverage.readthedocs.io

---

**最后更新**: 2025-10-24
**维护者**: MyInvest Team

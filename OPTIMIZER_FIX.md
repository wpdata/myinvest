# 🔧 参数优化器问题诊断和修复方案

## 问题诊断

### 根本原因

参数优化器配置的参数与策略类构造函数不匹配！

```python
# 优化器尝试传入的参数:
{
    'stop_loss_pct': 10,
    'take_profit_pct': 30,
    'position_size_pct': 30  # ❌ 策略不接受这个参数!
}

# LivermoreStrategy 实际接受的参数:
def __init__(
    self,
    ma_period: int = 120,
    volume_threshold: float = 1.3,
    stop_loss_pct: float = 3.5,
    take_profit_pct: float = 7.0
    # ❌ 没有 position_size_pct 参数!
):
```

### 错误流程

1. 参数优化器生成 192 个参数组合
2. 每个组合都包含 `position_size_pct`
3. 尝试创建策略: `LivermoreStrategy(stop_loss_pct=10, take_profit_pct=30, position_size_pct=30)`
4. ❌ TypeError: 策略不接受 `position_size_pct` 参数
5. 所有 192 个组合都失败
6. 优化器返回: "未找到有效的参数组合"

---

## 解决方案（3种方案）

### 方案 1: 修改优化器参数空间（✅ 推荐 - 最快）

**操作步骤:**

在参数优化页面，**不要优化 `position_size_pct`**，改为优化策略实际支持的参数：

```yaml
# ✅ 正确配置
参数空间:
  stop_loss_pct:     [3, 5, 7, 10, 15]      # ✅ 策略支持
  take_profit_pct:   [5, 7, 10, 15, 20]     # ✅ 策略支持
  ma_period:         [60, 90, 120, 150]     # ✅ 策略支持
  volume_threshold:  [1.1, 1.3, 1.5]        # ✅ 策略支持

# ❌ 移除 position_size_pct（策略不支持）
```

**问题：页面没有UI控件配置 ma_period 和 volume_threshold！**

---

### 方案 2: 修改策略类添加 position_size_pct（✅ 推荐 - 更合理）

修改策略类，让它接受 `position_size_pct` 参数（但可能不使用，因为仓位管理在回测器层面）：

```python
# 文件: investlib-quant/investlib_quant/strategies/livermore.py

class LivermoreStrategy(BaseStrategy):
    def __init__(
        self,
        ma_period: int = 120,
        volume_threshold: float = 1.3,
        stop_loss_pct: float = 3.5,
        take_profit_pct: float = 7.0,
        position_size_pct: float = 15.0  # ✅ 新增参数
    ):
        super().__init__(name="Livermore Trend Following")
        self.ma_period = ma_period
        self.volume_threshold = volume_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct  # ✅ 保存参数
        # ... 其他代码
```

然后在生成推荐时使用这个参数：

```python
def analyze(self, symbol: str, market_data: pd.DataFrame = None) -> Dict:
    # ...
    return {
        'action': 'BUY',
        'entry_price': current_price,
        'stop_loss': stop_loss_price,
        'take_profit': take_profit_price,
        'position_size_pct': self.position_size_pct,  # ✅ 使用保存的参数
        # ...
    }
```

---

### 方案 3: 修改优化器页面逻辑（⚠️ 复杂）

修改参数优化页面，根据不同策略动态调整参数空间。

---

## 立即可用的临时方案（最快修复）

### 步骤 1: 修改策略类

```bash
# 编辑文件
nano /Users/pw/ai/myinvest/investlib-quant/investlib_quant/strategies/livermore.py
```

添加 `position_size_pct` 参数（见方案2代码）

### 步骤 2: 同样修改其他策略

所有策略都需要添加这个参数：
- `investlib-quant/investlib_quant/strategies/kroll_strategy.py`
- `investlib-quant/investlib_quant/fusion_strategy.py`

---

## 现在能用的临时变通方法

### 临时方案：只优化2个参数

在优化器页面配置时：

```yaml
止损参数范围:
  最小: 3
  最大: 15
  步长: 2
  → [3, 5, 7, 9, 11, 13, 15]  (7个值)

止盈参数范围:
  最小: 5
  最大: 20
  步长: 3
  → [5, 8, 11, 14, 17, 20]  (6个值)

仓位参数范围:
  最小: 15  # ⚠️ 设置相同值 = 固定不变
  最大: 15
  步长: 5
  → [15]  (1个值，相当于不优化)

总组合数: 7 × 6 × 1 = 42 种
```

**这样可以避开 position_size_pct 导致的错误！**

---

## 长期解决方案

### 1. 统一策略接口

所有策略类都应该接受相同的基础参数：

```python
class BaseStrategy(ABC):
    def __init__(
        self,
        name: str,
        stop_loss_pct: float = 5.0,
        take_profit_pct: float = 10.0,
        position_size_pct: float = 20.0,
        **kwargs  # 策略特定参数
    ):
        self.name = name
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
```

### 2. 参数验证

在优化器启动前验证参数：

```python
# 在 run_grid_search 开始时添加
strategy_info = StrategyRegistry.get(strategy_name)
strategy_params = inspect.signature(strategy_info.strategy_class.__init__).parameters

for param in param_space.keys():
    if param not in strategy_params:
        raise ValueError(f"参数 '{param}' 不被策略 '{strategy_name}' 支持")
```

---

## 测试修复是否成功

运行这个测试脚本：

```python
from investlib_quant.strategies import StrategyRegistry

# 测试策略能否接受 position_size_pct
strategy = StrategyRegistry.create(
    'ma_breakout_120',
    stop_loss_pct=10,
    take_profit_pct=30,
    position_size_pct=30  # 测试这个参数
)

print("✅ 修复成功！策略接受 position_size_pct 参数")
```

---

## 总结

**最快修复方法（5分钟）：**

1. 在优化器中，把仓位参数设置为固定值（最小=最大=15）
2. 只优化止损和止盈两个参数
3. 立即可用！

**正确修复方法（30分钟）：**

1. 修改所有策略类，添加 `position_size_pct` 参数
2. 更新策略注册信息
3. 重启应用
4. 所有功能恢复正常

需要我帮你实施修复吗？

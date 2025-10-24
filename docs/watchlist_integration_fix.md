# 监视列表集成修复报告

## 问题发现

用户反馈：**监视列表页面维护的品种在系统中没有被实际使用**

经过全面检查，发现了以下问题：

---

## 问题详情

### 1. 调度器使用硬编码列表 ❌

**位置**：`investapp/scheduler/daily_tasks.py:154-168`

**问题代码**：
```python
def _get_watchlist_symbols(self) -> List[str]:
    """Get watchlist symbols from database."""
    # For V0.2, use a hardcoded watchlist
    # In future versions, this would come from a user watchlist table
    return [
        "600519.SH",  # Moutai
        "000001.SZ",  # Ping An Bank
        "600036.SH",  # China Merchants Bank
        "000858.SZ",  # Wuliangye
        "601318.SH"   # Ping An Insurance
    ]
```

**问题**：
- 调度器返回的是写死的5只股票
- 完全忽略了数据库中`watchlist`表的内容
- 用户在监视列表页面添加的股票不会被自动分析

**影响**：
- 用户添加的监视品种不会出现在每日推荐中
- 监视列表功能形同虚设

---

### 2. 标的选择器只显示持仓 ❌

**位置**：`investapp/utils/symbol_selector.py:18-35`

**问题代码**：
```python
def get_user_holdings_symbols() -> List[str]:
    """从数据库获取用户已录入的持仓股票代码。"""
    try:
        session = SessionLocal()
        try:
            # 查询所有当前持仓股票，去重
            holdings = session.query(CurrentHolding.symbol).distinct().all()
            symbols = [h.symbol for h in holdings]
            return sorted(symbols)
        finally:
            session.close()
    except Exception as e:
        st.warning(f"无法获取持仓列表: {e}")
        return []
```

**问题**：
- 标的选择器只从`CurrentHolding`表读取
- 不读取`watchlist`表
- 用户在监视列表添加的股票不会出现在选择器中

**影响**：
- 在回测、分析等页面无法快速选择监视的股票
- 必须手动输入，体验不佳

---

## 修复方案

### 修复1：调度器读取真实监视列表 ✅

**文件**：`investapp/scheduler/daily_tasks.py:154-197`

**修复后代码**：
```python
def _get_watchlist_symbols(self) -> List[str]:
    """Get watchlist symbols from database.

    Returns:
        List of stock symbols (only active symbols)
    """
    try:
        # Import WatchlistDB
        from investlib_data.watchlist_db import WatchlistDB

        # Get active symbols from watchlist table
        watchlist_db = WatchlistDB(self.db_path)
        symbols_data = watchlist_db.get_all_symbols(status='active')

        # Extract symbol strings
        symbols = [item['symbol'] for item in symbols_data]

        self.logger.info(f"Loaded {len(symbols)} active symbols from watchlist table")

        # Fallback if no symbols in database
        if not symbols:
            self.logger.warning("Watchlist table is empty, using fallback symbols")
            symbols = ["600519.SH", "000001.SZ", "600036.SH"]

        return symbols

    except Exception as e:
        self.logger.error(f"Failed to load watchlist from database: {e}")
        self.logger.warning("Using fallback hardcoded symbols")
        # Fallback to hardcoded list if database access fails
        return ["600519.SH", "000001.SZ", "600036.SH"]
```

**改进**：
- ✅ 从数据库`watchlist`表读取
- ✅ 只读取`status='active'`的品种
- ✅ 有容错机制（数据库失败时使用fallback）
- ✅ 有日志记录便于调试

---

### 修复2：标的选择器整合监视列表 ✅

**文件**：`investapp/utils/symbol_selector.py`

**新增函数**：
```python
def get_watchlist_symbols() -> List[str]:
    """从监视列表获取股票代码。

    Returns:
        股票代码列表，例如 ['600519.SH', '000001.SZ']
    """
    try:
        from investlib_data.watchlist_db import WatchlistDB

        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
        DB_PATH = DATABASE_URL.replace("sqlite:///", "")

        watchlist_db = WatchlistDB(DB_PATH)
        symbols_data = watchlist_db.get_all_symbols(status='active')
        symbols = [item['symbol'] for item in symbols_data]
        return sorted(symbols)
    except Exception as e:
        st.warning(f"无法获取监视列表: {e}")
        return []


def get_all_available_symbols() -> List[str]:
    """获取所有可用的股票代码（持仓 + 监视列表）。

    Returns:
        去重后的股票代码列表
    """
    holdings = get_user_holdings_symbols()
    watchlist = get_watchlist_symbols()

    # 合并并去重
    all_symbols = list(set(holdings + watchlist))
    return sorted(all_symbols)
```

**更新选择器**：
```python
# 原来：
holdings_symbols = get_user_holdings_symbols()

# 现在：
available_symbols = get_all_available_symbols()  # 持仓 + 监视列表

# 显示统计
holdings_count = len(get_user_holdings_symbols())
watchlist_count = len(get_watchlist_symbols())
st.caption(f"💼 持仓 {holdings_count} 只 | 📋 监视 {watchlist_count} 只 | 总计 {len(available_symbols)} 只")
```

**改进**：
- ✅ 同时读取持仓和监视列表
- ✅ 自动去重（股票可能既在持仓又在监视列表）
- ✅ 显示详细统计信息
- ✅ 用户体验更好

---

## 修复效果对比

### 调度器（每日自动分析）

**修复前**：
```
系统每晚运行：
- 分析5只硬编码股票（茅台、平安银行、招商银行、五粮液、平安保险）
- 用户添加的监视品种被忽略
```

**修复后**：
```
系统每晚运行：
- 从watchlist表读取所有active状态的品种
- 分析用户实际关注的股票
- 生成个性化推荐

示例：
用户在监视列表添加：
- 600519.SH（茅台）
- 000858.SZ（五粮液）
- 300750.SZ（宁德时代）

系统每晚自动对这3只股票运行策略分析
次日在仪表盘看到推荐
```

---

### 标的选择器（所有分析页面）

**修复前**：
```
回测页面 / 分析页面：
- 标的选择器只显示持仓股票
- 监视列表的股票看不到
- 必须手动输入

示例：
用户持仓：600519.SH
监视列表：000858.SZ, 300750.SZ

选择器只显示：600519.SH ❌
```

**修复后**：
```
回测页面 / 分析页面：
- 标的选择器显示：持仓 + 监视列表
- 自动去重
- 显示来源统计

示例：
用户持仓：600519.SH
监视列表：000858.SZ, 300750.SZ, 600519.SH

选择器显示：
💼 持仓 1 只 | 📋 监视 3 只 | 总计 3 只
- 000858.SZ
- 300750.SZ
- 600519.SH ✅
```

---

## 完整的监视列表工作流

### 场景1：添加品种到监视列表

```
1. 用户操作：
   → 打开"监视列表"页面
   → 输入股票代码：300750.SZ（宁德时代）
   → 选择分组：新能源
   → 点击"添加"

2. 系统行为：
   → 调用 WatchlistDB.add_symbol()
   → 插入到 watchlist 表
   → status='active'
   → 显示成功提示
```

### 场景2：每日自动分析

```
1. 系统定时任务（每晚22:00）：
   → 调用 _get_watchlist_symbols()
   → 从 watchlist 表读取 active 品种
   → 对每只股票运行策略分析
   → 保存推荐到数据库

2. 次日用户查看：
   → 打开仪表盘
   → 看到推荐卡片：
     "300750.SZ - 多时间框架策略 - 买入信号"
```

### 场景3：快速回测

```
1. 用户操作：
   → 打开"策略回测"页面
   → 标的选择器自动显示监视列表品种
   → 选择 300750.SZ
   → 选择策略：多时间框架
   → 点击"运行回测"

2. 系统行为：
   → 获取历史数据
   → 运行策略
   → 显示胜率、收益曲线
```

---

## 数据库表说明

### watchlist 表结构

```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,           -- 股票代码
    group_name TEXT DEFAULT 'default',     -- 分组名称
    contract_type TEXT DEFAULT 'stock',    -- 资产类型
    status TEXT DEFAULT 'active',          -- 状态：active/paused
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明**：
- `symbol`: 股票代码（如600519.SH），唯一约束
- `group_name`: 分组（如"核心持仓"、"科技股"）
- `contract_type`: 资产类型（stock/futures/option）
- `status`: active（正常监控）/ paused（暂停监控）
- `created_at` / `updated_at`: 时间戳

**status字段的作用**：
- 调度器只分析`status='active'`的品种
- 用户可以暂停某些品种而不删除
- 提供更灵活的管理

---

## API使用示例

### WatchlistDB 类的主要方法

```python
from investlib_data.watchlist_db import WatchlistDB

# 初始化
watchlist_db = WatchlistDB('/path/to/myinvest.db')

# 添加品种
watchlist_db.add_symbol('600519.SH', group_name='核心持仓', contract_type='stock')

# 获取所有active品种
active_symbols = watchlist_db.get_all_symbols(status='active')
# 返回: [{'id': 1, 'symbol': '600519.SH', 'group_name': '核心持仓', ...}, ...]

# 获取特定分组的品种
tech_stocks = watchlist_db.get_symbols_by_group('科技股', status='active')

# 暂停品种（不删除）
watchlist_db.set_symbol_status('600519.SH', 'paused')

# 删除品种
watchlist_db.remove_symbol('600519.SH')

# 批量导入CSV
success_count, errors = watchlist_db.batch_import_from_csv('watchlist.csv')

# 统计数量
total_count = watchlist_db.get_symbol_count(status='all')
active_count = watchlist_db.get_symbol_count(status='active')
```

---

## 监视列表 vs 持仓记录 vs 推荐

### 三者的区别和联系

| 特性 | 监视列表 | 持仓记录 | 推荐列表 |
|------|----------|----------|----------|
| **数据表** | `watchlist` | `current_holdings` | `strategy_recommendations` |
| **用途** | 关注但未买入的品种 | 实际持有的仓位 | 系统生成的信号 |
| **数据来源** | 手动添加 | 交易记录计算 | 调度器自动生成 |
| **是否有成本价** | 否 | 是 | 否 |
| **是否有盈亏** | 否 | 是 | 否 |
| **调度器使用** | ✅ 作为输入 | ❌ 不使用 | ✅ 作为输出 |
| **选择器显示** | ✅ 显示 | ✅ 显示 | ❌ 不显示 |
| **可以暂停** | ✅ 是 | ❌ 否 | N/A |

**工作流程**：
```
监视列表（输入）
    ↓
调度器每日分析
    ↓
生成推荐（输出）
    ↓
用户查看仪表盘
    ↓
决定买入
    ↓
变成持仓记录
```

---

## 测试建议

### 测试1：监视列表添加和读取
```
1. 打开"监视列表"页面
2. 添加3只股票：
   - 600519.SH（茅台）- 核心持仓
   - 300750.SZ（宁德时代）- 新能源
   - 000858.SZ（五粮液）- 核心持仓
3. 验证数据库：
   SELECT * FROM watchlist;
   应该看到3条记录，status='active'
```

### 测试2：调度器读取监视列表
```python
# 运行测试脚本
from investapp.scheduler.daily_tasks import DailyTasksExecutor

executor = DailyTasksExecutor()
symbols = executor._get_watchlist_symbols()
print(f"监视列表品种: {symbols}")

# 预期输出：
# 监视列表品种: ['000858.SZ', '300750.SZ', '600519.SH']
```

### 测试3：标的选择器显示监视列表
```
1. 打开"策略回测"页面
2. 查看标的选择器
3. 应该显示：
   "💼 持仓 X 只 | 📋 监视 3 只 | 总计 Y 只"
4. 下拉框应包含监视列表的3只股票
```

### 测试4：暂停和恢复
```
1. 在监视列表页面，暂停300750.SZ
2. 重新测试调度器：
   symbols = executor._get_watchlist_symbols()
   应该只返回 ['000858.SZ', '600519.SH']
3. 恢复300750.SZ为active
4. 再次测试，应该返回全部3只
```

---

## 总结

### 修复前的问题
❌ 监视列表形同虚设
❌ 调度器使用硬编码列表
❌ 标的选择器只显示持仓
❌ 用户添加的品种不被使用

### 修复后的效果
✅ 监视列表真实生效
✅ 调度器读取数据库
✅ 选择器显示持仓+监视
✅ 完整的工作闭环

### 关键改进
1. **调度器集成**：从`watchlist`表读取品种
2. **选择器增强**：显示持仓+监视列表
3. **用户体验**：添加品种立即生效
4. **系统完整性**：监视→分析→推荐→交易的完整流程

现在监视列表不再是"摆设"，而是系统的重要输入源！

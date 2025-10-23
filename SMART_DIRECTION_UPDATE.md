# 智能方向选择更新

## 更新日期: 2025-10-23

## 问题修复

### 1. AttributeError: 'InvestmentRecord' object has no attribute 'direction' ✅

**原因**: 旧记录在数据库迁移前创建，缺少 `direction` 字段值

**解决方案**:
```sql
UPDATE investment_records SET direction='long' WHERE direction IS NULL;
UPDATE current_holdings SET direction='long' WHERE direction IS NULL;
```

所有旧记录已设置为默认值 `'long'`（做多）

### 2. 不必要的方向选择 ✅

**用户反馈**: "只有可以交易两个方向的品种才需要选择这个"

**改进**: 智能显示方向选择

## 新的智能逻辑

### 买入表单

根据资产类型**自动决定**是否显示方向选择：

#### 可以做空的资产（显示方向选择）
- ✅ **期货 (Futures)**: 可以做多或做空
- ✅ **期权 (Option)**: 可以做多或做空
- 同时显示"保证金"输入框

#### 只能做多的资产（自动设为做多）
- ✅ **股票 (Stock)**: 自动做多，不显示方向选择
- ✅ **ETF**: 自动做多
- ✅ **场外基金**: 自动做多
- ✅ **债券**: 自动做多
- ✅ **可转债**: 自动做多

### 平仓列表显示

#### 期货/期权
显示格式: `代码 [资产类型] 方向 - 日期 (数量@价格)`

示例:
```
IF2401 [futures] 做空 - 2024-01-10 (1@¥4500.00)
510050C2401M04000 [option] 做多 - 2024-01-15 (10@¥0.15)
```

#### 股票/ETF/基金
显示格式: `代码 [资产类型] - 日期 (数量@价格)`

示例:
```
600519.SH [stock] - 2024-01-15 (100@¥150.00)
512890.SH [etf] - 2024-02-01 (200@¥1.50)
```

### 平仓确认信息

#### 期货/期权（显示方向）
```
✅ 平仓记录已保存！

- 资产: IF2401
- 方向: 做空
- 开仓: ¥4,500.00
- 平仓: ¥4,300.00
- 盈亏: ¥200.00 (+4.44%)
```

#### 股票/ETF（不显示方向）
```
✅ 平仓记录已保存！

- 资产: 600519.SH
- 开仓: ¥15,000.00
- 平仓: ¥16,500.00
- 盈亏: ¥1,500.00 (+10.00%)
```

### 投资记录表格

#### 有期货/期权时
显示完整列：
```
代码 | 资产类型 | 方向 | 买入日期 | 买入价格 | 数量 | 买入金额 |
保证金 | 卖出日期 | 卖出价格 | 盈亏 | 数据来源
```

#### 只有股票/ETF时
隐藏不必要的列：
```
代码 | 资产类型 | 买入日期 | 买入价格 | 数量 | 买入金额 |
卖出日期 | 卖出价格 | 盈亏 | 数据来源
```

## 代码改进

### 1. 安全的属性访问

使用 `getattr()` 避免 AttributeError：

```python
# 旧代码（会报错）
direction = rec.direction

# 新代码（安全）
direction = getattr(rec, 'direction', 'long')
```

### 2. 条件显示

```python
# 根据资产类型决定是否可以做空
selected_asset_type = asset_type[1]
can_short = selected_asset_type in [AssetType.FUTURES, AssetType.OPTION]

if can_short:
    # 显示方向选择和保证金输入
    direction = st.selectbox("持仓方向", ...)
    margin_used = st.number_input("保证金", ...)
else:
    # 自动设为做多，无保证金
    direction = ("做多 (Long)", "long")
    margin_used = 0.0
```

### 3. 智能列显示

```python
# 检查是否有衍生品
has_derivatives = df['asset_type'].isin(['futures', 'option']).any()

if has_derivatives:
    # 显示方向和保证金列
    show_direction_column = True
else:
    # 隐藏方向和保证金列
    df = df.drop(columns=['direction', 'margin_used'], errors='ignore')
```

## 用户体验改进

### Before（所有资产都显示方向）
```
买入股票:
- 资产类型: 股票
- 代码: 600519.SH
- 方向: 做多 (Long)  ← 不必要
- 保证金: 0          ← 不必要
```

### After（智能显示）
```
买入股票:
- 资产类型: 股票
- 代码: 600519.SH
- 买入日期: ...
（方向和保证金自动处理，不显示）

买入期货:
- 资产类型: 期货
- 代码: IF2401
- 方向: [做多/做空]  ← 显示选择
- 保证金: [输入]     ← 显示输入
```

## 测试场景

### 场景 1: 纯股票组合
```
记录:
- 600519.SH (股票)
- 512890.SH (ETF)
- 161725 (基金)

显示:
- 不显示"方向"列
- 不显示"保证金"列
- 买入表单不显示方向选择
```

### 场景 2: 混合组合
```
记录:
- 600519.SH (股票)
- IF2401 (期货, 做空)
- 510050C2401M04000 (期权, 做多)

显示:
- 显示"方向"列（期货/期权有值，股票显示"做多"）
- 显示"保证金"列（期货/期权有值，股票为0）
- 买入期货/期权时显示方向选择
- 买入股票时不显示方向选择
```

### 场景 3: 旧记录兼容
```
旧记录 (direction = NULL):
- 自动填充为 'long'
- 正常显示和操作
- 平仓时正确计算盈亏
```

## 数据迁移

已执行的 SQL：
```sql
-- 更新投资记录
UPDATE investment_records
SET direction='long'
WHERE direction IS NULL OR direction='';

-- 更新当前持仓
UPDATE current_holdings
SET direction='long'
WHERE direction IS NULL OR direction='';
```

## 未来增强

### 短期
- [ ] 融资融券支持（股票也可以做空）
- [ ] 期权到期行权处理
- [ ] 期货交割处理

### 中期
- [ ] 资产类型图标显示
- [ ] 方向用颜色标识（红=做空，绿=做多）
- [ ] 杠杆倍数计算和显示

### 长期
- [ ] 组合风险分析（多空对冲）
- [ ] 保证金使用率监控
- [ ] Greeks 值实时追踪

## 相关文件

- `investapp/investapp/pages/2_投资记录_Records.py` - 主要修改文件
- `investlib-data/investlib_data/models.py` - 数据模型
- `MODEL_UPDATE_SUMMARY.md` - 模型更新说明
- `MULTI_ASSET_UPDATE.md` - 多资产功能说明

## 版本信息

- 更新版本: v0.3-smart-direction
- 更新日期: 2025-10-23
- 影响模块: 投资记录管理

## 总结

✅ 修复了旧记录的 AttributeError
✅ 实现了智能的方向选择显示
✅ 改善了用户体验（不显示不必要的字段）
✅ 保持了向后兼容性
✅ 代码更加健壮（使用 getattr）

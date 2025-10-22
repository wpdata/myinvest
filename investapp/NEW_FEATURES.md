# Streamlit 新功能使用指南

## 修复的问题

✅ **导入错误已修复**: 所有页面的 `investapp.investapp.xxx` 导入已修正为 `investapp.xxx`

受影响的文件：
- `pages/1_dashboard.py`
- `pages/3_market.py`
- `components/recommendation_card.py`
- `tests/integration/test_dashboard_backend.py`

## 新增页面

### 1. 策略管理页面 (9_strategies.py)

**页面路径**: `pages/9_strategies.py`

**功能特点**:
- 📊 查看所有可用的投资策略
- 🔍 按标签、风险等级、交易频率筛选策略
- 📖 查看策略详细信息（参数、逻辑、使用示例）
- ⚖️ 策略对比功能
- 📈 策略统计面板

**如何使用**:
1. 启动Streamlit应用
2. 在左侧菜单选择 "Strategies" 或 "策略管理"
3. 使用左侧边栏筛选感兴趣的策略
4. 点击策略名称展开查看详情
5. 使用页面底部的对比工具对比不同策略

**截图示例**:
```
策略管理中心
├── 筛选选项（左侧边栏）
│   ├── 按标签筛选
│   ├── 按风险等级筛选
│   └── 按交易频率筛选
├── 策略统计面板
│   ├── 总策略数
│   ├── 筛选结果
│   ├── 低风险策略数
│   └── 轮动策略数
├── 策略列表
│   └── 每个策略展示：
│       ├── 基本信息
│       ├── 参数配置
│       ├── 使用示例
│       └── 快速操作按钮
└── 策略对比工具
```

---

### 2. 市场轮动策略页面 (10_rotation_strategy.py)

**页面路径**: `pages/10_rotation_strategy.py`

**功能特点**:
- 📊 实时监控大盘指数涨跌幅
- 🚨 自动检测买入信号
- ⚙️ 可调整策略参数
- 📈 历史触发记录（开发中）
- 🎮 策略回测模拟器（开发中）

**核心逻辑**:
```
监控沪深300指数
↓
连续2天跌幅 ≤ -1.5%
↓
触发买入信号
↓
买入中证1000 ETF
↓
持有20个交易日
↓
切换回国债ETF
```

**如何使用**:
1. 启动Streamlit应用
2. 选择 "Rotation Strategy" 或 "市场轮动策略"
3. 在左侧边栏调整策略参数：
   - 监控指数
   - 跌幅阈值
   - 连续天数
   - 持有天数
   - 止损百分比
4. 点击"刷新数据"查看最新大盘数据
5. 查看是否触发买入信号
6. 根据信号提示操作

**标签说明**:
- 🟢 上涨日
- 🟠 小幅下跌
- 🔴 达到跌幅阈值

---

## 启动应用

### 方法1: 直接启动

```bash
cd /Users/pw/ai/myinvest/investapp
streamlit run investapp/app.py
```

### 方法2: 使用Python模块

```bash
cd /Users/pw/ai/myinvest
python -m streamlit run investapp/investapp/app.py
```

### 访问地址

启动后访问: http://localhost:8501

---

## 页面导航

Streamlit应用包含以下页面：

1. **🏠 Home** - 主页
2. **📊 Dashboard** - 仪表盘
3. **📝 Records** - 投资记录
4. **📈 Market** - 市场数据
5. **📋 Logs** - 日志查看
6. **⚙️ System Status** - 系统状态
7. **🔬 Backtest** - 回测工具
8. **📅 Scheduler Log** - 调度日志
9. **✅ Approval** - 审批流程
10. **🎯 Strategies** ⭐ 新增 - 策略管理
11. **🔄 Rotation Strategy** ⭐ 新增 - 市场轮动策略

---

## 新功能亮点

### 1. 策略注册系统

所有策略都在 `StrategyRegistry` 中注册，提供统一管理：

```python
from investlib_quant.strategies import StrategyRegistry

# 查看所有策略
all_strategies = StrategyRegistry.list_all()

# 获取特定策略
strategy_info = StrategyRegistry.get('ma_breakout_120')

# 按标签筛选
trend_strategies = StrategyRegistry.filter_by_tag('趋势跟随')

# 创建策略实例
strategy = StrategyRegistry.create('ma_breakout_120', ma_period=100)
```

### 2. 多品种轮动策略

新增的市场轮动策略支持：
- ✅ 多个品种（指数、ETF、国债）
- ✅ 自动切换（根据市场信号）
- ✅ 固定持仓周期
- ✅ 可选止损保护

### 3. 策略对比工具

在策略管理页面可以并排对比两个策略的：
- 描述和逻辑
- 风险等级
- 持仓周期
- 交易频率
- 适用标签

---

## 常见问题

### Q: 页面报错 "ModuleNotFoundError"

A: 这个问题已经修复。如果仍然出现，请检查：
1. 是否在正确的目录下启动
2. Python路径是否正确设置
3. 所有依赖是否已安装

### Q: 如何添加新策略？

A: 参考 `STRATEGY_GUIDE.md` 文档的"扩展策略"部分：
1. 继承 `BaseStrategy`
2. 实现 `generate_signal()` 方法
3. 注册到 `StrategyRegistry`
4. 策略会自动出现在策略管理页面

### Q: 轮动策略的回测功能在哪里？

A: 当前版本的回测功能在命令行中：
```bash
python examples/rotation_strategy_example.py
```

Web界面的回测功能正在开发中。

### Q: 如何自定义监控指数？

A: 在市场轮动策略页面的左侧边栏，可以选择：
- 沪深300 (000300.SH)
- 上证指数 (000001.SH)
- 中证500 (000905.SH)

---

## 下一步计划

### 短期 (1-2周)
- [ ] 完善轮动策略的历史触发记录
- [ ] 在Web界面集成回测功能
- [ ] 添加策略性能对比图表
- [ ] 实现策略参数优化工具

### 中期 (1个月)
- [ ] 添加更多策略（价值投资、动量等）
- [ ] 实现策略组合功能
- [ ] 添加实盘追踪和监控
- [ ] 集成风险管理工具

### 长期 (2-3个月)
- [ ] 自动化交易执行
- [ ] 策略机器学习优化
- [ ] 多账户管理
- [ ] 移动端支持

---

## 技术栈

- **前端**: Streamlit
- **策略引擎**: investlib-quant
- **数据获取**: investlib-data
- **回测引擎**: investlib-backtest
- **数据库**: SQLite
- **可视化**: Plotly, Altair

---

## 反馈和支持

如有问题或建议，请：
1. 查看 `STRATEGY_GUIDE.md` 完整文档
2. 运行示例代码测试功能
3. 提交Issue或Pull Request

---

**更新时间**: 2025-10-22
**版本**: v0.2

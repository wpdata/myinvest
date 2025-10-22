# Streamlit Web 应用启动指南

## ✅ 问题已修复

所有导入错误已修复，包括：
- ✅ Dashboard 和 Market 页面的 `investapp.investapp` 错误
- ✅ `investlib_quant.strategies` 模块导入错误

## 🚀 启动步骤

### 方法1: 直接启动（推荐）

```bash
cd /Users/pw/ai/myinvest/investapp
streamlit run investapp/app.py
```

### 方法2: 指定端口

```bash
cd /Users/pw/ai/myinvest/investapp
streamlit run investapp/app.py --server.port 8501
```

### 方法3: 后台运行

```bash
cd /Users/pw/ai/myinvest/investapp
nohup streamlit run investapp/app.py > streamlit.log 2>&1 &
```

## 📱 访问应用

启动后访问: **http://localhost:8501**

## 📋 可用页面

### 原有页面
1. 🏠 **Home** - 主页
2. 📊 **Dashboard** - 仪表盘（已修复）
3. 📝 **Records** - 投资记录
4. 📈 **Market** - 市场数据（已修复）
5. 📋 **Logs** - 日志查看
6. ⚙️ **System Status** - 系统状态
7. 🔬 **Backtest** - 回测工具
8. 📅 **Scheduler Log** - 调度日志
9. ✅ **Approval** - 审批流程

### 新增页面 ⭐
10. **🎯 Strategies** (9_strategies.py) - 策略管理中心
    - 查看所有策略
    - 按标签/风险/频率筛选
    - 策略详情和对比

11. **🔄 Rotation Strategy** (10_rotation_strategy.py) - 市场轮动策略
    - 实时监控大盘
    - 自动检测买入信号
    - 调整策略参数

## 🎯 新功能亮点

### 策略管理页面

**功能**:
- 📊 查看所有投资策略
- 🔍 智能筛选（标签、风险、频率）
- 📖 查看详细参数和使用示例
- ⚖️ 策略对比工具

**使用场景**:
1. 浏览所有可用策略
2. 对比不同策略特点
3. 查看代码示例
4. 了解策略参数

### 市场轮动策略页面

**功能**:
- 📊 监控大盘指数（沪深300/上证/中证500）
- 🚨 自动检测买入信号
- ⚙️ 可调整策略参数
- 💡 实时操作建议

**核心逻辑**:
```
监控大盘 → 连续2日跌≤-1.5% → 买入中证1000 ETF → 持有20日 → 切回国债
```

**使用场景**:
1. 每日检查是否触发信号
2. 调整参数适应市场
3. 查看历史触发记录

## 🧪 测试新功能

### 1. 测试策略导入

```bash
python -c "from investlib_quant.strategies import StrategyRegistry; StrategyRegistry.print_summary()"
```

### 2. 测试命令行工具

```bash
# 查看所有策略
python scripts/show_strategies.py

# 查看特定策略
python scripts/show_strategies.py market_rotation_panic_buy
```

### 3. 测试回测示例

```bash
python examples/rotation_strategy_example.py
```

## 🐛 常见问题

### Q: 页面显示 "ModuleNotFoundError"

**A**: 已修复。如果仍有问题：
```bash
# 重新安装 investlib-quant
cd /Users/pw/ai/myinvest/investlib-quant
pip install -e .

# 重启 Streamlit
```

### Q: 页面加载缓慢

**A**: 首次加载需要获取数据，请耐心等待。可以：
- 检查网络连接
- 查看是否有数据缓存

### Q: 策略页面显示 "策略数量为0"

**A**: 确保策略已注册：
```bash
python -c "from investlib_quant.strategies import StrategyRegistry; print(len(StrategyRegistry.list_all()))"
```
应该显示至少2个策略。

### Q: 如何停止 Streamlit

**A**:
- 前台运行: `Ctrl + C`
- 后台运行: `pkill -f streamlit`

## 📚 相关文档

- `QUICK_START.md` - 快速开始指南
- `STRATEGY_GUIDE.md` - 完整策略文档
- `investapp/NEW_FEATURES.md` - 新功能详细说明

## 🔄 更新日志

### v0.2 (2025-10-22)
- ✅ 修复所有页面导入错误
- ✅ 新增策略管理页面
- ✅ 新增市场轮动策略页面
- ✅ 实现策略注册系统
- ✅ 实现多品种轮动回测

## 📞 需要帮助？

查看详细文档或运行测试命令确认功能正常。

---

**准备好了吗？运行下面的命令启动应用：**

```bash
cd /Users/pw/ai/myinvest/investapp && streamlit run investapp/app.py
```

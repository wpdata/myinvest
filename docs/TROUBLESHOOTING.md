# 🔧 MyInvest 问题排查和反馈指南

## 📌 快速诊断流程

### 步骤 1: 运行自动诊断

```bash
cd /Users/pw/ai/myinvest
./scripts/diagnose_issue.sh
```

这会生成一个完整的诊断报告在 `debug_reports/` 目录。

---

## 🐛 常见问题和解决方案

### 问题 1: Streamlit 应用无法启动

**现象**:
```
ModuleNotFoundError: No module named 'investlib_data'
```

**解决方案**:
```bash
# 重新安装库
pip install -e investlib-data
pip install -e investlib-quant
pip install -e investlib-advisors
pip install -e investapp
```

---

### 问题 2: 数据库错误

**现象**:
```
sqlalchemy.exc.OperationalError: no such table: investment_records
```

**解决方案**:
```bash
# 初始化数据库
python -m investlib_data.cli init-db
```

---

### 问题 3: 市场数据获取失败

**现象**:
```
TushareAPIError: Invalid token
```

**解决方案**:
1. 检查 `.env` 文件中的 `TUSHARE_TOKEN`
2. 或者系统会自动降级使用 AKShare（无需 token）

```bash
# 测试 AKShare
python -c "from investlib_data.market_api import AKShareClient; c = AKShareClient(); print('AKShare OK')"
```

---

### 问题 4: 页面显示空白或加载失败

**现象**: 页面一直显示 "Loading..." 或空白

**解决方案**:
```bash
# 1. 检查浏览器控制台（F12）是否有 JavaScript 错误
# 2. 清除 Streamlit 缓存
streamlit cache clear

# 3. 重启应用
# Ctrl+C 停止，然后重新运行
streamlit run investapp/investapp/app.py
```

---

### 问题 5: CSV 导入失败

**现象**: "所有记录都被拒绝"

**解决方案**:
检查 CSV 格式是否正确：

```csv
symbol,purchase_date,purchase_price,quantity,sale_date,sale_price
600519.SH,2023-01-15,1500.00,100,,
000001.SZ,2023-02-20,12.50,1000,2023-06-15,14.80
```

**验证规则**:
- `symbol`: 必须格式为 `XXXXXX.SH` 或 `XXXXXX.SZ`
- `purchase_price`: 必须 > 0
- `quantity`: 必须 > 0
- `purchase_date`: 不能晚于今天

---

## 📊 如何反馈页面测试问题

### 完整反馈流程

#### 第 1 步: 收集信息

运行诊断脚本：
```bash
./scripts/diagnose_issue.sh
```

#### 第 2 步: 记录问题

创建问题报告文件：
```bash
cp .github/ISSUE_TEMPLATE.md debug_reports/my_issue.md
```

编辑文件，填写：
1. 问题类型
2. 问题页面
3. 预期行为 vs 实际行为
4. 重现步骤
5. 错误消息（完整复制）

#### 第 3 步: 截图/录屏

**推荐工具**:
- macOS: Cmd+Shift+5 (内置截图)
- Windows: Win+Shift+S
- 录屏: QuickTime (macOS) / OBS Studio

**需要截图的内容**:
1. 错误页面截图
2. 浏览器控制台错误 (F12 → Console)
3. Streamlit 终端输出

#### 第 4 步: 提交反馈

**方式 1: 直接告诉 Claude**

```
我在测试市场数据页面时遇到问题：

页面: 3_market.py
错误: 点击"查询数据"按钮后页面崩溃
错误消息: [粘贴完整错误]
重现步骤:
1. 打开市场数据页面
2. 输入股票代码 600519.SH
3. 点击查询按钮
4. 页面显示 KeyError: 'timestamp'

诊断报告: [附上 diagnose_issue.sh 的输出]
```

**方式 2: 创建 GitHub Issue**

如果项目在 GitHub，使用模板创建 Issue。

---

## 🔍 高级调试技巧

### 1. 查看 Streamlit 日志

```bash
# 启动应用时启用详细日志
streamlit run investapp/investapp/app.py --logger.level=debug
```

### 2. Python 调试模式

在代码中添加断点：
```python
import pdb; pdb.set_trace()
```

### 3. 检查数据库内容

```bash
# 使用 SQLite CLI
sqlite3 data/myinvest.db

# 查看表
.tables

# 查看数据
SELECT * FROM investment_records LIMIT 5;
```

### 4. 手动测试 API

```bash
# 测试市场数据获取
python -c "
from investlib_data.market_api import MarketDataFetcher
fetcher = MarketDataFetcher()
result = fetcher.fetch_with_fallback('600519.SH')
print(f'Records: {len(result[\"data\"])}')
"
```

---

## 📝 问题反馈模板（纯文本版）

```
=== MyInvest 问题反馈 ===

【问题类型】
UI错误 / 功能异常 / 数据问题 / 性能问题

【问题页面】
仪表盘 / 投资记录 / 市场数据 / 操作日志

【问题描述】
预期行为: [我期望...]
实际行为: [但实际...]

【错误消息】
[完整的错误堆栈]

【重现步骤】
1.
2.
3.

【环境信息】
- OS: macOS 14.6
- Python: 3.11.13
- Streamlit: 1.50.0
- 浏览器: Chrome 120

【诊断报告】
[粘贴 diagnose_issue.sh 的输出]

【截图】
[附上截图]
```

---

## 🆘 紧急问题快速反馈

如果遇到**阻塞性问题**（完全无法使用），立即提供：

```bash
# 1. 运行快速诊断
./scripts/diagnose_issue.sh > emergency_report.txt

# 2. 收集完整错误
streamlit run investapp/investapp/app.py 2>&1 | tee streamlit_error.log

# 3. 提供这两个文件
```

然后直接告诉我：
```
紧急问题！应用无法启动/崩溃

错误类型: [启动失败/运行崩溃/数据丢失]
附件:
- emergency_report.txt
- streamlit_error.log
- 截图
```

---

## ✅ 提交前检查清单

提交问题反馈前，请确认：

- [ ] 已运行 `./scripts/diagnose_issue.sh`
- [ ] 已尝试重启应用
- [ ] 已检查 `.env` 配置
- [ ] 已提供完整错误消息（不要截断）
- [ ] 已提供重现步骤（详细且可操作）
- [ ] 已附上截图（如果是 UI 问题）
- [ ] 已查看 [常见问题](#-常见问题和解决方案) 部分

---

## 📞 获取帮助

1. **运行诊断**: `./scripts/diagnose_issue.sh`
2. **查看日志**: `debug_reports/` 目录
3. **反馈问题**: 使用上述模板告诉 Claude 或创建 GitHub Issue
4. **查阅文档**: `docs/` 目录和 `specs/001-myinvest-v0-1/quickstart.md`

---

**记住**: 详细的问题描述 = 更快的解决方案！🚀

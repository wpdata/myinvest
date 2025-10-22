# MyInvest - 智能投资分析系统 v0.1

MyInvest 是一个基于 Python 的个人投资分析与模拟交易系统，整合个人历史投资记录、市场实时数据，并结合 AI 顾问（参考 Livermore 投资哲学）提供智能化的投资建议。

## ✨ 核心特性

### 📊 四大核心功能

1. **投资记录管理** (User Story 1)
   - CSV 批量导入/手动录入
   - 持仓自动计算
   - 收益曲线可视化
   - 资产分布分析

2. **AI 投资推荐** (User Story 2)
   - Livermore 趋势跟随策略
   - 自动止损/止盈计算
   - 风险收益评估
   - 历史案例参考

3. **模拟交易执行** (User Story 3)
   - 二次确认流程
   - 仓位限制验证（单只≤20%）
   - 操作日志（不可篡改）
   - 持仓实时更新

4. **市场数据查询** (User Story 4)
   - K线图展示（日/周/月）
   - 120日均线叠加
   - 成交量分析
   - 数据新鲜度指示

### 🛡️ 安全与合规

- **📊 数据整合**: 支持 Efinance/AKShare 双数据源，自动故障切换（免费，无需API Token）
- **🧠 AI 顾问**: 基于模板的 Livermore 投资顾问，提供可解释的建议
- **📈 量化策略**: Livermore 趋势跟随策略（120日均线突破 + 成交量确认）
- **🛡️ 风险控制**: 强制止损、仓位限制（≤20%）、操作审批流程
- **💾 数据缓存**: 7天缓存机制，减少 API 调用，降级保护
- **🔍 完整审计**: 所有操作记录到 SQLite 数据库，append-only 日志

## 🚀 快速开始

### 1. 环境准备

**系统要求:**
- Python 3.10+
- Git

**克隆仓库:**
```bash
git clone <your-repo-url>
cd myinvest
git checkout 001-myinvest-v0-1
```

### 2. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装库（开发模式）
pip install -e investlib-data
pip install -e investlib-quant
pip install -e investlib-advisors
pip install -e investapp
```

### 3. 配置环境变量

复制环境变量模板并编辑:
```bash
cp .env.example .env
```

编辑 `.env` 文件（可选，使用默认配置即可）：
```env
DATABASE_URL=sqlite:///data/myinvest.db
CACHE_DIR=data/cache

# 注意：Efinance 为主数据源（免费，无需 Token）
# AKShare 为备份数据源
```

### 4. 初始化数据库

```bash
python -m investlib_data.cli init-db
```

### 5. 启动 Streamlit 应用

```bash
streamlit run investapp/investapp/app.py
```

访问 http://localhost:8501 开始使用！

## 📖 使用示例

### CLI 命令

```bash
# 初始化数据库
investlib-data init-db

# 导入投资记录
investlib-data import-csv --file records.csv

# 获取市场数据
investlib-data fetch-market --symbol 600519.SH --output json

# 生成投资分析
investlib-quant analyze --symbol 600519.SH --strategy livermore --capital 100000

# 查询 AI 顾问建议
investlib-advisors ask --advisor livermore --context signal.json

# 查看可用顾问
investlib-advisors list-advisors
```

### Web 界面

1. **仪表盘** - 查看投资组合概览和生成推荐
2. **投资记录管理** - 导入/编辑投资记录
3. **市场数据** - 查询K线图和市场数据
4. **操作日志** - 查看所有交易操作记录

完整使用指南见 `specs/001-myinvest-v0-1/quickstart.md`

## 🏗️ 项目结构

```
myinvest/
├── investlib-data/          # 数据管理库（市场数据、投资记录、缓存）
├── investlib-quant/         # 量化策略库（Livermore 策略、信号生成）
├── investlib-advisors/      # AI 顾问库（推荐生成、解释）
├── investapp/               # Streamlit Web 应用
├── tests/                   # 集成测试
├── data/                    # 数据存储（SQLite 数据库、缓存）
└── specs/                   # 需求文档和任务清单
```

## 🧪 测试

运行所有测试：
```bash
# 合约测试（CLI 接口）
pytest */tests/contract -v

# 集成测试（真实 API）
pytest */tests/integration -v

# 覆盖率报告
pytest --cov=investlib_data --cov=investlib_quant --cov=investlib_advisors --cov-report=html
```

## 📋 架构合规性

严格遵守 MyInvest Constitution 规范：

✅ **Library-First** - 所有业务逻辑在 investlib-* 库中
✅ **CLI Interface** - 所有库提供 CLI 命令（--help, --dry-run, JSON 输出）
✅ **Test-First** - TDD 开发流程，先写测试后实现
✅ **Data Integrity** - 所有数据包含来源、时间戳、校验和
✅ **Investment Safety** - 强制止损、仓位限制、审批流程、append-only 日志

## 📊 实现进度

- ✅ Phase 1-2: 基础设施 & 数据层 (T001-T034)
- ✅ Phase 3: User Story 1 - 导入和查看 (T035)
- ✅ Phase 4: User Story 2 - 投资推荐 (T036-T051)
- ✅ Phase 5: User Story 3 - 模拟交易 (T052-T063)
- ✅ Phase 6: User Story 4 - 市场数据 (T064-T073)
- 🔄 Phase 7: 收尾和文档 (T074-T078)

**总进度**: 73/78 tasks (94%)

## ⚠️ 免责声明

本系统仅供学习研究使用，不构成投资建议。

- v0.1 版本**仅支持模拟交易**，无真实资金交易功能
- 所有推荐基于历史数据和技术分析，不保证未来收益
- 投资有风险，决策需谨慎

## 📝 许可证

本项目采用 MIT 许可证


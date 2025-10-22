# MyInvest v0.1 技术架构设计

## 1. 架构总览

### 1.1 高层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface Layer                        │
│                    (Streamlit Web App)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 投资概览页面  │  │ 今日推荐页面  │  │ 操作日志页面        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Application Orchestration Layer                 │
│                      (investapp)                                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Google ADK Orchestrator                          │   │
│  │  • Agent coordination (Livermore Advisor)                │   │
│  │  • Session state management                              │   │
│  │  • Workflow orchestration                                │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────┬──────────────┬──────────────┬──────────────────────┘
            │              │              │
    ┌───────▼──────┐  ┌───▼──────────┐  ┌▼──────────────┐
    │ investlib-   │  │ investlib-   │  │ investlib-    │
    │ data         │  │ quant        │  │ advisors      │
    │              │  │              │  │               │
    │ • 数据采集   │  │ • 策略计算   │  │ • Livermore   │
    │ • 数据存储   │  │ • 信号生成   │  │   Agent       │
    │ • 数据验证   │  │ • 风控计算   │  │ • Prompt      │
    │              │  │              │  │   版本管理    │
    └──────┬───────┘  └──────────────┘  └───────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                    Data & Cache Layer                            │
│                                                                   │
│  ┌──────────────────┐        ┌────────────────────────────┐    │
│  │   PostgreSQL     │        │        Redis Cache         │    │
│  │   (Docker)       │        │        (Docker)            │    │
│  │                  │        │                            │    │
│  │ • 投资记录表     │        │ • 市场数据缓存             │    │
│  │ • 操作日志表     │        │ • 会话状态缓存             │    │
│  │ • 持仓表         │        │ • API 响应缓存             │    │
│  │ • 建议记录表     │        │   (TTL: 1h)                │    │
│  └──────────────────┘        └────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                    External Services Layer                       │
│                                                                   │
│  ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐ │
│  │  Tushare API     │ │  AKShare API    │ │ Google Gemini API│ │
│  │  (Primary Data)  │ │ (Fallback Data) │ │ (for ADK Agents) │ │
│  └──────────────────┘ └─────────────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈

### 2.1 核心技术

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| **Frontend** | Streamlit | 1.40+ | 主流 Python Web 框架，适合数据展示；与 ADK 集成简单 |
| **Agent Framework** | Google ADK | Latest | 官方推荐的 Agent 编排框架，支持 LLM Agent |
| **Backend Language** | Python | 3.10+ | 生态成熟，数据分析库丰富 |
| **Database** | PostgreSQL | 16+ (Docker) | 可靠的关系型数据库，支持复杂查询 |
| **Cache** | Redis | 7+ (Docker) | 高性能缓存，减少 API 调用次数 |
| **LLM Provider** | Google Gemini | 2.0 Flash | ADK 默认支持，速度快，成本低 |
| **Market Data API** | Tushare / AKShare | Latest | 国内主流金融数据源，增加备用数据源提高稳定性 |
| **Backtesting Engine**| Backtrader | 1.9+ | 功能强大、社区活跃的量化回测引擎 (用于 v0.2) |

### 2.2 关键 Python 库

| Library | Purpose | Version |
|---------|---------|---------|
| `streamlit` | Web UI 框架 | 1.40+ |
| `google-adk` | Agent 编排 | Latest |
| `psycopg2-binary` | PostgreSQL 驱动 | 2.9+ |
| `redis` | Redis 客户端 | 5.0+ |
| `tushare` | 主要市场数据 API | Latest |
| `akshare` | 备用市场数据 API | Latest |
| `backtrader` | 量化回测引擎 | 1.9+ |
| `pandas` | 数据处理 | 2.2+ |
| `plotly` | 图表可视化 | 5.22+ |
| `pydantic` | 数据验证 | 2.0+ |
| `click` | CLI 框架 | 8.1+ |
| `pytest` | 测试框架 | 8.0+ |
| `python-dotenv` | 环境变量管理 | 1.0+ |

---

## 3. 项目结构

### 3.1 目录结构

```
myinvest/
├── docker-compose.yml          # Docker 编排文件（PostgreSQL + Redis）
├── .env.example                # 环境变量模板
├── requirements.txt            # 依赖列表
├── README.md                   # 项目说明
│
├── investlib-data/             # 数据采集与管理库
│   ├── src/
│   │   ├── investlib_data/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── data_fetcher.py      # 统一数据获取器 (Tushare/AKShare)
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── market_data.py       # 市场数据模型
│   │   │   │   └── investment_record.py # 投资记录模型
│   │   │   ├── storage/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── db.py                # 数据库连接与操作
│   │   │   │   └── cache.py             # Redis 缓存操作
│   │   │   ├── validation/
│   │   │   │   ├── __init__.py
│   │   │   │   └── validators.py        # 数据验证逻辑
│   │   │   └── cli.py                   # CLI 入口
│   │   └── tests/
│   │       ├── test_data_fetcher.py
│   │       └── test_validators.py
│   ├── pyproject.toml          # 包配置（Poetry）
│   └── README.md
│
├── investlib-quant/            # 量化策略库
│   ├── src/
│   │   ├── investlib_quant/
│   │   │   ├── __init__.py
│   │   │   ├── strategies/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py              # 策略基类
│   │   │   │   └── livermore.py         # Livermore 趋势策略
│   │   │   ├── signals/
│   │   │   │   ├── __init__.py
│   │   │   │   └── signal_generator.py  # 信号生成器
│   │   │   ├── risk/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── position_sizer.py    # 仓位计算
│   │   │   │   └── stop_loss.py         # 止损计算
│   │   │   └── cli.py
│   │   └── tests/
│   │       ├── test_livermore.py
│   │       └── test_signal_generator.py
│   ├── pyproject.toml
│   └── README.md
│
├── investlib-advisors/         # AI 顾问库
│   ├── src/
│   │   ├── investlib_advisors/
│   │   │   ├── __init__.py
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_advisor.py      # Advisor 基类
│   │   │   │   └── livermore_agent.py   # Livermore Agent
│   │   │   ├── prompts/
│   │   │   │   ├── __init__.py
│   │   │   │   └── livermore-v1.0.0.md  # Prompt 版本文件
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── input_schema.py      # Agent 输入 Schema
│   │   │   │   └── output_schema.py     # Agent 输出 Schema
│   │   │   └── cli.py
│   │   └── tests/
│   │       └── test_livermore_agent.py
│   ├── pyproject.toml
│   └── README.md
│
└── investapp/                  # 主应用（Orchestrator）
    ├── src/
    │   ├── investapp/
    │   │   ├── __init__.py
    │   │   ├── app.py                   # Streamlit 主入口
    │   │   ├── orchestrator/
    │   │   │   ├── __init__.py
    │   │   │   ├── adk_setup.py         # Google ADK 初始化
    │   │   │   └── recommendation_flow.py # 建议生成流程
    │   │   ├── pages/
    │   │   │   ├── __init__.py
    │   │   │   ├── overview.py          # 投资概览页面
    │   │   │   ├── recommendations.py   # 今日推荐页面
    │   │   │   └── operation_log.py     # 操作日志页面
    │   │   ├── components/
    │   │   │   ├── __init__.py
    │   │   │   ├── recommendation_card.py # 建议卡片组件
    │   │   │   ├── charts.py            # 图表组件
    │   │   │   └── mode_indicator.py    # 模式指示器组件
    │   │   └── config/
    │   │       ├── __init__.py
    │   │       └── settings.py          # 配置管理
    │   └── tests/
    │       └── test_orchestrator.py
    ├── requirements.txt
    └── README.md
```

---

## 4. 核心组件设计

### 4.1 investlib-data (数据层)

#### 4.1.1 职责
- 从多个数据源 (Tushare, AKShare) 获取市场数据，并提供故障切换 (Failover) 机制。
- 管理个人投资记录的 CRUD 操作。
- 数据验证与完整性检查。
- Redis 缓存管理。

#### 4.1.2 核心类设计

**`DataFetcher` (data_fetcher.py)**

```python
import tushare as ts
import akshare as ak
import redis
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class DataFetcher:
    """
    统一数据获取器，支持多数据源和缓存。
    - 主要数据源: Tushare
    - 备用数据源: AKShare
    """

    def __init__(self, tushare_token: str, redis_client: redis.Redis):
        self.tushare_api = ts.pro_api(tushare_token)
        self.redis = redis_client
        self.cache_ttl = 3600  # 1小时缓存

    def get_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        获取日线行情数据，实现 Tushare -> AKShare 的故障切换。

        Args:
            symbol: 股票代码 (Tushare: 600519.SH, AKShare: 600519)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            use_cache: 是否使用缓存

        Returns:
            成功时返回包含数据和元数据的字典，失败时返回 None。
        """
        cache_key = f"market_data:{symbol}:{start_date}:{end_date}"

        if use_cache:
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        # 优先尝试 Tushare
        try:
            data = self._fetch_from_tushare(symbol, start_date, end_date)
            source = "Tushare"
        except Exception as e:
            print(f"Tushare fetch failed: {e}. Trying AKShare...")
            # Tushare 失败，尝试 AKShare
            try:
                # 需要转换 symbol 格式
                ak_symbol = symbol.split('.')[0]
                data = self._fetch_from_akshare(ak_symbol, start_date, end_date)
                source = "AKShare"
            except Exception as e_ak:
                print(f"AKShare fetch failed: {e_ak}. All sources failed.")
                return None

        if data is None or data.empty:
            return None

        result = {
            "symbol": symbol,
            "data": data.to_dict(orient='records'),
            "metadata": {
                "source": source,
                "retrieval_timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }

        self.redis.setex(cache_key, self.cache_ttl, json.dumps(result))
        return result

    def _fetch_from_tushare(self, symbol: str, start_date: str, end_date: str):
        """从 Tushare 获取数据"""
        df = self.tushare_api.daily(
            ts_code=symbol,
            start_date=start_date,
            end_date=end_date,
            adj='qfq'
        )
        # ... (此处省略数据清洗和格式统一)
        return df

    def _fetch_from_akshare(self, symbol: str, start_date: str, end_date: str):
        """从 AKShare 获取数据"""
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        # ... (此处省略数据清洗和格式统一)
        return df
```

**`InvestmentRecord` (投资记录模型)**

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Literal

class InvestmentRecord(BaseModel):
    """投资记录数据模型"""

    id: Optional[int] = None
    symbol: str = Field(..., description="标的代码，如 600519.SH")
    symbol_name: str = Field(..., description="标的名称，如 贵州茅台")
    action: Literal["BUY", "SELL"] = Field(..., description="操作类型")
    price: float = Field(..., gt=0, description="成交价格")
    quantity: int = Field(..., gt=0, description="数量（股）")
    amount: float = Field(..., gt=0, description="总金额")
    trade_date: datetime = Field(..., description="交易日期")

    # 数据完整性字段
    source: Literal["manual_entry", "broker_statement", "api_import"]
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None

    # 可选字段
    notes: Optional[str] = None

    @validator("trade_date")
    def trade_date_not_future(cls, v):
        if v > datetime.now():
            raise ValueError("交易日期不能是未来时间")
        return v

    @validator("amount")
    def amount_matches_price_quantity(cls, v, values):
        """验证总金额 = 价格 × 数量"""
        if "price" in values and "quantity" in values:
            expected = values["price"] * values["quantity"]
            if abs(v - expected) > 0.01:  # 允许0.01的浮点误差
                raise ValueError(
                    f"金额不匹配：期望 {expected}，实际 {v}"
                )
        return v
```

**CLI 接口 (cli.py)**

```python
import click
import json
import os
from .api.data_fetcher import DataFetcher
from .storage.db import get_db_connection
from .storage.cache import get_redis_client

@click.group()
def cli():
    """investlib-data CLI"""
    pass

@cli.command()
@click.option('--symbol', required=True, help='股票代码，如 600519.SH')
@click.option('--start', required=True, help='开始日期 YYYYMMDD')
@click.option('--end', required=True, help='结束日期 YYYYMMDD')
@click.option('--output', type=click.Choice(['json', 'csv']), default='json')
@click.option('--no-cache', is_flag=True, help='不使用缓存')
def fetch(symbol, start, end, output, no_cache):
    """获取市场数据"""
    fetcher = DataFetcher(
        tushare_token=os.getenv("TUSHARE_TOKEN"),
        redis_client=get_redis_client()
    )

    data = fetcher.get_daily_data(
        symbol=symbol,
        start_date=start,
        end_date=end,
        use_cache=not no_cache
    )

    if data:
        if output == 'json':
            click.echo(json.dumps(data, indent=2))
        else:
            # CSV 输出逻辑
            pass
    else:
        click.echo("Failed to fetch data from all sources.", err=True)


if __name__ == '__main__':
    cli()
```

---

### 4.2 investlib-quant (策略层)

#### 4.2.1 职责
- 实现 Livermore 趋势跟随策略
- 生成买入/卖出信号
- 计算止损、止盈、仓位

#### 4.2.2 核心类设计

**`LivermoreStrategy` (livermore.py)**

```python
from typing import Dict, Optional
import pandas as pd
from .base import BaseStrategy

class LivermoreStrategy(BaseStrategy):
    """
    Livermore 趋势跟随策略

    核心逻辑：
    1. 价格突破 120 日均线 → 买入信号
    2. 成交量放大 30% → 确认信号
    3. 止损设置为入场价 -3.5%
    4. 止盈设置为入场价 +7%
    """

    def __init__(self, ma_period: int = 120, volume_threshold: float = 1.3):
        self.ma_period = ma_period
        self.volume_threshold = volume_threshold

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """
        生成交易信号

        Args:
            market_data: DataFrame with columns [date, open, high, low, close, volume]

        Returns:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "entry_price": 1680.0,
                "stop_loss": 1620.0,
                "take_profit": 1800.0,
                "position_size_pct": 15,
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": {
                    "ma_breakout": True,
                    "volume_surge": True,
                    "current_price": 1680.0,
                    "ma_120": 1650.0,
                    "volume_ratio": 1.35
                }
            }
        """
        if len(market_data) < self.ma_period:
            return None  # 数据不足

        # 计算技术指标
        market_data['ma_120'] = market_data['close'].rolling(self.ma_period).mean()
        market_data['volume_ma_20'] = market_data['volume'].rolling(20).mean()

        latest = market_data.iloc[-1]
        prev = market_data.iloc[-2]

        current_price = latest['close']
        ma_120 = latest['ma_120']
        volume_ratio = latest['volume'] / latest['volume_ma_20']

        # 判断信号
        ma_breakout = (prev['close'] < prev['ma_120']) and (current_price > ma_120)
        volume_surge = volume_ratio > self.volume_threshold

        if ma_breakout and volume_surge:
            # 买入信号
            stop_loss = current_price * 0.965  # -3.5%
            take_profit = current_price * 1.07  # +7%

            return {
                "action": "BUY",
                "entry_price": current_price,
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
                "position_size_pct": 15,
                "confidence": "HIGH" if volume_ratio > 1.5 else "MEDIUM",
                "reasoning": {
                    "ma_breakout": True,
                    "volume_surge": True,
                    "current_price": current_price,
                    "ma_120": round(ma_120, 2),
                    "volume_ratio": round(volume_ratio, 2)
                }
            }

        return {"action": "HOLD"}
```

---

### 4.3 investlib-advisors (AI 顾问层)

(此部分无重大变更，内容省略)

---

### 4.4 investapp (应用编排层)

(此部分无重大变更，内容省略)

---

## 5. 数据库 Schema

(此部分无重大变更，内容省略)

---

## 6. Docker 部署

(此部分无重大变更，内容省略)

---

## 7. 数据流示例

(此部分无重大变更，内容省略)

---

## 8. 测试策略

(此部分无重大变更，内容省略)

---

## 9. 部署与运维

(此部分无重大变更，内容省略)

---

## 10. Constitution 合规性检查

(此部分无重大变更，内容省略)

---

## 11. 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| **数据源 API 失败/限流** | **高** | **实现 Tushare -> AKShare 的故障切换机制；使用 Redis 缓存热门标的。** |
| Google ADK 学习曲线 | 中 | 提供详细代码示例；先实现简单 Agent。 |
| PostgreSQL 连接池耗尽 | 中 | 使用 psycopg2 连接池；设置 max_connections=100。 |
| Prompt 版本管理混乱 | 低 | 强制语义化版本号；Git 追踪 prompts/ 目录。 |
| Advisor 输出格式不稳定 | 高 | 使用 Pydantic 强制验证输出 Schema。 |

---

## 12. 后续步骤 (v0.1 之后)

### 12.1 v0.2 功能扩展
- **使用 `backtrader` 框架实现 `investlib-backtest` 回测库。**
- 添加 Kroll Advisor。
- 支持多策略融合。

### 12.2 性能优化
- 实现 PostgreSQL 连接池。
- 增加 Redis 缓存命中率监控。
- 优化 Streamlit 页面加载速度。

### 12.3 监控与告警
- 添加 Prometheus metrics。
- **配置数据源 API 调用失败告警。**
- 配置 PostgreSQL 慢查询日志。

---

**文档版本**: v1.1
**更新日期**: 2025-10-14
**作者**: Architecture Team
**审批状态**: ✅ 通过宪章合规性检查
# MyInvest 快速启动指南

## 启动服务

```bash
cd /Users/pw/ai/myinvest
./start_dashboard.sh
```

访问: http://localhost:8501

## 检查配置

```bash
./check_database.sh
```

所有检查项应该显示 ✓

## 常见问题

### 1. 策略推荐按钮报错

**症状**: 点击推荐按钮后出现错误

**解决方案**:
```bash
# 检查是否有多个服务运行
ps aux | grep streamlit | grep -v grep

# 如果有多个，停止所有服务
pkill -f streamlit

# 重新启动
./start_dashboard.sh
```

### 2. 找不到数据库表

**症状**: `no such table: current_holdings`

**解决方案**:
```bash
# 1. 验证数据库配置
./check_database.sh

# 2. 确认数据库表存在
sqlite3 data/myinvest.db ".tables"

# 3. 如果表不存在，重新初始化
cd investlib-data
python -m investlib_data.cli init-db
```

### 3. 端口被占用

**症状**: `Address already in use`

**解决方案**:
```bash
# 找到占用端口的进程
lsof -i :8501

# 停止该进程
kill <PID>

# 或者停止所有 streamlit
pkill -f streamlit
```

## 重要文件

- **`.env`** - 环境配置（数据库路径等）
- **`start_dashboard.sh`** - 启动脚本
- **`check_database.sh`** - 配置检查脚本
- **`DATABASE_PATH_FIX.md`** - 详细的修复说明

## 数据库位置

**唯一正确的数据库**: `/Users/pw/ai/myinvest/data/myinvest.db`

所有其他位置的 `myinvest.db` 都是错误的或过时的。

## 验证系统状态

运行检查脚本应该看到：

```
✓ .env 文件存在
✓ 使用绝对路径
✓ 主数据库存在
✓ 表数量: 13
✓ current_holdings 表存在
✓ market_data 表存在
✓ 1 个 Streamlit 服务正在运行
✓ 没有发现相对路径
```

## 获取帮助

1. 阅读 `DATABASE_PATH_FIX.md` 了解详细的问题和解决方案
2. 运行 `./check_database.sh` 诊断问题
3. 检查 Streamlit 日志获取错误信息

## 最后更新

2025-10-23 - 数据库路径问题完全修复

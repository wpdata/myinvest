# MyInvest Constitution

## Core Principles

### I. 中文优先 (Chinese-First Interface)
**所有用户界面必须使用中文**
- 所有 Streamlit 页面、标题、说明文字必须使用中文
- 用户可见的所有文本（按钮、标签、提示信息、错误消息等）必须使用中文
- 技术文档可以使用英文，但面向用户的文档必须使用中文
- 变量名、函数名、注释可以使用英文（符合 Python 规范）
- 异常：技术术语（如 Sharpe Ratio, API）可保留英文，但需提供中文说明

### II. Library-First Architecture
**每个功能首先作为独立的库实现**
- 库必须独立、可测试、有文档
- 每个库有明确的目的
- 库之间低耦合

### III. Test-First Development (NON-NEGOTIABLE)
**测试驱动开发是强制性的**
- 先写测试 → 用户批准 → 测试失败 → 实现代码
- 严格遵循 Red-Green-Refactor 循环
- 所有新功能必须有对应测试

### IV. Integration Testing
**关注以下领域的集成测试**
- 新库的契约测试
- 契约变更
- 服务间通信
- 共享模式

### V. Data Quality & Freshness
**数据质量和新鲜度监控**
- 所有市场数据必须标注数据源
- 显示数据新鲜度指标
- 实现 API 失败回退机制
- 缓存策略透明化

## User Experience Standards

### 界面设计要求
- **语言**：所有用户界面必须使用中文
- **一致性**：界面风格、术语使用保持一致
- **可读性**：使用清晰的标题层级和分组
- **反馈**：所有操作提供明确的成功/失败反馈
- **帮助**：提供使用说明和示例

### 错误处理
- 所有错误消息必须用中文表述
- 错误消息应具体、可操作
- 提供问题解决建议
- 记录详细的错误日志供调试

## Development Workflow

### Code Quality Gates
- 所有代码必须通过 linting (ruff check)
- 所有测试必须通过 (pytest)
- 新功能必须有测试覆盖
- Pull Request 需要审查

### Streamlit UI Guidelines
1. **页面标题**：使用 `st.title()` 设置中文标题
2. **配置**：使用 `st.set_page_config()` 设置中文 page_title
3. **说明文字**：使用 `st.markdown()` 提供中文说明
4. **表单标签**：所有输入框、按钮使用中文标签
5. **反馈消息**：`st.success()`, `st.error()`, `st.warning()` 使用中文

## Governance

本章程优先于所有其他实践和规范。

### 修订流程
- 章程修订需要文档记录
- 重大修改需要迁移计划
- 所有 PR/审查必须验证章程合规性

### 审核标准
- 新页面必须检查是否使用中文界面
- 复杂度需要充分理由
- 遵循最简原则 (YAGNI)

**Version**: 1.0.0 | **Ratified**: 2025-10-21 | **Last Amended**: 2025-10-21
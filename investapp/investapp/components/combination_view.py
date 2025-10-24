"""
Combination Holdings View Component (T056)

Reusable component to display multi-leg combination positions
with expandable leg details.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict


def render_combination_holdings(combinations: List[Dict]):
    """Render combination positions with expandable legs.

    Args:
        combinations: List of combination dicts with:
            - combination_id: str
            - strategy_name: str
            - strategy_type: str
            - status: 'active' | 'closed'
            - entry_date: str
            - legs: List[Dict] with leg details
            - total_pnl: float
            - total_margin: float
            - greeks: Dict (if options)

    Example:
        >>> combinations = [
        ...     {
        ...         'combination_id': 'combo_001',
        ...         'strategy_name': '备兑开仓 - 600519.SH',
        ...         'strategy_type': 'covered_call',
        ...         'status': 'active',
        ...         'entry_date': '2025-01-15',
        ...         'legs': [
        ...             {'leg_id': 'leg1', 'asset_type': 'stock', ...},
        ...             {'leg_id': 'leg2', 'asset_type': 'call', ...}
        ...         ],
        ...         'total_pnl': 5000.0,
        ...         'total_margin': 180000.0,
        ...         'greeks': {'delta': 0.4, 'gamma': 0.02}
        ...     }
        ... ]
        >>> render_combination_holdings(combinations)
    """
    if not combinations:
        st.info("📭 当前没有组合策略持仓")
        return

    st.subheader(f"📊 组合策略持仓 ({len(combinations)})")

    for combo in combinations:
        # Combination summary card
        with st.expander(
            f"🎯 {combo['strategy_name']} | "
            f"腿数: {len(combo['legs'])} | "
            f"P&L: ¥{combo['total_pnl']:,.0f}",
            expanded=False
        ):
            # Header row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                status_emoji = "🟢" if combo['status'] == 'active' else "⚫"
                st.markdown(f"**状态:** {status_emoji} {combo['status'].upper()}")

            with col2:
                st.markdown(f"**类型:** {_format_strategy_type(combo['strategy_type'])}")

            with col3:
                st.markdown(f"**入场日期:** {combo['entry_date']}")

            with col4:
                pnl_color = "green" if combo['total_pnl'] >= 0 else "red"
                st.markdown(
                    f"**盈亏:** :"
                    f"{pnl_color}[¥{combo['total_pnl']:,.0f}]"
                )

            st.divider()

            # Margin and Greeks
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "保证金占用",
                    f"¥{combo['total_margin']:,.0f}"
                )

            with col2:
                if combo.get('greeks'):
                    greeks = combo['greeks']
                    st.markdown(
                        f"**Greeks:** Delta={greeks.get('delta', 0):.2f}, "
                        f"Gamma={greeks.get('gamma', 0):.3f}, "
                        f"Theta={greeks.get('theta', 0):.2f}"
                    )

            # Legs table
            st.markdown("### 策略腿明细")

            legs_df = _format_legs_table(combo['legs'])
            st.dataframe(legs_df, use_container_width=True)

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(
                    "📈 查看 P&L 曲线",
                    key=f"pnl_{combo['combination_id']}"
                ):
                    st.session_state[f"show_pnl_{combo['combination_id']}"] = True

            with col2:
                if combo['status'] == 'active':
                    if st.button(
                        "⚠️ 平仓",
                        key=f"close_{combo['combination_id']}"
                    ):
                        st.warning("确认平仓操作？")

            with col3:
                if st.button(
                    "ℹ️ 详细信息",
                    key=f"detail_{combo['combination_id']}"
                ):
                    st.session_state[f"show_detail_{combo['combination_id']}"] = True


def _format_strategy_type(strategy_type: str) -> str:
    """Format strategy type for display."""
    type_map = {
        'covered_call': '备兑开仓',
        'butterfly_spread': '蝶式价差',
        'straddle': '跨式组合',
        'strangle': '宽跨式组合',
        'bull_call_spread': '牛市看涨价差',
        'bear_put_spread': '熊市看跌价差',
        'iron_condor': '铁鹰式组合',
        'calendar_spread': '日历价差',
        'custom': '自定义'
    }
    return type_map.get(strategy_type, strategy_type)


def _format_legs_table(legs: List[Dict]) -> pd.DataFrame:
    """Format legs into DataFrame for display."""
    data = []

    for i, leg in enumerate(legs, 1):
        asset_type_emoji = {
            'stock': '📈',
            'call': '📞',
            'put': '📉',
            'futures': '📊'
        }.get(leg.get('asset_type'), '❓')

        action_emoji = {
            'BUY': '🟢 买入',
            'SELL': '🔴 卖出'
        }.get(leg.get('action'), leg.get('action'))

        data.append({
            '腿': f"Leg {i}",
            '类型': f"{asset_type_emoji} {leg.get('asset_type', 'N/A')}",
            '方向': action_emoji,
            '标的': leg.get('symbol', 'N/A'),
            '数量': leg.get('quantity', 0),
            '入场价': f"¥{leg.get('entry_price', 0):.2f}",
            '行权价': f"¥{leg.get('strike_price', 0):.2f}" if leg.get('strike_price') else 'N/A',
            '到期日': leg.get('expiry_date', 'N/A'),
            '当前盈亏': f"¥{leg.get('current_pnl', 0):,.0f}"
        })

    return pd.DataFrame(data)


# Example usage for testing
if __name__ == '__main__':
    # Sample data
    sample_combinations = [
        {
            'combination_id': 'combo_001',
            'strategy_name': '备兑开仓 - 600519.SH',
            'strategy_type': 'covered_call',
            'status': 'active',
            'entry_date': '2025-01-15',
            'legs': [
                {
                    'leg_id': 'leg1',
                    'asset_type': 'stock',
                    'action': 'BUY',
                    'symbol': '600519.SH',
                    'quantity': 100,
                    'entry_price': 1800,
                    'current_pnl': 2000
                },
                {
                    'leg_id': 'leg2',
                    'asset_type': 'call',
                    'action': 'SELL',
                    'symbol': '600519.SH',
                    'quantity': 1,
                    'entry_price': 50,
                    'strike_price': 1900,
                    'expiry_date': '2025-03-21',
                    'current_pnl': 3000
                }
            ],
            'total_pnl': 5000.0,
            'total_margin': 180000.0,
            'greeks': {
                'delta': 0.42,
                'gamma': 0.015,
                'theta': -0.05
            }
        },
        {
            'combination_id': 'combo_002',
            'strategy_name': '蝶式价差 - 50ETF',
            'strategy_type': 'butterfly_spread',
            'status': 'active',
            'entry_date': '2025-02-01',
            'legs': [
                {'leg_id': 'leg1', 'asset_type': 'call', 'action': 'BUY',
                 'symbol': '50ETF', 'quantity': 1, 'entry_price': 0.15,
                 'strike_price': 2.8, 'expiry_date': '2025-03-26', 'current_pnl': 500},
                {'leg_id': 'leg2', 'asset_type': 'call', 'action': 'SELL',
                 'symbol': '50ETF', 'quantity': 2, 'entry_price': 0.10,
                 'strike_price': 3.0, 'expiry_date': '2025-03-26', 'current_pnl': -200},
                {'leg_id': 'leg3', 'asset_type': 'call', 'action': 'BUY',
                 'symbol': '50ETF', 'quantity': 1, 'entry_price': 0.05,
                 'strike_price': 3.2, 'expiry_date': '2025-03-26', 'current_pnl': 100}
            ],
            'total_pnl': 400.0,
            'total_margin': 6000.0,
            'greeks': {
                'delta': 0.05,
                'gamma': 0.08,
                'theta': -0.03
            }
        }
    ]

    print("组合持仓视图组件测试")
    print("=" * 60)
    print(f"组合数量: {len(sample_combinations)}")
    for combo in sample_combinations:
        print(f"\n策略: {combo['strategy_name']}")
        print(f"  腿数: {len(combo['legs'])}")
        print(f"  总盈亏: ¥{combo['total_pnl']:,.0f}")
        print(f"  保证金: ¥{combo['total_margin']:,.0f}")

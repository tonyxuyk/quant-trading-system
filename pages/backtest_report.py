"""
回测报告页模块
显示详细的回测结果和分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show():
    """显示回测报告页面"""
    st.markdown("# 📊 回测报告分析")
    st.markdown("### 详细的回测结果与性能分析")
    
    # 检查前置条件
    if not st.session_state.get('backtest_completed', False):
        st.error("❌ 请先完成策略配置和回测！")
        return
    
    # 获取回测结果
    results = st.session_state.get('backtest_results', {})
    if not results:
        st.error("❌ 回测结果不存在！")
        return
    
    st.markdown("---")
    
    # 总体概览
    show_overview(results)
    
    st.markdown("---")
    
    # 详细结果分析
    show_detailed_analysis(results)
    
    st.markdown("---")
    
    # 股票对比分析
    show_stock_comparison(results)
    
    st.markdown("---")
    
    # 风险分析
    show_risk_analysis(results)
    
    st.markdown("---")
    
    # 交易记录
    show_trade_records(results)

def show_overview(results):
    """显示总体概览"""
    
    st.markdown("## 📈 总体概览")
    
    # 计算汇总指标
    total_stocks = len(results)
    total_return = np.mean([result['total_return'] for result in results.values()])
    avg_sharpe = np.mean([result['sharpe_ratio'] for result in results.values() if result['sharpe_ratio'] is not None])
    max_drawdown = max([result['max_drawdown'] for result in results.values()])
    avg_win_rate = np.mean([result['win_rate'] for result in results.values()])
    
    # 关键指标展示
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "股票数量",
            f"{total_stocks}",
            help="参与回测的股票总数"
        )
    
    with col2:
        st.metric(
            "平均收益率",
            f"{total_return:.2f}%",
            delta=f"{total_return:.2f}%",
            help="所有股票的平均收益率"
        )
    
    with col3:
        st.metric(
            "平均夏普比率",
            f"{avg_sharpe:.2f}",
            delta="higher is better",
            help="风险调整后收益指标"
        )
    
    with col4:
        st.metric(
            "最大回撤",
            f"{max_drawdown:.2f}%",
            delta=f"-{max_drawdown:.2f}%",
            help="所有股票中的最大回撤"
        )
    
    with col5:
        st.metric(
            "平均胜率",
            f"{avg_win_rate:.1f}%",
            delta=f"{avg_win_rate:.1f}%",
            help="平均交易胜率"
        )
    
    # 策略信息
    strategy_params = st.session_state.get('strategy_params', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 策略配置")
        st.info(f"""
        **策略名称:** {strategy_params.get('strategy_name', 'N/A')}
        
        **初始资金:** {strategy_params.get('initial_cash', 0):,} 元
        
        **仓位比例:** {strategy_params.get('position_size', 0)*100:.1f}%
        
        **最大回撤限制:** {strategy_params.get('max_drawdown', 0)*100:.1f}%
        """)
    
    with col2:
        st.markdown("### 💰 交易费用")
        trade_costs = strategy_params.get('trade_costs', {})
        st.info(f"""
        **佣金费率:** {trade_costs.get('commission', 0)*100:.3f}%
        
        **印花税:** {trade_costs.get('stamp_tax', 0)*100:.3f}%
        
        **过户费:** {trade_costs.get('transfer_fee', 0)*100:.4f}%
        
        **最低佣金:** {trade_costs.get('min_commission', 0):.1f} 元
        """)

def show_detailed_analysis(results):
    """显示详细分析"""
    
    st.markdown("## 📋 详细分析")
    
    # 收益率分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 收益率分布")
        returns = [result['total_return'] for result in results.values()]
        
        fig = px.histogram(
            x=returns,
            nbins=10,
            title="收益率分布直方图",
            labels={'x': '收益率 (%)', 'y': '频次'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 风险收益散点图")
        
        returns = [result['total_return'] for result in results.values()]
        sharpe_ratios = [result['sharpe_ratio'] if result['sharpe_ratio'] is not None else 0 for result in results.values()]
        stock_codes = list(results.keys())
        
        fig = px.scatter(
            x=returns,
            y=sharpe_ratios,
            text=stock_codes,
            title="风险收益关系",
            labels={'x': '收益率 (%)', 'y': '夏普比率'}
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # 表现汇总表
    st.markdown("### 📈 表现汇总表")
    
    summary_data = []
    for stock_code, result in results.items():
        summary_data.append({
            '股票代码': stock_code,
            '收益率 (%)': f"{result['total_return']:.2f}",
            '夏普比率': f"{result['sharpe_ratio']:.2f}" if result['sharpe_ratio'] is not None else "N/A",
            '最大回撤 (%)': f"{result['max_drawdown']:.2f}",
            '胜率 (%)': f"{result['win_rate']:.1f}",
            '交易次数': result['total_trades'],
            '盈亏比': f"{result['profit_loss_ratio']:.2f}" if result['profit_loss_ratio'] > 0 else "N/A"
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # 添加颜色标记
    def highlight_performance(val):
        if isinstance(val, str) and val.endswith('%'):
            try:
                num_val = float(val.replace('%', ''))
                if num_val > 0:
                    return 'background-color: lightgreen'
                elif num_val < 0:
                    return 'background-color: lightcoral'
            except:
                pass
        return ''
    
    st.dataframe(
        df_summary.style.applymap(highlight_performance, subset=['收益率 (%)']),
        use_container_width=True
    )

def show_stock_comparison(results):
    """显示股票对比分析"""
    
    st.markdown("## 🔍 股票对比分析")
    
    # 选择要对比的股票
    stock_codes = list(results.keys())
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_stocks = st.multiselect(
            "选择要对比的股票",
            options=stock_codes,
            default=stock_codes[:min(3, len(stock_codes))],
            help="最多选择5只股票进行对比"
        )
    
    if not selected_stocks:
        st.warning("请选择至少一只股票进行对比")
        return
    
    with col2:
        comparison_metric = st.selectbox(
            "选择对比指标",
            ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "total_trades"],
            format_func=lambda x: {
                "total_return": "收益率",
                "sharpe_ratio": "夏普比率", 
                "max_drawdown": "最大回撤",
                "win_rate": "胜率",
                "total_trades": "交易次数"
            }[x]
        )
    
    # 对比图表
    if len(selected_stocks) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # 柱状图对比
            values = [results[code][comparison_metric] for code in selected_stocks]
            
            fig = go.Figure(data=[
                go.Bar(x=selected_stocks, y=values, name=comparison_metric)
            ])
            
            metric_names = {
                "total_return": "收益率 (%)",
                "sharpe_ratio": "夏普比率",
                "max_drawdown": "最大回撤 (%)",
                "win_rate": "胜率 (%)",
                "total_trades": "交易次数"
            }
            
            fig.update_layout(
                title=f"{metric_names[comparison_metric]}对比",
                xaxis_title="股票代码",
                yaxis_title=metric_names[comparison_metric]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 雷达图
            metrics = ['total_return', 'sharpe_ratio', 'win_rate']
            metric_labels = ['收益率', '夏普比率', '胜率']
            
            fig = go.Figure()
            
            for stock in selected_stocks[:3]:  # 最多显示3只股票的雷达图
                values = []
                for metric in metrics:
                    val = results[stock][metric]
                    if val is None:
                        val = 0
                    values.append(val)
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metric_labels,
                    fill='toself',
                    name=stock
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max([max([results[s][m] if results[s][m] is not None else 0 for m in metrics]) for s in selected_stocks])]
                    )),
                title="多维度对比雷达图"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 详细对比表
    st.markdown("### 📊 详细对比表")
    
    comparison_data = {}
    for stock in selected_stocks:
        result = results[stock]
        comparison_data[stock] = {
            '收益率 (%)': f"{result['total_return']:.2f}",
            '夏普比率': f"{result['sharpe_ratio']:.2f}" if result['sharpe_ratio'] is not None else "N/A",
            '最大回撤 (%)': f"{result['max_drawdown']:.2f}",
            '胜率 (%)': f"{result['win_rate']:.1f}",
            '交易次数': result['total_trades'],
            '盈利交易': result['winning_trades'],
            '亏损交易': result['losing_trades'],
            '盈亏比': f"{result['profit_loss_ratio']:.2f}" if result['profit_loss_ratio'] > 0 else "N/A"
        }
    
    df_comparison = pd.DataFrame(comparison_data).T
    st.dataframe(df_comparison, use_container_width=True)

def show_risk_analysis(results):
    """显示风险分析"""
    
    st.markdown("## ⚠️ 风险分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📉 回撤分析")
        
        # 回撤分布
        drawdowns = [result['max_drawdown'] for result in results.values()]
        
        fig = px.box(
            y=drawdowns,
            title="最大回撤分布",
            labels={'y': '最大回撤 (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 回撤统计
        st.markdown("**回撤统计:**")
        st.write(f"- 平均回撤: {np.mean(drawdowns):.2f}%")
        st.write(f"- 最大回撤: {max(drawdowns):.2f}%")
        st.write(f"- 最小回撤: {min(drawdowns):.2f}%")
        st.write(f"- 回撤标准差: {np.std(drawdowns):.2f}%")
    
    with col2:
        st.markdown("### 📊 胜率分析")
        
        # 胜率分布
        win_rates = [result['win_rate'] for result in results.values()]
        
        fig = px.histogram(
            x=win_rates,
            nbins=8,
            title="胜率分布",
            labels={'x': '胜率 (%)', 'y': '频次'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 胜率统计
        st.markdown("**胜率统计:**")
        st.write(f"- 平均胜率: {np.mean(win_rates):.1f}%")
        st.write(f"- 最高胜率: {max(win_rates):.1f}%")
        st.write(f"- 最低胜率: {min(win_rates):.1f}%")
        st.write(f"- 胜率>50%的股票: {sum(1 for wr in win_rates if wr > 50)}/{len(win_rates)}")
    
    # 风险提示
    st.markdown("### ⚠️ 风险提示")
    
    high_risk_stocks = []
    for stock, result in results.items():
        if result['max_drawdown'] > 15 or result['win_rate'] < 40:
            high_risk_stocks.append(stock)
    
    if high_risk_stocks:
        st.warning(f"""
        **高风险股票提醒:**
        
        以下股票存在较高风险（最大回撤>15%或胜率<40%）:
        
        {', '.join(high_risk_stocks)}
        
        **建议:** 谨慎考虑这些股票的投资，或调整策略参数。
        """)
    else:
        st.success("✅ 所有股票的风险指标都在可接受范围内。")

def show_trade_records(results):
    """显示交易记录"""
    
    st.markdown("## 📝 交易记录")
    
    # 选择股票查看交易记录
    stock_codes = list(results.keys())
    selected_stock = st.selectbox(
        "选择股票查看详细交易记录",
        options=stock_codes,
        index=0
    )
    
    if selected_stock and selected_stock in results:
        result = results[selected_stock]
        trades_detail = result.get('trades_detail', [])
        
        if trades_detail:
            # 交易记录表格
            st.markdown(f"### 📊 {selected_stock} 交易记录")
            
            trade_data = []
            for i, trade in enumerate(trades_detail):
                trade_data.append({
                    '序号': i + 1,
                    '开仓日期': trade.get('entry_date', 'N/A'),
                    '平仓日期': trade.get('exit_date', 'N/A'),
                    '开仓价格': f"{trade.get('entry_price', 0):.2f}",
                    '平仓价格': f"{trade.get('exit_price', 0):.2f}",
                    '数量': trade.get('size', 0),
                    '盈亏': f"{trade.get('profit', 0):.2f}",
                    '手续费': f"{trade.get('commission', 0):.2f}",
                    '净盈亏': f"{trade.get('profit', 0) - trade.get('commission', 0):.2f}"
                })
            
            df_trades = pd.DataFrame(trade_data)
            
            # 添加颜色标记
            def highlight_profit(val):
                try:
                    if isinstance(val, str):
                        num_val = float(val)
                        if num_val > 0:
                            return 'background-color: lightgreen'
                        elif num_val < 0:
                            return 'background-color: lightcoral'
                except:
                    pass
                return ''
            
            st.dataframe(
                df_trades.style.applymap(highlight_profit, subset=['盈亏', '净盈亏']),
                use_container_width=True
            )
            
            # 交易统计
            col1, col2, col3 = st.columns(3)
            
            profits = [trade.get('profit', 0) for trade in trades_detail]
            profitable_trades = [p for p in profits if p > 0]
            losing_trades = [p for p in profits if p < 0]
            
            with col1:
                st.markdown("**盈利交易统计:**")
                if profitable_trades:
                    st.write(f"- 盈利次数: {len(profitable_trades)}")
                    st.write(f"- 平均盈利: {np.mean(profitable_trades):.2f}")
                    st.write(f"- 最大盈利: {max(profitable_trades):.2f}")
                else:
                    st.write("无盈利交易")
            
            with col2:
                st.markdown("**亏损交易统计:**")
                if losing_trades:
                    st.write(f"- 亏损次数: {len(losing_trades)}")
                    st.write(f"- 平均亏损: {np.mean(losing_trades):.2f}")
                    st.write(f"- 最大亏损: {min(losing_trades):.2f}")
                else:
                    st.write("无亏损交易")
            
            with col3:
                st.markdown("**总体统计:**")
                st.write(f"- 总交易次数: {len(trades_detail)}")
                st.write(f"- 总盈亏: {sum(profits):.2f}")
                st.write(f"- 胜率: {len(profitable_trades)/len(trades_detail)*100:.1f}%")
                if losing_trades and profitable_trades:
                    st.write(f"- 盈亏比: {abs(np.mean(profitable_trades)/np.mean(losing_trades)):.2f}")
        else:
            st.info("该股票暂无详细交易记录")
    
    # 导出功能
    st.markdown("---")
    st.markdown("### 📥 导出功能")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 导出汇总报告"):
            export_summary_report(results)
    
    with col2:
        if st.button("📝 导出交易记录"):
            export_trade_records(results)
    
    with col3:
        if st.button("📈 生成PDF报告"):
            st.info("PDF报告生成功能开发中...")

def export_summary_report(results):
    """导出汇总报告"""
    
    summary_data = []
    for stock_code, result in results.items():
        summary_data.append({
            '股票代码': stock_code,
            '收益率': result['total_return'],
            '夏普比率': result['sharpe_ratio'],
            '最大回撤': result['max_drawdown'],
            '胜率': result['win_rate'],
            '交易次数': result['total_trades'],
            '盈利交易': result['winning_trades'],
            '亏损交易': result['losing_trades'],
            '盈亏比': result['profit_loss_ratio']
        })
    
    df = pd.DataFrame(summary_data)
    
    # 转换为CSV
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📊 下载汇总报告CSV",
        data=csv,
        file_name=f"backtest_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.success("✅ 汇总报告已准备好下载！")

def export_trade_records(results):
    """导出交易记录"""
    
    all_trades = []
    for stock_code, result in results.items():
        trades_detail = result.get('trades_detail', [])
        for trade in trades_detail:
            trade_record = {
                '股票代码': stock_code,
                '开仓日期': trade.get('entry_date', 'N/A'),
                '平仓日期': trade.get('exit_date', 'N/A'),
                '开仓价格': trade.get('entry_price', 0),
                '平仓价格': trade.get('exit_price', 0),
                '数量': trade.get('size', 0),
                '盈亏': trade.get('profit', 0),
                '手续费': trade.get('commission', 0),
                '净盈亏': trade.get('profit', 0) - trade.get('commission', 0)
            }
            all_trades.append(trade_record)
    
    if all_trades:
        df = pd.DataFrame(all_trades)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📝 下载交易记录CSV",
            data=csv,
            file_name=f"trade_records_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.success("✅ 交易记录已准备好下载！")
    else:
        st.warning("⚠️ 没有可导出的交易记录")

if __name__ == "__main__":
    show() 
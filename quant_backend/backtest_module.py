#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易算法后台 - 回测库模块
功能：执行策略回测、生成回测结果、性能分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class BacktestEngine:
    """回测引擎 - 执行策略回测"""
    
    def __init__(self, initial_cash: float = 1000000):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
        """
        self.initial_cash = initial_cash
        self.reset_state()
        
        print("🧪 回测引擎初始化完成")
    
    def reset_state(self):
        """重置回测状态"""
        self.cash = self.initial_cash
        self.holdings = {}  # {股票代码: 持股数量}
        self.trades = []    # 交易记录
        self.portfolio_values = []  # 组合价值历史
        self.current_date = None
        self.max_portfolio_value = self.initial_cash
        self.max_drawdown = 0.0
    
    def run_backtest(self, signals_data: Dict[str, pd.DataFrame], 
                    position_manager, benchmark_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        运行回测
        
        Args:
            signals_data: 包含交易信号的数据
            position_manager: 仓位管理器
            benchmark_data: 基准数据
            
        Returns:
            回测结果字典
        """
        print("🚀 开始执行回测...")
        
        try:
            # 重置状态
            self.reset_state()
            
            # 获取所有交易日期
            all_dates = self._get_all_trading_dates(signals_data)
            
            if not all_dates:
                raise ValueError("没有找到有效的交易日期")
            
            print(f"📅 回测期间: {all_dates[0]} 至 {all_dates[-1]}")
            print(f"📊 交易日数: {len(all_dates)} 天")
            
            # 逐日回测
            for date in all_dates:
                self.current_date = date
                self._process_trading_day(date, signals_data, position_manager)
            
            # 生成回测报告
            results = self._generate_backtest_report(signals_data, benchmark_data)
            
            print("✅ 回测执行完成")
            return results
            
        except Exception as e:
            print(f"❌ 回测执行失败: {str(e)}")
            return self._generate_error_report(str(e))
    
    def _get_all_trading_dates(self, signals_data: Dict[str, pd.DataFrame]) -> List[pd.Timestamp]:
        """获取所有交易日期"""
        all_dates = set()
        
        for symbol, data in signals_data.items():
            if not data.empty:
                all_dates.update(data.index.tolist())
        
        return sorted(list(all_dates))
    
    def _process_trading_day(self, date: pd.Timestamp, signals_data: Dict[str, pd.DataFrame], 
                            position_manager):
        """处理单个交易日"""
        
        # 更新组合价值
        portfolio_value = self._calculate_portfolio_value(date, signals_data)
        self.portfolio_values.append({
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'holdings_value': portfolio_value - self.cash
        })
        
        # 更新最大回撤
        if portfolio_value > self.max_portfolio_value:
            self.max_portfolio_value = portfolio_value
        
        current_drawdown = (self.max_portfolio_value - portfolio_value) / self.max_portfolio_value
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # 风险控制检查
        if not position_manager.check_risk_control(portfolio_value):
            print(f"⚠️ {date.strftime('%Y-%m-%d')} 触发风险控制，停止交易")
            return
        
        # 处理交易信号
        self._process_trading_signals(date, signals_data, position_manager)
    
    def _calculate_portfolio_value(self, date: pd.Timestamp, 
                                  signals_data: Dict[str, pd.DataFrame]) -> float:
        """计算当前组合价值"""
        total_value = self.cash
        
        for symbol, shares in self.holdings.items():
            if shares > 0 and symbol in signals_data:
                data = signals_data[symbol]
                if date in data.index:
                    current_price = data.loc[date, 'close']
                    total_value += shares * current_price
        
        return total_value
    
    def _process_trading_signals(self, date: pd.Timestamp, signals_data: Dict[str, pd.DataFrame], 
                                position_manager):
        """处理交易信号"""
        
        for symbol, data in signals_data.items():
            if date not in data.index:
                continue
            
            signal = data.loc[date, 'signal']
            signal_strength = data.loc[date, 'signal_strength']
            current_price = data.loc[date, 'close']
            
            if signal == 0:
                continue
            
            try:
                if signal == 1:  # 买入信号
                    self._execute_buy_order(symbol, current_price, signal_strength, 
                                          position_manager, date)
                elif signal == -1:  # 卖出信号
                    self._execute_sell_order(symbol, current_price, signal_strength, 
                                           position_manager, date)
            except Exception as e:
                print(f"❌ {date.strftime('%Y-%m-%d')} {symbol} 交易执行失败: {e}")
                continue
    
    def _execute_buy_order(self, symbol: str, price: float, signal_strength: float, 
                          position_manager, date: pd.Timestamp):
        """执行买入订单"""
        
        # 如果已有持仓，跳过
        if symbol in self.holdings and self.holdings[symbol] > 0:
            return
        
        # 计算可买入股数
        current_value = self.cash
        shares = position_manager.calculate_position_size(current_value, price, signal_strength)
        
        if shares <= 0:
            return
        
        # 计算交易费用
        trade_cost = position_manager.calculate_trade_cost(shares, price, True)
        total_cost = shares * price + trade_cost
        
        # 检查资金是否充足
        if total_cost > self.cash:
            return
        
        # 执行买入
        self.cash -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + shares
        
        # 记录交易
        trade_record = {
            'date': date,
            'symbol': symbol,
            'action': 'BUY',
            'shares': shares,
            'price': price,
            'trade_value': shares * price,
            'trade_cost': trade_cost,
            'total_cost': total_cost,
            'signal_strength': signal_strength,
            'cash_after': self.cash
        }
        
        self.trades.append(trade_record)
        print(f"📈 {date.strftime('%Y-%m-%d')} 买入 {symbol}: {shares}股 @ {price:.2f}元")
    
    def _execute_sell_order(self, symbol: str, price: float, signal_strength: float, 
                           position_manager, date: pd.Timestamp):
        """执行卖出订单"""
        
        # 检查是否有持仓
        if symbol not in self.holdings or self.holdings[symbol] <= 0:
            return
        
        shares = self.holdings[symbol]
        
        # 计算交易费用
        trade_cost = position_manager.calculate_trade_cost(shares, price, False)
        trade_value = shares * price
        net_proceeds = trade_value - trade_cost
        
        # 执行卖出
        self.cash += net_proceeds
        self.holdings[symbol] = 0
        
        # 记录交易
        trade_record = {
            'date': date,
            'symbol': symbol,
            'action': 'SELL',
            'shares': shares,
            'price': price,
            'trade_value': trade_value,
            'trade_cost': trade_cost,
            'net_proceeds': net_proceeds,
            'signal_strength': signal_strength,
            'cash_after': self.cash
        }
        
        self.trades.append(trade_record)
        print(f"📉 {date.strftime('%Y-%m-%d')} 卖出 {symbol}: {shares}股 @ {price:.2f}元")
    
    def _generate_backtest_report(self, signals_data: Dict[str, pd.DataFrame], 
                                 benchmark_data: Optional[pd.DataFrame]) -> Dict:
        """生成回测报告"""
        
        if not self.portfolio_values:
            return self._generate_error_report("没有有效的组合价值数据")
        
        # 基本统计
        portfolio_df = pd.DataFrame(self.portfolio_values)
        portfolio_df.set_index('date', inplace=True)
        
        final_value = portfolio_df['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_cash) / self.initial_cash
        
        # 计算年化收益率
        days = len(portfolio_df)
        annual_return = (final_value / self.initial_cash) ** (252 / days) - 1
        
        # 计算夏普比率
        daily_returns = portfolio_df['portfolio_value'].pct_change().dropna()
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # 交易统计
        trade_stats = self._calculate_trade_statistics()
        
        # 基准对比
        benchmark_stats = self._calculate_benchmark_comparison(portfolio_df, benchmark_data)
        
        # 风险指标
        risk_metrics = self._calculate_risk_metrics(daily_returns)
        
        # 生成报告
        report = {
            'success': True,
            'summary': {
                'initial_cash': self.initial_cash,
                'final_value': final_value,
                'total_return': total_return * 100,
                'annual_return': annual_return * 100,
                'max_drawdown': self.max_drawdown * 100,
                'sharpe_ratio': sharpe_ratio,
                'trading_days': days
            },
            'trade_statistics': trade_stats,
            'risk_metrics': risk_metrics,
            'benchmark_comparison': benchmark_stats,
            'portfolio_history': portfolio_df.to_dict('records'),
            'trades': self.trades,
            'holdings': {k: v for k, v in self.holdings.items() if v > 0}
        }
        
        return report
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if returns.empty or returns.std() == 0:
            return 0.0
        
        excess_returns = returns.mean() - risk_free_rate / 252
        return (excess_returns / returns.std()) * np.sqrt(252)
    
    def _calculate_trade_statistics(self) -> Dict:
        """计算交易统计"""
        if not self.trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_costs': 0,
                'profitable_trades': 0,
                'win_rate': 0,
                'avg_profit_per_trade': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        buy_trades = trades_df[trades_df['action'] == 'BUY']
        sell_trades = trades_df[trades_df['action'] == 'SELL']
        
        total_costs = trades_df['trade_cost'].sum()
        
        # 计算盈利交易
        profitable_trades = 0
        total_profit = 0
        
        for symbol in set(trades_df['symbol']):
            symbol_trades = trades_df[trades_df['symbol'] == symbol].sort_values('date')
            buy_price = sell_price = 0
            
            for _, trade in symbol_trades.iterrows():
                if trade['action'] == 'BUY':
                    buy_price = trade['price']
                elif trade['action'] == 'SELL' and buy_price > 0:
                    profit = (trade['price'] - buy_price) * trade['shares'] - trade['trade_cost']
                    total_profit += profit
                    if profit > 0:
                        profitable_trades += 1
                    buy_price = 0
        
        completed_trades = len(sell_trades)
        win_rate = (profitable_trades / completed_trades * 100) if completed_trades > 0 else 0
        avg_profit = total_profit / completed_trades if completed_trades > 0 else 0
        
        return {
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'completed_trades': completed_trades,
            'total_costs': total_costs,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit,
            'total_profit': total_profit
        }
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict:
        """计算风险指标"""
        if returns.empty:
            return {}
        
        # VaR和CVaR
        var_95 = np.percentile(returns, 5) * 100
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
        
        # 波动率
        volatility = returns.std() * np.sqrt(252) * 100
        
        # 最大连续下跌天数
        negative_returns = returns < 0
        max_consecutive_losses = 0
        current_losses = 0
        
        for is_negative in negative_returns:
            if is_negative:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0
        
        return {
            'volatility': volatility,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_consecutive_losses': max_consecutive_losses,
            'positive_days': (returns > 0).sum(),
            'negative_days': (returns < 0).sum(),
            'flat_days': (returns == 0).sum()
        }
    
    def _calculate_benchmark_comparison(self, portfolio_df: pd.DataFrame, 
                                      benchmark_data: Optional[pd.DataFrame]) -> Dict:
        """计算基准对比"""
        if benchmark_data is None or benchmark_data.empty:
            return {'available': False, 'reason': '无基准数据'}
        
        try:
            # 对齐日期
            common_dates = portfolio_df.index.intersection(benchmark_data.index)
            if len(common_dates) == 0:
                return {'available': False, 'reason': '基准数据日期不匹配'}
            
            portfolio_aligned = portfolio_df.loc[common_dates, 'portfolio_value']
            benchmark_aligned = benchmark_data.loc[common_dates, 'close']
            
            # 计算基准收益率
            benchmark_initial = benchmark_aligned.iloc[0]
            benchmark_final = benchmark_aligned.iloc[-1]
            benchmark_return = (benchmark_final - benchmark_initial) / benchmark_initial * 100
            
            # 计算组合收益率（对齐期间）
            portfolio_initial = portfolio_aligned.iloc[0]
            portfolio_final = portfolio_aligned.iloc[-1]
            portfolio_return = (portfolio_final - portfolio_initial) / portfolio_initial * 100
            
            # 超额收益
            excess_return = portfolio_return - benchmark_return
            
            # Beta系数
            portfolio_returns = portfolio_aligned.pct_change().dropna()
            benchmark_returns = benchmark_aligned.pct_change().dropna()
            
            if len(portfolio_returns) > 1 and len(benchmark_returns) > 1:
                beta = np.cov(portfolio_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
            else:
                beta = 0
            
            return {
                'available': True,
                'benchmark_return': benchmark_return,
                'portfolio_return': portfolio_return,
                'excess_return': excess_return,
                'beta': beta,
                'tracking_days': len(common_dates)
            }
            
        except Exception as e:
            return {'available': False, 'reason': f'基准对比计算失败: {str(e)}'}
    
    def _generate_error_report(self, error_message: str) -> Dict:
        """生成错误报告"""
        return {
            'success': False,
            'error': error_message,
            'summary': {
                'initial_cash': self.initial_cash,
                'final_value': self.initial_cash,
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'trading_days': 0
            },
            'trade_statistics': {
                'total_trades': 0,
                'completed_trades': 0,
                'win_rate': 0
            }
        }

class BacktestModule:
    """回测库模块 - 统一管理回测流程"""
    
    def __init__(self):
        """初始化回测模块"""
        self.backtest_engine = None
        print("🔬 回测库模块初始化完成")
    
    def execute_backtest(self, stock_data: Dict[str, pd.DataFrame], 
                        signals_data: Dict[str, pd.DataFrame],
                        strategy_config: Dict,
                        position_manager,
                        benchmark_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        执行完整回测流程
        
        Args:
            stock_data: 原始股票数据
            signals_data: 包含信号的数据
            strategy_config: 策略配置
            position_manager: 仓位管理器
            benchmark_data: 基准数据
            
        Returns:
            回测结果
        """
        
        print("🎯 开始执行完整回测流程...")
        
        try:
            # 验证输入数据
            validation_result = self._validate_inputs(stock_data, signals_data, strategy_config)
            if not validation_result['valid']:
                return self._create_error_result(validation_result['error'])
            
            # 初始化回测引擎
            initial_cash = strategy_config.get('initial_cash', 1000000)
            self.backtest_engine = BacktestEngine(initial_cash)
            
            # 执行回测
            backtest_results = self.backtest_engine.run_backtest(
                signals_data, position_manager, benchmark_data
            )
            
            if not backtest_results.get('success', False):
                return backtest_results
            
            # 增强结果报告
            enhanced_results = self._enhance_results(backtest_results, strategy_config)
            
            # 生成用户友好的摘要
            user_summary = self._generate_user_summary(enhanced_results)
            
            enhanced_results['user_summary'] = user_summary
            
            print("🎉 回测流程执行完成")
            return enhanced_results
            
        except Exception as e:
            error_msg = f"回测执行过程中发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_error_result(error_msg)
    
    def _validate_inputs(self, stock_data: Dict, signals_data: Dict, 
                        strategy_config: Dict) -> Dict:
        """验证输入数据"""
        
        if not stock_data:
            return {'valid': False, 'error': '股票数据为空'}
        
        if not signals_data:
            return {'valid': False, 'error': '信号数据为空'}
        
        if not strategy_config:
            return {'valid': False, 'error': '策略配置为空'}
        
        # 检查数据一致性
        for symbol in signals_data.keys():
            if symbol not in stock_data:
                return {'valid': False, 'error': f'股票 {symbol} 缺少原始数据'}
            
            if signals_data[symbol].empty:
                return {'valid': False, 'error': f'股票 {symbol} 信号数据为空'}
        
        return {'valid': True}
    
    def _enhance_results(self, results: Dict, strategy_config: Dict) -> Dict:
        """增强结果报告"""
        
        # 添加策略信息
        results['strategy_info'] = {
            'name': strategy_config.get('strategy_name', '未知策略'),
            'parameters': {k: v for k, v in strategy_config.items() 
                          if k not in ['initial_cash', 'max_drawdown', 'position_size']}
        }
        
        # 添加详细的费用分析
        if 'trade_statistics' in results:
            results['cost_analysis'] = self._analyze_costs(results['trades'])
        
        # 添加月度/年度分析
        if 'portfolio_history' in results:
            results['period_analysis'] = self._analyze_by_periods(results['portfolio_history'])
        
        return results
    
    def _analyze_costs(self, trades: List[Dict]) -> Dict:
        """分析交易费用"""
        if not trades:
            return {}
        
        trades_df = pd.DataFrame(trades)
        
        total_trade_value = trades_df['trade_value'].sum()
        total_costs = trades_df['trade_cost'].sum()
        cost_ratio = total_costs / total_trade_value if total_trade_value > 0 else 0
        
        return {
            'total_trade_value': total_trade_value,
            'total_costs': total_costs,
            'cost_ratio': cost_ratio * 100,
            'avg_cost_per_trade': trades_df['trade_cost'].mean(),
            'max_single_cost': trades_df['trade_cost'].max(),
            'min_single_cost': trades_df['trade_cost'].min()
        }
    
    def _analyze_by_periods(self, portfolio_history: List[Dict]) -> Dict:
        """按期间分析"""
        if not portfolio_history:
            return {}
        
        df = pd.DataFrame(portfolio_history)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 月度分析
        monthly_returns = df['portfolio_value'].resample('M').last().pct_change().dropna()
        
        # 季度分析
        quarterly_returns = df['portfolio_value'].resample('Q').last().pct_change().dropna()
        
        return {
            'monthly_analysis': {
                'best_month': monthly_returns.max() * 100,
                'worst_month': monthly_returns.min() * 100,
                'avg_monthly_return': monthly_returns.mean() * 100,
                'positive_months': (monthly_returns > 0).sum(),
                'negative_months': (monthly_returns < 0).sum()
            },
            'quarterly_analysis': {
                'best_quarter': quarterly_returns.max() * 100,
                'worst_quarter': quarterly_returns.min() * 100,
                'positive_quarters': (quarterly_returns > 0).sum(),
                'negative_quarters': (quarterly_returns < 0).sum()
            }
        }
    
    def _generate_user_summary(self, results: Dict) -> str:
        """生成用户友好的摘要"""
        
        if not results.get('success', False):
            return f"❌ 回测失败: {results.get('error', '未知错误')}"
        
        summary = results.get('summary', {})
        trade_stats = results.get('trade_statistics', {})
        
        # 基本信息
        initial_cash = summary.get('initial_cash', 0)
        final_value = summary.get('final_value', 0)
        total_return = summary.get('total_return', 0)
        max_drawdown = summary.get('max_drawdown', 0)
        sharpe_ratio = summary.get('sharpe_ratio', 0)
        
        # 交易信息
        total_trades = trade_stats.get('total_trades', 0)
        win_rate = trade_stats.get('win_rate', 0)
        total_costs = trade_stats.get('total_costs', 0)
        
        # 生成摘要文本
        summary_text = f"""
📊 回测摘要报告

💰 资金情况:
   • 初始资金: {initial_cash:,.0f} 元
   • 最终价值: {final_value:,.0f} 元
   • 总收益率: {total_return:+.2f}%
   • 最大回撤: {max_drawdown:.2f}%

📈 风险收益:
   • 夏普比率: {sharpe_ratio:.2f}
   • 风险评级: {'优秀' if sharpe_ratio > 1.5 else '良好' if sharpe_ratio > 1.0 else '一般' if sharpe_ratio > 0.5 else '较差'}

🔄 交易统计:
   • 总交易次数: {total_trades} 笔
   • 交易胜率: {win_rate:.1f}%
   • 交易费用: {total_costs:,.2f} 元

📋 总体评价: {'策略表现优秀' if total_return > 10 and max_drawdown < 15 else '策略表现良好' if total_return > 5 else '策略需要优化'}
        """
        
        return summary_text.strip()
    
    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            'success': False,
            'error': error_message,
            'summary': {},
            'user_summary': f"❌ 回测失败: {error_message}"
        }

if __name__ == "__main__":
    # 测试代码
    backtest_module = BacktestModule()
    print("✅ 回测库模块测试完成") 
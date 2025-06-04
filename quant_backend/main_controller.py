#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易算法后台 - 主控制器
整合数据库、策略库、回测库的完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_module import DatabaseModule
from strategy_module import StrategyModule
from backtest_module import BacktestModule
from typing import Dict, List, Optional
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class QuantTradingBackend:
    """量化交易算法后台主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        print("🎯 初始化量化交易算法后台...")
        
        # 初始化三大模块
        self.database_module = None
        self.strategy_module = None  
        self.backtest_module = None
        
        print("✅ 主控制器初始化完成")
    
    def run_complete_backtest(self, request_params: Dict) -> Dict:
        """
        运行完整的量化交易回测流程
        
        Args:
            request_params: 来自Streamlit界面的请求参数
            包含：
            - stock_codes: 股票代码列表
            - start_date: 开始日期
            - end_date: 结束日期  
            - timeframe: 时间级别
            - strategy_config: 策略配置
            
        Returns:
            完整的回测结果
        """
        
        print("🚀 开始完整量化交易回测流程...")
        
        try:
            # 1. 数据获取阶段
            print("\n📊 阶段1: 数据获取与处理")
            data_result = self._execute_data_phase(request_params)
            
            if not data_result['success']:
                return self._create_error_response("数据获取失败", data_result['error'])
            
            # 2. 策略信号生成阶段
            print("\n⚙️ 阶段2: 策略信号生成")
            strategy_result = self._execute_strategy_phase(
                data_result['stock_data'], 
                request_params.get('strategy_config', {})
            )
            
            if not strategy_result['success']:
                return self._create_error_response("策略信号生成失败", strategy_result['error'])
            
            # 3. 回测执行阶段
            print("\n🧪 阶段3: 回测执行与分析")
            backtest_result = self._execute_backtest_phase(
                data_result['stock_data'],
                strategy_result['signals_data'],
                request_params.get('strategy_config', {}),
                strategy_result['position_manager'],
                data_result.get('benchmark_data')
            )
            
            if not backtest_result['success']:
                return self._create_error_response("回测执行失败", backtest_result['error'])
            
            # 4. 结果整合
            print("\n📋 阶段4: 结果整合与输出")
            final_result = self._integrate_results(
                data_result, strategy_result, backtest_result, request_params
            )
            
            print("🎉 完整回测流程执行成功！")
            return final_result
            
        except Exception as e:
            error_msg = f"回测流程执行出错: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_error_response("系统错误", error_msg)
    
    def _execute_data_phase(self, params: Dict) -> Dict:
        """执行数据获取阶段"""
        
        try:
            # 初始化数据库模块
            self.database_module = DatabaseModule()
            
            # 获取参数
            stock_codes = params.get('stock_codes', [])
            start_date = params.get('start_date', '2024-01-01')
            end_date = params.get('end_date', '2024-06-01')
            timeframe = params.get('timeframe', '1d')
            
            if not stock_codes:
                return {'success': False, 'error': '未指定股票代码'}
            
            print(f"📈 获取股票数据: {stock_codes}")
            print(f"📅 时间范围: {start_date} 至 {end_date}")
            print(f"⏰ 时间级别: {timeframe}")
            
            # 获取股票数据
            stock_data = self.database_module.get_stock_data(
                stock_codes, start_date, end_date, timeframe
            )
            
            if not stock_data:
                return {'success': False, 'error': '未能获取到任何股票数据'}
            
            # 获取基准数据
            print("📊 获取基准数据...")
            benchmark_data = self.database_module.get_benchmark_data(
                start_date, end_date, timeframe
            )
            
            print(f"✅ 数据获取完成，共获取 {len(stock_data)} 只股票数据")
            
            return {
                'success': True,
                'stock_data': stock_data,
                'benchmark_data': benchmark_data,
                'data_summary': {
                    'stock_count': len(stock_data),
                    'has_benchmark': benchmark_data is not None,
                    'date_range': f"{start_date} 至 {end_date}",
                    'timeframe': timeframe
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_strategy_phase(self, stock_data: Dict, strategy_config: Dict) -> Dict:
        """执行策略信号生成阶段"""
        
        try:
            # 初始化策略模块
            self.strategy_module = StrategyModule(strategy_config)
            
            print(f"📈 使用策略: {strategy_config.get('strategy_name', '未知')}")
            
            # 生成交易信号
            signals_data = self.strategy_module.generate_trading_signals(stock_data)
            
            if not signals_data:
                return {'success': False, 'error': '未能生成任何交易信号'}
            
            # 获取策略摘要
            strategy_summary = self.strategy_module.get_strategy_summary()
            
            print(f"✅ 策略信号生成完成，涵盖 {len(signals_data)} 只股票")
            
            return {
                'success': True,
                'signals_data': signals_data,
                'position_manager': self.strategy_module.position_manager,
                'strategy_summary': strategy_summary
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_backtest_phase(self, stock_data: Dict, signals_data: Dict, 
                               strategy_config: Dict, position_manager, 
                               benchmark_data: Optional[pd.DataFrame]) -> Dict:
        """执行回测阶段"""
        
        try:
            # 初始化回测模块
            self.backtest_module = BacktestModule()
            
            # 执行回测
            backtest_results = self.backtest_module.execute_backtest(
                stock_data=stock_data,
                signals_data=signals_data,
                strategy_config=strategy_config,
                position_manager=position_manager,
                benchmark_data=benchmark_data
            )
            
            print("✅ 回测执行完成")
            
            return backtest_results
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _integrate_results(self, data_result: Dict, strategy_result: Dict, 
                          backtest_result: Dict, original_params: Dict) -> Dict:
        """整合所有结果"""
        
        # 构建最终结果
        integrated_result = {
            'success': True,
            'timestamp': pd.Timestamp.now(),
            'request_params': original_params,
            
            # 数据阶段结果
            'data_phase': {
                'success': data_result['success'],
                'summary': data_result.get('data_summary', {}),
                'stock_count': len(data_result.get('stock_data', {})),
                'has_benchmark': data_result.get('benchmark_data') is not None
            },
            
            # 策略阶段结果  
            'strategy_phase': {
                'success': strategy_result['success'],
                'summary': strategy_result.get('strategy_summary', {}),
                'signals_count': len(strategy_result.get('signals_data', {}))
            },
            
            # 回测结果（完整）
            'backtest_results': backtest_result,
            
            # 用户界面显示用的简化摘要
            'display_summary': self._create_display_summary(backtest_result),
            
            # 与Streamlit界面的兼容性数据
            'streamlit_data': self._prepare_streamlit_data(backtest_result)
        }
        
        return integrated_result
    
    def _create_display_summary(self, backtest_result: Dict) -> Dict:
        """创建用于界面显示的摘要"""
        
        if not backtest_result.get('success', False):
            return {
                'status': 'failed',
                'message': backtest_result.get('error', '回测失败'),
                'summary_text': backtest_result.get('user_summary', '回测执行失败')
            }
        
        summary = backtest_result.get('summary', {})
        trade_stats = backtest_result.get('trade_statistics', {})
        
        return {
            'status': 'success',
            'summary_text': backtest_result.get('user_summary', ''),
            'key_metrics': {
                'total_return': f"{summary.get('total_return', 0):.2f}%",
                'annual_return': f"{summary.get('annual_return', 0):.2f}%", 
                'max_drawdown': f"{summary.get('max_drawdown', 0):.2f}%",
                'sharpe_ratio': f"{summary.get('sharpe_ratio', 0):.2f}",
                'win_rate': f"{trade_stats.get('win_rate', 0):.1f}%",
                'total_trades': trade_stats.get('total_trades', 0)
            },
            'final_value': summary.get('final_value', 0),
            'initial_cash': summary.get('initial_cash', 0)
        }
    
    def _prepare_streamlit_data(self, backtest_result: Dict) -> Dict:
        """准备传输给Streamlit的数据"""
        
        if not backtest_result.get('success', False):
            return {'available': False, 'error': backtest_result.get('error', '数据不可用')}
        
        # 提取关键数据用于图表和表格显示
        return {
            'available': True,
            'portfolio_history': backtest_result.get('portfolio_history', []),
            'trades': backtest_result.get('trades', []),
            'summary': backtest_result.get('summary', {}),
            'trade_statistics': backtest_result.get('trade_statistics', {}),
            'risk_metrics': backtest_result.get('risk_metrics', {}),
            'benchmark_comparison': backtest_result.get('benchmark_comparison', {})
        }
    
    def _create_error_response(self, phase: str, error_msg: str) -> Dict:
        """创建错误响应"""
        
        return {
            'success': False,
            'error_phase': phase,
            'error_message': error_msg,
            'display_summary': {
                'status': 'failed',
                'message': f"{phase}: {error_msg}",
                'summary_text': f"❌ {phase}: {error_msg}"
            },
            'streamlit_data': {'available': False, 'error': error_msg}
        }
    
    def get_module_status(self) -> Dict:
        """获取各模块状态"""
        
        return {
            'database_module': self.database_module is not None,
            'strategy_module': self.strategy_module is not None,
            'backtest_module': self.backtest_module is not None,
            'backend_version': '1.0.0',
            'modules_loaded': all([
                self.database_module is not None,
                self.strategy_module is not None, 
                self.backtest_module is not None
            ])
        }

# 为了保持与现有Streamlit系统的兼容性，提供简化的接口函数
def run_quantitative_backtest(stock_codes: List[str], start_date: str, end_date: str,
                             strategy_config: Dict, timeframe: str = '1d') -> Dict:
    """
    运行量化回测的简化接口函数
    与Streamlit界面保持兼容
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        strategy_config: 策略配置
        timeframe: 时间级别
        
    Returns:
        回测结果
    """
    
    # 构建请求参数
    request_params = {
        'stock_codes': stock_codes,
        'start_date': start_date,
        'end_date': end_date,
        'timeframe': timeframe,
        'strategy_config': strategy_config
    }
    
    # 创建主控制器并执行
    backend = QuantTradingBackend()
    result = backend.run_complete_backtest(request_params)
    
    # 返回Streamlit需要的格式
    if result['success']:
        return result['streamlit_data']
    else:
        return {
            'available': False,
            'error': result['error_message'],
            'summary_text': result['display_summary']['summary_text']
        }

if __name__ == "__main__":
    # 测试代码
    print("🧪 测试量化交易算法后台...")
    
    # 测试参数
    test_params = {
        'stock_codes': ['000001', '000002'],
        'start_date': '2024-01-01',
        'end_date': '2024-03-01',
        'timeframe': '1d',
        'strategy_config': {
            'strategy_name': '双均线策略',
            'fast_period': 5,
            'slow_period': 20,
            'initial_cash': 1000000,
            'max_drawdown': 0.1,
            'position_size': 0.8
        }
    }
    
    # 执行测试
    backend = QuantTradingBackend()
    result = backend.run_complete_backtest(test_params)
    
    print("\n📊 测试结果:")
    print(f"执行状态: {'成功' if result['success'] else '失败'}")
    if result['success']:
        print(result['display_summary']['summary_text'])
    else:
        print(f"错误: {result['error_message']}")
    
    print("\n✅ 后台测试完成") 
"""
策略选择页模块
交易策略配置和参数设置
"""

import streamlit as st
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_backend.strategy_module import StrategyModule
from quant_backend.backtest_module import BacktestModule

def show():
    """显示策略选择页面"""
    st.markdown("# ⚙️ 策略选择与配置")
    st.markdown("### 选择交易策略和设置参数")
    
    # 检查前置条件
    if not st.session_state.get('data_loaded', False):
        st.error("❌ 请先在选股页完成数据获取！")
        return
    
    st.markdown("---")
    
    # 显示已选股票信息
    st.markdown("## 📊 已选股票信息")
    
    selected_stocks = st.session_state.get('selected_stocks', [])
    if selected_stocks:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("已选股票数量", len(selected_stocks))
        
        with col2:
            start_date, end_date = st.session_state.get('selected_period', (None, None))
            if start_date and end_date:
                period_days = (end_date - start_date).days
                st.metric("回测天数", f"{period_days} 天")
        
        with col3:
            timeframe = st.session_state.get('selected_timeframe', '1d')
            st.metric("K线级别", timeframe)
        
        # 显示股票列表
        with st.expander("📋 查看选中的股票", expanded=False):
            for stock in selected_stocks:
                st.write(f"📈 {stock}")
    
    st.markdown("---")
    
    # 策略选择区域
    st.markdown("## 1️⃣ 策略类型选择")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 策略选择
        strategy_options = {
            "双均线策略": {
                "description": "基于快慢均线交叉的趋势跟踪策略",
                "适用": "趋势明显的市场",
                "参数": ["快线周期", "慢线周期"]
            },
            "RSI策略": {
                "description": "基于相对强弱指标的反转策略",
                "适用": "震荡市场",
                "参数": ["RSI周期", "超买阈值", "超卖阈值"]
            },
            "价格行为策略": {
                "description": "基于K线形态和价格行为的策略",
                "适用": "各种市场条件",
                "参数": ["观察周期", "突破阈值", "回撤阈值"]
            }
        }
        
        selected_strategy = st.selectbox(
            "选择交易策略",
            list(strategy_options.keys()),
            index=0,
            help="选择适合当前市场环境的交易策略"
        )
        
        # 显示策略详情
        strategy_info = strategy_options[selected_strategy]
        
        st.markdown(f"""
        **策略说明:** {strategy_info['description']}
        
        **适用环境:** {strategy_info['适用']}
        
        **主要参数:** {', '.join(strategy_info['参数'])}
        """)
    
    with col2:
        st.markdown("### 💡 策略选择建议")
        
        if selected_strategy == "双均线策略":
            st.info("""
            **适合场景:**
            - 明确的上升或下降趋势
            - 较长的回测周期
            - 波动相对较小的股票
            
            **注意事项:**
            - 在震荡市可能产生假信号
            - 需要合理设置均线周期
            """)
        elif selected_strategy == "RSI策略":
            st.info("""
            **适合场景:**
            - 震荡市场环境
            - 有明显超买超卖特征
            - 短期交易
            
            **注意事项:**
            - 强趋势中可能过早退出
            - 需要结合其他指标确认
            """)
        else:  # 价格行为策略
            st.info("""
            **适合场景:**
            - 各种市场环境
            - 关注关键支撑阻力位
            - 形态突破交易
            
            **注意事项:**
            - 需要较好的风险控制
            - 主观判断成分较高
            """)
    
    st.markdown("---")
    
    # 策略参数配置
    st.markdown("## 2️⃣ 策略参数配置")
    
    strategy_params = configure_strategy_parameters(selected_strategy)
    
    st.markdown("---")
    
    # 基准指数选择
    selected_benchmarks = configure_benchmark_selection()
    
    # 保存基准选择到session state
    if selected_benchmarks:
        st.session_state.selected_benchmarks = selected_benchmarks
    
    st.markdown("---")
    
    # 资金和风险管理
    st.markdown("## 3️⃣ 资金与风险管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_cash = st.number_input(
            "初始资金 (元)",
            min_value=10000,
            max_value=100000000,
            value=1000000,
            step=10000,
            help="回测使用的初始资金"
        )
    
    with col2:
        max_drawdown = st.slider(
            "最大回撤限制 (%)",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            help="当回撤超过此值时停止交易"
        )
    
    with col3:
        position_size = st.slider(
            "单次建仓比例 (%)",
            min_value=10,
            max_value=100,
            value=95,
            step=5,
            help="每次交易使用的资金比例"
        )
    
    # 交易费用设置
    st.markdown("### 💰 A股交易费用")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        commission_rate = st.number_input(
            "佣金费率 (%)",
            min_value=0.01,
            max_value=0.3,
            value=0.025,
            step=0.005,
            format="%.3f",
            help="券商佣金费率"
        )
    
    with col2:
        stamp_tax = st.number_input(
            "印花税 (%)",
            min_value=0.0,
            max_value=0.2,
            value=0.05,
            step=0.01,
            format="%.3f",
            help="卖出时收取的印花税"
        )
    
    with col3:
        transfer_fee = st.number_input(
            "过户费 (%)",
            min_value=0.0,
            max_value=0.01,
            value=0.001,
            step=0.0001,
            format="%.4f",
            help="上海股票过户费"
        )
    
    with col4:
        min_commission = st.number_input(
            "最低佣金 (元)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.1,
            help="最低佣金标准"
        )
    
    st.markdown("---")
    
    # 配置预览
    st.markdown("## 4️⃣ 配置预览")
    
    with st.expander("📋 查看完整配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **策略配置:**
            - 选择策略: {selected_strategy}
            - 策略参数: {strategy_params}
            - 回测股票: {len(selected_stocks)} 只
            """)
        
        with col2:
            st.markdown(f"""
            **资金配置:**
            - 初始资金: {initial_cash:,} 元
            - 最大回撤: {max_drawdown}%
            - 建仓比例: {position_size}%
            - 佣金费率: {commission_rate}%
            """)
    
    # 策略配置和启动回测
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 配置策略并开始回测", type="primary", use_container_width=True):
            configure_and_run_backtest(
                strategy_name=selected_strategy,
                strategy_params=strategy_params,
                initial_cash=initial_cash,
                max_drawdown=max_drawdown,
                position_size=position_size,
                commission_rate=commission_rate / 100,
                stamp_tax=stamp_tax / 100,
                transfer_fee=transfer_fee / 100,
                min_commission=min_commission
            )

def configure_strategy_parameters(strategy_name):
    """配置策略参数 (增强版 - 防止bool对象错误)"""
    
    try:
        # 调试信息
        print(f"🔧 配置策略参数: {strategy_name}")
        
        if strategy_name == "双均线策略":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fast_period = st.number_input(
                    "快线周期",
                    min_value=1,
                    max_value=50,
                    value=10,
                    step=1,
                    help="快速移动平均线的计算周期"
                )
            
            with col2:
                slow_period = st.number_input(
                    "慢线周期",
                    min_value=fast_period + 1,
                    max_value=200,
                    value=30,
                    step=1,
                    help="慢速移动平均线的计算周期"
                )
            
            with col3:
                ma_type = st.selectbox(
                    "均线类型",
                    ["SMA", "EMA", "WMA"],
                    index=0,
                    help="移动平均线的计算方法"
                )
            
            params = {
                "fast_period": fast_period,
                "slow_period": slow_period,
                "ma_type": ma_type
            }
            print(f"✅ 双均线策略参数: {params}")
            return params
        
        elif strategy_name == "RSI策略":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                rsi_period = st.number_input(
                    "RSI周期",
                    min_value=5,
                    max_value=50,
                    value=14,
                    step=1,
                    help="RSI指标的计算周期"
                )
            
            with col2:
                rsi_oversold = st.number_input(
                    "超卖阈值",
                    min_value=10,
                    max_value=40,
                    value=30,
                    step=1,
                    help="RSI超卖信号阈值"
                )
            
            with col3:
                rsi_overbought = st.number_input(
                    "超买阈值",
                    min_value=60,
                    max_value=90,
                    value=70,
                    step=1,
                    help="RSI超买信号阈值"
                )
            
            params = {
                "rsi_period": rsi_period,
                "rsi_oversold": rsi_oversold,
                "rsi_overbought": rsi_overbought
            }
            print(f"✅ RSI策略参数: {params}")
            return params
        
        elif strategy_name == "价格行为策略":
            col1, col2, col3 = st.columns(3)
            
            with col1:
                lookback_period = st.number_input(
                    "观察周期",
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=1,
                    help="价格行为分析的回望周期"
                )
            
            with col2:
                breakout_threshold = st.number_input(
                    "突破阈值 (%)",
                    min_value=0.5,
                    max_value=10.0,
                    value=2.0,
                    step=0.1,
                    help="价格突破的最小涨幅"
                )
            
            with col3:
                pullback_threshold = st.number_input(
                    "回撤阈值 (%)",
                    min_value=1.0,
                    max_value=20.0,
                    value=5.0,
                    step=0.5,
                    help="止损的回撤阈值"
                )
            
            params = {
                "lookback_period": lookback_period,
                "breakout_threshold": breakout_threshold / 100,
                "pullback_threshold": pullback_threshold / 100
            }
            print(f"✅ 价格行为策略参数: {params}")
            return params
        
        else:
            # 未知策略，返回默认参数
            st.warning(f"⚠️ 未知策略类型: {strategy_name}，使用默认参数")
            default_params = {
                "strategy_type": "unknown",
                "default": True
            }
            print(f"⚠️ 默认策略参数: {default_params}")
            return default_params
    
    except Exception as e:
        # 异常处理，确保始终返回字典
        error_msg = str(e)
        st.error(f"❌ 策略参数配置失败: {error_msg}")
        print(f"❌ 策略参数配置异常: {error_msg}")
        
        # 返回安全的默认参数
        safe_params = {
            "error": True,
            "error_message": error_msg,
            "strategy_name": strategy_name
        }
        print(f"🛡️ 安全参数: {safe_params}")
        return safe_params

def configure_benchmark_selection():
    """配置基准指数选择"""
    st.markdown("### 📊 基准指数选择")
    
    # 获取用户选择的股票市场信息 - 优先使用保存的市场信息
    selected_market = st.session_state.get('selected_market', None)
    selected_stocks = st.session_state.get('selected_stocks', [])
    
    # 检测股票市场类型
    markets_detected = set()
    
    # 如果有明确的市场选择，直接使用
    if selected_market:
        markets_detected.add(selected_market)
    
    # 否则通过股票代码检测
    elif selected_stocks:
        for stock in selected_stocks:
            stock = str(stock).strip()
            # A股检测：6位数字
            if stock.isdigit() and len(stock) == 6:
                markets_detected.add('A_STOCK')
            # 港股检测：数字代码或带.HK后缀，且不是6位
            elif (stock.isdigit() and len(stock) <= 5) or stock.upper().endswith('.HK'):
                markets_detected.add('HK_STOCK')
            # 美股检测：字母组合
            elif stock.isalpha() and len(stock) <= 5:
                markets_detected.add('US_STOCK')
            # 特殊美股代码（带^符号的指数）
            elif stock.startswith('^'):
                markets_detected.add('US_STOCK')
    
    # 基准指数配置 - 增加更多选项
    benchmark_options = {
        'A_STOCK': {
            '沪深300': '000300.SH',
            '上证指数': '000001.SH', 
            '中证500': '000905.SH',
            '创业板指': '399006.SZ'
        },
        'HK_STOCK': {
            '恒生指数': 'HSI',
            '恒生科技指数': 'HSTECH',
            '恒生中国企业指数': 'HSCEI',
            '恒生综合指数': 'HSCI'
        },
        'US_STOCK': {
            '标准普尔500': '^GSPC',
            '纳斯达克100': '^NDX',
            '道琼斯指数': '^DJI',
            '纳斯达克综合指数': '^IXIC'
        }
    }
    
    market_names = {
        'A_STOCK': '🇨🇳 A股市场',
        'HK_STOCK': '🇭🇰 港股市场', 
        'US_STOCK': '🇺🇸 美股市场'
    }
    
    selected_benchmarks = {}
    
    if not markets_detected:
        # 显示调试信息
        st.warning("⚠️ 未检测到有效股票市场，请先在选股页面选择股票")
        with st.expander("🔍 调试信息", expanded=False):
            st.write(f"保存的市场: {selected_market}")
            st.write(f"选择的股票: {selected_stocks}")
        return {}
    
    # 显示检测到的市场
    st.info(f"📊 检测到的市场: {', '.join([market_names.get(m, m) for m in markets_detected])}")
    
    # 为每个检测到的市场显示基准选择
    for market in markets_detected:
        if market in benchmark_options:
            st.markdown(f"#### {market_names[market]}")
            
            options = benchmark_options[market]
            selected_benchmark = st.selectbox(
                f"选择{market_names[market]}基准指数",
                list(options.keys()),
                key=f"benchmark_{market}",
                help=f"选择用于{market_names[market]}比较的基准指数"
            )
            
            if selected_benchmark:
                selected_benchmarks[market] = {
                    'name': selected_benchmark,
                    'symbol': options[selected_benchmark]
                }
                
                # 显示选择的基准
                st.success(f"✅ {market_names[market]}: {selected_benchmark} ({options[selected_benchmark]})")
    
    return selected_benchmarks

def configure_and_run_backtest(strategy_name, strategy_params, initial_cash, 
                              max_drawdown, position_size, commission_rate,
                              stamp_tax, transfer_fee, min_commission):
    """配置策略并运行回测 (增强版 - 全面错误处理)"""
    
    # 详细的参数验证和调试
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 验证输入参数...")
        progress_bar.progress(5)
        
        # 详细调试信息
        print(f"🔧 开始回测配置")
        print(f"策略名称: {strategy_name}")
        print(f"策略参数类型: {type(strategy_params)}")
        print(f"策略参数内容: {strategy_params}")
        
        # 1. 基础参数验证
        if strategy_name is None or strategy_name == "":
            st.error("❌ 策略名称为空")
            return
        
        # 2. 策略参数类型验证
        if strategy_params is None:
            st.error("❌ 策略参数为None，请重新配置策略参数")
            return
        
        if isinstance(strategy_params, bool):
            st.error("❌ 检测到bool类型的策略参数，这是一个配置错误")
            st.error("💡 解决方案：请刷新页面重新配置策略参数")
            return
        
        if not isinstance(strategy_params, dict):
            st.error(f"❌ 策略参数类型错误: {type(strategy_params)}，期望字典类型")
            st.error("💡 解决方案：请重新选择策略并配置参数")
            return
        
        if len(strategy_params) == 0:
            st.error("❌ 策略参数字典为空")
            return
        
        # 3. 检查错误标记
        if strategy_params.get('error', False):
            error_msg = strategy_params.get('error_message', '未知错误')
            st.error(f"❌ 策略参数配置时发生错误: {error_msg}")
            return
        
        # 4. 验证策略参数完整性
        if not validate_strategy_params(strategy_name, strategy_params):
            st.error("❌ 策略参数验证失败，请检查参数配置")
            return
        
        progress_bar.progress(10)
        
        # 5. 配置策略
        status_text.text("⚙️ 配置策略参数...")
        progress_bar.progress(20)
        
        # 构建策略配置
        strategy_config = {
            'strategy_name': strategy_name,
            'initial_cash': initial_cash,
            'max_drawdown': max_drawdown / 100,
            'position_size': position_size / 100
        }
        
        # 添加具体策略参数
        if strategy_name == "双均线策略":
            strategy_config.update({
                'fast_period': strategy_params.get('fast_period', 10),
                'slow_period': strategy_params.get('slow_period', 30),
                'ma_type': strategy_params.get('ma_type', 'SMA')
            })
        elif strategy_name == "RSI策略":
            strategy_config.update({
                'rsi_period': strategy_params.get('rsi_period', 14),
                'rsi_oversold': strategy_params.get('rsi_oversold', 30),
                'rsi_overbought': strategy_params.get('rsi_overbought', 70)
            })
        elif strategy_name == "价格行为策略":
            strategy_config.update({
                'lookback_period': strategy_params.get('lookback_period', 20),
                'breakout_threshold': strategy_params.get('breakout_threshold', 0.02),
                'pullback_threshold': strategy_params.get('pullback_threshold', 0.05)
            })
        
        print(f"✅ 策略配置完成: {strategy_config}")
        
        # 创建策略模块
        strategy_module = StrategyModule(strategy_config)
        
        progress_bar.progress(40)
        
        # 6. 配置交易费用
        status_text.text("💰 配置交易费用...")
        
        trade_costs = {
            'commission': commission_rate,
            'stamp_tax': stamp_tax,
            'transfer_fee': transfer_fee,
            'min_commission': min_commission
        }
        
        progress_bar.progress(60)
        
        # 7. 保存配置到会话状态
        status_text.text("💾 保存配置参数...")
        
        st.session_state.strategy_params = {
            'strategy_name': strategy_name,
            'strategy_module': strategy_module,
            'strategy_config': strategy_config,
            'initial_cash': initial_cash,
            'max_drawdown': max_drawdown / 100,
            'position_size': position_size / 100,
            'trade_costs': trade_costs
        }
        
        st.session_state.strategy_configured = True
        
        progress_bar.progress(80)
        
        # 8. 初始化回测引擎
        status_text.text("🚀 初始化回测引擎...")
        
        backtest_module = BacktestModule()
        
        # 获取股票数据
        stock_data = st.session_state.get('stock_data', {})
        benchmark_data = st.session_state.get('benchmark_data', None)
        
        if not stock_data:
            st.error("❌ 股票数据不存在，请重新获取数据！")
            return
        
        progress_bar.progress(90)
        
        # 9. 运行回测
        status_text.text("📊 执行回测计算...")
        
        # 首先生成交易信号
        signals_data = strategy_module.generate_trading_signals(stock_data)
        
        if not signals_data:
            st.error("❌ 信号生成失败！")
            return
        
        # 执行回测
        results = backtest_module.execute_backtest(
            stock_data=stock_data,
            signals_data=signals_data,
            strategy_config=strategy_config,
            position_manager=strategy_module.position_manager,
            benchmark_data=benchmark_data
        )
        
        if results:
            # 保存回测结果
            st.session_state.backtest_results = results
            st.session_state.backtest_completed = True
            
            progress_bar.progress(100)
            status_text.text("🎉 回测完成！")
            
            st.success("✅ 策略配置成功，回测已完成！")
            st.balloons()
            
            # 显示简要结果
            display_quick_results(results)
            
            st.info("🎯 回测完成！请在侧边栏点击 '📊 回测报告' 查看详细结果。")
            
        else:
            st.error("❌ 回测执行失败！")
    
    except Exception as e:
        error_msg = str(e) if e is not None else "未知错误"
        st.error(f"❌ 策略配置过程中发生错误: {error_msg}")
        
        # 添加详细错误信息用于调试
        with st.expander("🔍 详细错误信息", expanded=False):
            st.code(f"""
错误类型: {type(e).__name__ if e is not None else 'Unknown'}
错误描述: {error_msg}
策略名称: {strategy_name}
策略参数类型: {type(strategy_params)}
策略参数内容: {strategy_params}
            """)
        
        # 提供解决建议
        st.markdown("### 💡 解决建议")
        if isinstance(strategy_params, bool):
            st.warning("检测到bool类型参数错误，建议：")
            st.write("1. 刷新页面")
            st.write("2. 重新选择策略")
            st.write("3. 重新配置参数")
        else:
            st.info("通用解决方案：")
            st.write("1. 检查股票数据是否已获取")
            st.write("2. 确认策略参数配置完整")
            st.write("3. 尝试刷新页面重新配置")
    
    finally:
        progress_bar.empty()
        status_text.empty()

def validate_strategy_params(strategy_name: str, strategy_params: dict) -> bool:
    """验证策略参数完整性"""
    
    try:
        if strategy_name == "双均线策略":
            required_keys = ['fast_period', 'slow_period', 'ma_type']
            missing_keys = [key for key in required_keys if key not in strategy_params]
            if missing_keys:
                st.error(f"❌ 双均线策略缺少参数: {missing_keys}")
                return False
            
            # 验证参数值
            if strategy_params['fast_period'] >= strategy_params['slow_period']:
                st.error("❌ 快线周期必须小于慢线周期")
                return False
                
        elif strategy_name == "RSI策略":
            required_keys = ['rsi_period', 'rsi_oversold', 'rsi_overbought']
            missing_keys = [key for key in required_keys if key not in strategy_params]
            if missing_keys:
                st.error(f"❌ RSI策略缺少参数: {missing_keys}")
                return False
            
            # 验证参数值
            if strategy_params['rsi_oversold'] >= strategy_params['rsi_overbought']:
                st.error("❌ 超卖阈值必须小于超买阈值")
                return False
                
        elif strategy_name == "价格行为策略":
            required_keys = ['lookback_period', 'breakout_threshold', 'pullback_threshold']
            missing_keys = [key for key in required_keys if key not in strategy_params]
            if missing_keys:
                st.error(f"❌ 价格行为策略缺少参数: {missing_keys}")
                return False
        
        print(f"✅ 策略参数验证通过: {strategy_name}")
        return True
        
    except Exception as e:
        st.error(f"❌ 参数验证过程中发生错误: {e}")
        return False

def display_quick_results(results):
    """显示快速结果预览"""
    
    if not results:
        return
    
    st.markdown("### 📊 回测结果预览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 获取第一个股票的结果作为示例
    first_stock = list(results.keys())[0]
    first_result = results[first_stock]
    
    with col1:
        total_return = first_result.get('total_return', 0)
        st.metric(
            "总收益率",
            f"{total_return:.2f}%",
            delta=f"{total_return:.2f}%"
        )
    
    with col2:
        sharpe_ratio = first_result.get('sharpe_ratio', 0)
        st.metric(
            "夏普比率",
            f"{sharpe_ratio:.2f}",
            delta="higher is better"
        )
    
    with col3:
        max_drawdown = first_result.get('max_drawdown', 0)
        st.metric(
            "最大回撤",
            f"{max_drawdown:.2f}%",
            delta=f"-{max_drawdown:.2f}%"
        )
    
    with col4:
        win_rate = first_result.get('win_rate', 0)
        st.metric(
            "胜率",
            f"{win_rate:.1f}%",
            delta=f"{win_rate:.1f}%"
        )
    
    # 显示所有股票的简要结果
    with st.expander("📋 所有股票回测结果", expanded=False):
        for symbol, result in results.items():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**{symbol}**")
            with col2:
                st.write(f"收益: {result.get('total_return', 0):.2f}%")
            with col3:
                st.write(f"回撤: {result.get('max_drawdown', 0):.2f}%")
            with col4:
                st.write(f"胜率: {result.get('win_rate', 0):.1f}%")

if __name__ == "__main__":
    show() 
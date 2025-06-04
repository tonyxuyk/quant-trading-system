"""
选股页模块
股票选择和数据获取
"""

import streamlit as st
import pandas as pd
import akshare as ak
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
from pypinyin import lazy_pinyin

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_backend.database_module import DatabaseModule

def show():
    """显示选股页面"""
    st.markdown("# 📈 股票选择与数据获取")
    st.markdown("### 选择要回测的股票和参数")
    
    # 检查前置条件
    if not st.session_state.get('libraries_loaded', False):
        st.error("❌ 请先在首页完成库导入！")
        return
    
    st.markdown("---")
    
    # 股票选择区域
    st.markdown("## 1️⃣ 市场与股票选择")
    
    # 市场选择
    st.markdown("### 🌍 选择交易市场")
    
    market_options = {
        "🇨🇳 A股市场": "A_STOCK",
        "🇭🇰 港股市场": "HK_STOCK", 
        "🇺🇸 美股市场": "US_STOCK"
    }
    
    selected_market_name = st.radio(
        "选择要交易的市场:",
        list(market_options.keys()),
        horizontal=True,
        help="选择不同市场将使用对应的数据源"
    )
    
    selected_market = market_options[selected_market_name]
    
    # 根据市场显示不同的示例
    market_examples = {
        "A_STOCK": {
            "代码示例": "000001, 600000, 000858",
            "名称示例": "平安银行, 浦发银行, 五粮液",
            "说明": "A股支持深交所(000xxx, 002xxx)和上交所(600xxx)代码"
        },
        "HK_STOCK": {
            "代码示例": "00700, 00941, 00005",
            "名称示例": "腾讯控股, 中国移动, 汇丰控股", 
            "说明": "港股代码通常为5位数字，也可带.HK后缀"
        },
        "US_STOCK": {
            "代码示例": "AAPL, MSFT, GOOGL",
            "名称示例": "Apple Inc., Microsoft Corp., Alphabet Inc.",
            "说明": "美股代码通常为英文字母组合"
        }
    }
    
    current_examples = market_examples[selected_market]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 股票输入方式选择
        if selected_market == "US_STOCK":
            # 美股主要使用股票代码
            input_method = st.radio(
                "选择输入方式:",
                ["股票代码", "股票名称"],
                horizontal=True
            )
        else:
            # A股和港股支持更多输入方式
            input_method = st.radio(
                "选择输入方式:",
                ["股票代码", "股票名称", "拼音输入"],
                horizontal=True
            )
        
        if input_method == "股票代码":
            stock_input = st.text_input(
                f"请输入{selected_market_name.split(' ')[1]}股票代码",
                placeholder=f"如: {current_examples['代码示例']}",
                help=f"{current_examples['说明']}，支持多个代码用逗号分隔"
            )
        elif input_method == "股票名称":
            stock_input = st.text_input(
                f"请输入{selected_market_name.split(' ')[1]}股票名称",
                placeholder=f"如: {current_examples['名称示例']}",
                help="输入完整的股票名称，支持多个名称用逗号分隔"
            )
        else:  # 拼音输入 (仅A股和港股)
            stock_input = st.text_input(
                "请输入股票名称拼音",
                placeholder="如: payh, pfyh (平安银行, 浦发银行)",
                help="支持拼音缩写，如平安银行可输入'payh'"
            )
        
        # 显示热门股票快速选择
        st.markdown("### 🔥 热门股票快速选择")
        if st.button("显示热门股票"):
            show_popular_stocks(selected_market)
    
    with col2:
        st.markdown("### 💡 输入提示")
        
        if selected_market == "A_STOCK":
            st.info(f"""
            **{selected_market_name} 示例:**
            - 平安银行: 000001
            - 浦发银行: 600000
            - 五粮液: 000858
            - 招商银行: 600036
            
            **支持格式:**
            - 单个: 000001
            - 多个: 000001,600000
            """)
        elif selected_market == "HK_STOCK":
            st.info(f"""
            **{selected_market_name} 示例:**
            - 腾讯控股: 00700
            - 中国移动: 00941
            - 汇丰控股: 00005
            - 友邦保险: 01299
            
            **支持格式:**
            - 标准: 00700
            - 带后缀: 00700.HK
            """)
        else:  # US_STOCK
            st.info(f"""
            **{selected_market_name} 示例:**
            - 苹果: AAPL
            - 微软: MSFT
            - 谷歌: GOOGL
            - 亚马逊: AMZN
            
            **支持格式:**
            - 标准: AAPL
            - 多个: AAPL,MSFT
            """)
    
    # 如果选择了港股或美股，显示特殊提示
    if selected_market == "HK_STOCK":
        st.info("🇭🇰 港股数据通过AKShare接口获取，支持实时和历史数据")
    elif selected_market == "US_STOCK":
        st.warning("🇺🇸 美股数据通过Alpha Vantage接口获取，每分钟限制5次请求，请耐心等待")
    
    # 保存市场选择到session state
    st.session_state.selected_market = selected_market
    
    # 时间选择区域
    st.markdown("## 2️⃣ 回测时间设置")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now().date()
        )
    
    with col2:
        end_date = st.date_input(
            "结束日期", 
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
    
    with col3:
        # 快速时间选择
        quick_period = st.selectbox(
            "快速选择时间段",
            ["自定义", "最近1个月", "最近3个月", "最近6个月", "最近1年", "最近2年"],
            help="选择预设时间段将自动设置开始和结束日期"
        )
        
        if quick_period != "自定义":
            if quick_period == "最近1个月":
                start_date = datetime.now().date() - timedelta(days=30)
            elif quick_period == "最近3个月":
                start_date = datetime.now().date() - timedelta(days=90)
            elif quick_period == "最近6个月":
                start_date = datetime.now().date() - timedelta(days=180)
            elif quick_period == "最近1年":
                start_date = datetime.now().date() - timedelta(days=365)
            elif quick_period == "最近2年":
                start_date = datetime.now().date() - timedelta(days=730)
            
            end_date = datetime.now().date()
    
    # K线时间级别选择
    st.markdown("## 3️⃣ K线时间级别")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        timeframe_options = {
            "1分钟": "1m",
            "5分钟": "5m", 
            "15分钟": "15m",
            "30分钟": "30m",
            "1小时": "1h",
            "1日": "1d",
            "1周": "1w",
            "1月": "1M"
        }
        
        selected_timeframe = st.selectbox(
            "选择K线时间级别",
            list(timeframe_options.keys()),
            index=5,  # 默认选择1日
            help="选择用于回测的K线数据时间级别"
        )
    
    with col2:
        st.markdown("### ⏰ 时间级别说明")
        st.info("""
        **推荐设置:**
        - 短线交易: 1分钟-1小时
        - 中线交易: 1日-1周  
        - 长线交易: 1日-1月
        
        **注意:** 时间级别越小，数据量越大，回测时间越长
        """)
    
    st.markdown("---")
    
    # 参数确认和数据获取
    st.markdown("## 4️⃣ 确认参数并获取数据")
    
    # 显示当前设置
    with st.expander("📋 当前设置预览", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **股票设置:**
            - 输入方式: {input_method}
            - 股票输入: {stock_input if stock_input else '未输入'}
            - 时间范围: {start_date} 至 {end_date}
            """)
        
        with col2:
            st.markdown(f"""
            **数据设置:**
            - K线级别: {selected_timeframe}
            - 数据天数: {(end_date - start_date).days} 天
            - 基准配置: 在策略配置页面设置
            """)
    
    # 数据获取按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 开始获取数据", type="primary", use_container_width=True):
            if not stock_input:
                st.error("❌ 请先输入股票信息!")
            elif start_date >= end_date:
                st.error("❌ 开始日期必须早于结束日期!")
            else:
                # 获取数据
                fetch_stock_data(
                    stock_input=stock_input,
                    input_method=input_method,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe_options[selected_timeframe],
                    market=selected_market  # 新增市场参数
                )

def show_popular_stocks(market: str):
    """显示热门股票列表"""
    try:
        # 初始化数据模块
        db = DatabaseModule()
        popular_stocks = db.get_popular_stocks(market)
        
        if popular_stocks:
            st.markdown("### 🔥 热门股票列表")
            
            # 创建多列布局显示股票
            cols = st.columns(3)
            
            for i, stock in enumerate(popular_stocks):
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(f"{stock['code']} - {stock['name']}", key=f"popular_{stock['code']}"):
                        # 当用户点击时，自动填入股票代码
                        st.session_state.auto_fill_stock = stock['code']
                        st.rerun()
        else:
            st.warning(f"暂无{market}热门股票数据")
            
    except Exception as e:
        st.error(f"获取热门股票失败: {e}")

def fetch_stock_data(stock_input, input_method, start_date, end_date, timeframe, market):
    """获取股票数据"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 1. 解析股票输入
        status_text.text("🔍 解析股票输入...")
        progress_bar.progress(10)
        
        stock_codes = parse_stock_input(stock_input, input_method, market)
        
        if not stock_codes:
            st.error("❌ 未找到有效的股票代码！")
            return
        
        st.success(f"✅ 解析到 {len(stock_codes)} 只股票: {', '.join(stock_codes)}")
        
        # 2. 初始化数据模块
        status_text.text("📊 初始化数据模块...")
        progress_bar.progress(20)
        
        db = DatabaseModule()
        
        # 3. 获取股票数据
        status_text.text("📈 获取股票数据...")
        progress_bar.progress(40)
        
        stock_data = {}
        total_stocks = len(stock_codes)
        
        for i, code in enumerate(stock_codes):
            status_text.text(f"📈 获取股票数据... ({i+1}/{total_stocks}) {code}")
            
            # 使用新的市场参数
            data = db.get_stock_data(
                symbol=code,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                market=market
            )
            
            if data is not None:
                stock_data[code] = data
                st.success(f"✅ {code} 数据获取成功")
            else:
                st.warning(f"⚠️ {code} 数据获取失败")
            
            # 更新进度
            progress = 40 + (i + 1) / total_stocks * 40
            progress_bar.progress(int(progress))
        
        if not stock_data:
            st.error("❌ 没有成功获取任何股票数据！")
            return
        
        # 4. 获取基准数据
        status_text.text("📊 获取基准数据...")
        progress_bar.progress(85)
        
        # 检查策略选择页面的基准配置
        selected_benchmarks = st.session_state.get('selected_benchmarks', {})
        benchmark_data = {}
        
        # 根据市场和用户选择获取基准数据
        if market == "A_STOCK":
            # A股基准数据
            if 'A_STOCK' in selected_benchmarks:
                benchmark_info = selected_benchmarks['A_STOCK']
                benchmark_symbol = benchmark_info['symbol']
                benchmark_name = benchmark_info['name']
                
                st.info(f"🔄 获取A股基准指数: {benchmark_name} ({benchmark_symbol})")
                
                bench_data = db.get_benchmark_data(
                    symbol=benchmark_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe
                )
                
                if bench_data is not None:
                    benchmark_data[benchmark_symbol] = bench_data
                    st.success(f"✅ A股基准数据获取成功: {benchmark_name}")
                else:
                    st.warning(f"⚠️ A股基准数据获取失败: {benchmark_name}")
            else:
                st.info("ℹ️ A股市场未配置基准指数，请在策略配置页面选择基准")
                
        elif market == "HK_STOCK":
            # 港股基准数据
            if 'HK_STOCK' in selected_benchmarks:
                benchmark_info = selected_benchmarks['HK_STOCK']
                benchmark_symbol = benchmark_info['symbol']
                benchmark_name = benchmark_info['name']
                
                st.info(f"🔄 获取港股基准指数: {benchmark_name} ({benchmark_symbol})")
                
                bench_data = db.get_benchmark_data(
                    symbol=benchmark_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe
                )
                
                if bench_data is not None:
                    benchmark_data[benchmark_symbol] = bench_data
                    st.success(f"✅ 港股基准数据获取成功: {benchmark_name}")
                else:
                    st.warning(f"⚠️ 港股基准数据获取失败: {benchmark_name}")
            else:
                st.info("ℹ️ 港股市场未配置基准指数，请在策略配置页面选择基准")
                
        elif market == "US_STOCK":
            # 美股基准数据
            if 'US_STOCK' in selected_benchmarks:
                benchmark_info = selected_benchmarks['US_STOCK']
                benchmark_symbol = benchmark_info['symbol']
                benchmark_name = benchmark_info['name']
                
                st.info(f"🔄 获取美股基准指数: {benchmark_name} ({benchmark_symbol})")
                
                bench_data = db.get_benchmark_data(
                    symbol=benchmark_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe
                )
                
                if bench_data is not None:
                    benchmark_data[benchmark_symbol] = bench_data
                    st.success(f"✅ 美股基准数据获取成功: {benchmark_name}")
                else:
                    st.warning(f"⚠️ 美股基准数据获取失败: {benchmark_name}")
            else:
                st.info("ℹ️ 美股市场未配置基准指数，请在策略配置页面选择基准")
        
        # 转换为单一基准数据格式（保持向后兼容）
        final_benchmark_data = None
        if benchmark_data:
            # 使用第一个基准数据
            first_key = list(benchmark_data.keys())[0]
            final_benchmark_data = benchmark_data[first_key]
        else:
            st.info("ℹ️ 未配置基准指数，回测时将无法进行基准对比")
        
        # 5. 保存到session state
        status_text.text("💾 保存数据...")
        progress_bar.progress(95)
        
        st.session_state.stock_data = stock_data
        st.session_state.benchmark_data = final_benchmark_data
        st.session_state.selected_stocks = stock_codes
        st.session_state.selected_period = (start_date, end_date)
        st.session_state.selected_timeframe = timeframe
        st.session_state.selected_market = market  # 保存市场信息
        st.session_state.data_loaded = True
        
        # 6. 显示结果
        progress_bar.progress(100)
        status_text.text("🎉 数据获取完成！")
        
        st.success(f"🎉 数据获取完成！共获取 {len(stock_data)} 只股票数据")
        st.balloons()
        
        # 显示数据预览
        display_data_preview(stock_data, final_benchmark_data, market)
        
        # 提示下一步
        st.info("✨ 数据获取完成！现在可以前往 '⚙️ 策略选择' 页面配置交易策略。")
        
    except Exception as e:
        st.error(f"❌ 数据获取过程中发生错误: {str(e)}")
        
    finally:
        progress_bar.empty()
        status_text.empty()

def parse_stock_input(stock_input, input_method, market):
    """解析股票输入 (增强版)"""
    
    if not stock_input:
        return []
    
    # 清理输入并分割
    codes = [code.strip().upper() for code in stock_input.replace('，', ',').split(',') if code.strip()]
    result_codes = []
    
    for code in codes:
        if input_method == "股票代码":
            # 直接使用股票代码
            if market == "A_STOCK":
                # A股代码验证
                if code.isdigit() and len(code) == 6:
                    result_codes.append(code)
                else:
                    st.warning(f"⚠️ 无效的A股代码: {code} (应为6位数字)")
                    
            elif market == "HK_STOCK":
                # 港股代码处理
                clean_code = code.replace('.HK', '').replace('.hk', '')
                if clean_code.isdigit() and len(clean_code) <= 5:
                    # 补齐到5位
                    padded_code = clean_code.zfill(5)
                    result_codes.append(padded_code)
                    print(f"✅ 港股代码格式化: {code} -> {padded_code}")
                else:
                    st.warning(f"⚠️ 无效的港股代码: {code} (应为数字且不超过5位)")
                    
            elif market == "US_STOCK":
                # 美股代码验证
                if code.isalpha() and len(code) <= 6:
                    result_codes.append(code.upper())
                else:
                    st.warning(f"⚠️ 无效的美股代码: {code} (应为字母组合)")
                    
        elif input_method == "股票名称":
            # 通过名称查找代码
            if market == "A_STOCK":
                stock_code = find_stock_code_by_name(code)
                if stock_code:
                    result_codes.append(stock_code)
                else:
                    st.warning(f"⚠️ 未找到股票: {code}")
            else:
                # 港股和美股名称查找功能待扩展
                st.warning(f"暂不支持{market}的名称查找功能，请使用股票代码")
                
        elif input_method == "拼音输入" and market in ["A_STOCK", "HK_STOCK"]:
            # 拼音查找（主要用于A股）
            if market == "A_STOCK":
                stock_code = find_stock_code_by_pinyin(code)
                if stock_code:
                    result_codes.append(stock_code)
                else:
                    st.warning(f"⚠️ 未找到股票: {code}")
    
    return result_codes

def find_stock_code_by_name(stock_name):
    """通过股票名称查找代码"""
    # 这里应该实现股票名称到代码的映射
    # 由于空间限制，这里提供一个简化版本
    
    stock_dict = {
        "平安银行": "000001",
        "万科A": "000002", 
        "浦发银行": "600000",
        "中国石化": "600028",
        "民生银行": "600016",
        "招商银行": "600036",
        "中国平安": "601318",
        "贵州茅台": "600519",
        "中国建筑": "601668",
        "中国银行": "601988"
    }
    
    return stock_dict.get(stock_name)

def find_stock_code_by_pinyin(pinyin_input):
    """通过拼音查找股票代码"""
    # 这里应该实现拼音到股票代码的映射
    # 简化版本
    
    pinyin_dict = {
        "payh": "000001",  # 平安银行
        "wka": "000002",   # 万科A
        "pfyh": "600000",  # 浦发银行
        "zsyh": "600036",  # 招商银行
        "zgpa": "601318",  # 中国平安
        "gzmt": "600519",  # 贵州茅台
    }
    
    return pinyin_dict.get(pinyin_input.lower())

def display_data_preview(stock_data, benchmark_data, market):
    """显示数据预览"""
    
    if not stock_data:
        return
    
    # 市场信息显示
    market_names = {
        "A_STOCK": "🇨🇳 A股市场",
        "HK_STOCK": "🇭🇰 港股市场", 
        "US_STOCK": "🇺🇸 美股市场"
    }
    
    st.markdown("### 📊 数据预览")
    st.markdown(f"**交易市场**: {market_names.get(market, market)}")
    
    # 基本统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("股票数量", len(stock_data))
    
    # 计算数据统计
    total_records = sum(len(df) for df in stock_data.values())
    with col2:
        st.metric("总数据条数", total_records)
    
    # 获取日期范围
    all_dates = []
    for df in stock_data.values():
        all_dates.extend(df.index.tolist())
    
    if all_dates:
        with col3:
            earliest_date = min(all_dates).strftime('%Y-%m-%d')
            st.metric("最早日期", earliest_date)
        
        with col4:
            latest_date = max(all_dates).strftime('%Y-%m-%d')
            st.metric("最新日期", latest_date)
    
    # 股票列表
    with st.expander("📋 股票数据详情", expanded=False):
        for symbol, data in stock_data.items():
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                st.write(f"**{symbol}**")
            
            with col2:
                st.write(f"数据条数: {len(data)}")
            
            with col3:
                if not data.empty:
                    latest_price = data['close'].iloc[-1]
                    st.write(f"最新价格: {latest_price:.2f}")
    
    # 基准数据信息
    if benchmark_data is not None and not benchmark_data.empty:
        st.markdown("### 📈 基准数据")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("基准数据条数", len(benchmark_data))
        
        with col2:
            if not benchmark_data.empty:
                latest_benchmark = benchmark_data['close'].iloc[-1]
                st.metric("基准最新值", f"{latest_benchmark:.2f}")
    elif market == "A_STOCK":
        st.info("ℹ️ 基准数据获取失败，回测时将无法进行基准对比")
    else:
        st.info(f"ℹ️ {market_names.get(market, market)} 暂不支持基准对比")
    
    # 数据质量检查
    st.markdown("### 🔍 数据质量检查")
    
    quality_issues = []
    
    for symbol, data in stock_data.items():
        if data.empty:
            quality_issues.append(f"{symbol}: 数据为空")
        elif len(data) < 10:
            quality_issues.append(f"{symbol}: 数据量过少 ({len(data)} 条)")
        elif data.isnull().sum().sum() > 0:
            null_count = data.isnull().sum().sum()
            quality_issues.append(f"{symbol}: 存在 {null_count} 个缺失值")
    
    if quality_issues:
        st.warning("⚠️ 发现数据质量问题:")
        for issue in quality_issues:
            st.write(f"- {issue}")
    else:
        st.success("✅ 数据质量检查通过")

# 添加数据管理功能
def show_data_management():
    """显示数据管理功能"""
    
    with st.expander("🗂️ 数据管理", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清除所有数据"):
                clear_all_data()
        
        with col2:
            if st.button("📁 查看本地数据"):
                show_local_data()

def clear_all_data():
    """清除所有数据"""
    # 清除session state中的数据
    keys_to_clear = ['stock_data', 'benchmark_data', 'selected_stocks', 'data_loaded']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.success("✅ 所有数据已清除")
    st.rerun()

def show_local_data():
    """显示本地数据文件"""
    data_dir = "stock-data"
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        if files:
            st.write("**本地数据文件：**")
            for file in files:
                st.write(f"- {file}")
        else:
            st.info("暂无本地数据文件")
    else:
        st.info("数据目录不存在") 
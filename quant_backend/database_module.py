#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易算法后台 - 数据库模块
功能：数据获取、数据处理、数据传输
支持A股、港股、美股数据获取
"""

import pandas as pd
import numpy as np
import os
import datetime as dt
from typing import Dict, List, Tuple, Optional
import logging
import requests
import time

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseModule:
    """数据库模块 - 负责数据获取、处理和传输"""
    
    def __init__(self, tushare_token: str = "dfb371512cbe14cc65084a2dbdc5429990f605aa802d48bd2dd9146c",
                 alpha_vantage_key: str = "SNZ3VYIZTR69SJYD"):
        """初始化数据库模块"""
        self.tushare_token = tushare_token
        self.alpha_vantage_key = alpha_vantage_key
        self.data_dir = "stock-data"
        self.ensure_data_directory()
        
        # 初始化数据源
        self.akshare_available = self._init_akshare()
        self.tushare_available = self._init_tushare()
        self.alpha_vantage_available = self._init_alpha_vantage()
        
        print("📊 多市场数据库模块初始化完成")
        self._print_supported_markets()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"✅ 创建数据目录: {self.data_dir}")
    
    def _init_akshare(self) -> bool:
        """初始化AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            print("✅ AKShare初始化成功 (支持A股/港股)")
            return True
        except ImportError:
            print("❌ AKShare未安装")
            return False
    
    def _init_tushare(self) -> bool:
        """初始化Tushare"""
        try:
            import tushare as ts
            ts.set_token(self.tushare_token)
            self.ts_pro = ts.pro_api()
            self.ts = ts
            print("✅ Tushare初始化成功 (A股数据源)")
            return True
        except ImportError:
            print("❌ Tushare未安装")
            return False
        except Exception as e:
            print(f"❌ Tushare初始化失败: {e}")
            return False
    
    def _init_alpha_vantage(self) -> bool:
        """初始化Alpha Vantage"""
        if not self.alpha_vantage_key:
            print("❌ Alpha Vantage API Key未设置")
            return False
        
        try:
            # 测试API连接
            test_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey={self.alpha_vantage_key}&outputsize=compact"
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "Error Message" not in data and "Note" not in data:
                    print("✅ Alpha Vantage初始化成功 (美股数据源)")
                    return True
                else:
                    print("❌ Alpha Vantage API配额限制或错误")
                    return False
            else:
                print("❌ Alpha Vantage连接失败")
                return False
        except Exception as e:
            print(f"❌ Alpha Vantage初始化失败: {e}")
            return False
    
    def _print_supported_markets(self):
        """打印支持的市场"""
        markets = []
        if self.akshare_available:
            markets.extend(["🇨🇳 A股", "🇭🇰 港股"])
        if self.alpha_vantage_available:
            markets.append("🇺🇸 美股")
        
        if markets:
            print(f"🌍 支持的市场: {' | '.join(markets)}")
        else:
            print("⚠️ 无可用数据源")
    
    def detect_market(self, symbol: str) -> str:
        """
        检测股票代码所属市场
        
        Args:
            symbol: 股票代码
            
        Returns:
            市场类型: 'A_STOCK', 'HK_STOCK', 'US_STOCK'
        """
        symbol = symbol.upper().strip()
        
        # 美股检测 (通常是字母组合)
        if symbol.isalpha() and len(symbol) <= 5:
            return 'US_STOCK'
        
        # 港股检测 (港股代码通常是数字，且以特定数字开头)
        if symbol.isdigit():
            code_num = int(symbol)
            # 港股代码范围
            if (1 <= code_num <= 9999) and len(symbol) <= 5:
                return 'HK_STOCK'
        
        # A股检测 (6位数字)
        if symbol.isdigit() and len(symbol) == 6:
            return 'A_STOCK'
        
        # 带后缀的代码检测
        if '.' in symbol:
            prefix, suffix = symbol.split('.', 1)
            if suffix.upper() in ['HK']:
                return 'HK_STOCK'
            elif suffix.upper() in ['SH', 'SZ']:
                return 'A_STOCK'
        
        # 默认为A股
        return 'A_STOCK'
    
    def get_stock_data(self, symbol: str, start_date, end_date, 
                      timeframe: str = "1d", market: str = None) -> Optional[pd.DataFrame]:
        """
        获取单只股票数据 (支持多市场)
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 YYYY-MM-DD 或 date对象
            end_date: 结束日期 YYYY-MM-DD 或 date对象
            timeframe: 时间级别 1d/1w/1m
            market: 指定市场类型，为空则自动检测
            
        Returns:
            股票数据DataFrame
        """
        # 自动检测市场
        if market is None:
            market = self.detect_market(symbol)
        
        market_name = {'A_STOCK': 'A股', 'HK_STOCK': '港股', 'US_STOCK': '美股'}[market]
        print(f"🔍 正在获取 {market_name} {symbol} 数据...")
        
        # 转换日期格式
        start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
        end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
        
        # 根据市场选择数据源
        data = None
        
        if market == 'A_STOCK':
            data = self._fetch_a_stock_data(symbol, start_str, end_str, timeframe)
        elif market == 'HK_STOCK':
            data = self._fetch_hk_stock_data(symbol, start_str, end_str, timeframe)
        elif market == 'US_STOCK':
            data = self._fetch_us_stock_data(symbol, start_str, end_str, timeframe)
        
        if data is not None and not data.empty:
            # 数据处理和验证
            processed_data = self._process_and_validate_data(data, f"{market}_{symbol}")
            if processed_data is not None:
                # 保存数据
                self._save_data(processed_data, f"{market}_{symbol}", timeframe)
                print(f"✅ {market_name} {symbol} 数据获取成功，共 {len(processed_data)} 条记录")
                return processed_data
            else:
                print(f"❌ {market_name} {symbol} 数据处理失败")
        else:
            print(f"❌ {market_name} {symbol} 数据获取失败")
        
        return None
    
    def _fetch_a_stock_data(self, symbol: str, start_date: str, 
                           end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取A股数据"""
        # 优先使用AKShare
        data = self._fetch_with_akshare(symbol, start_date, end_date, timeframe)
        
        if data is None or data.empty:
            print(f"🔄 AKShare获取失败，尝试Tushare...")
            data = self._fetch_with_tushare(symbol, start_date, end_date)
        
        return data
    
    def _fetch_hk_stock_data(self, symbol: str, start_date: str, 
                            end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取港股数据"""
        if not self.akshare_available:
            print("❌ AKShare不可用，无法获取港股数据")
            return None
        
        try:
            # 确保港股代码格式正确
            hk_symbol = symbol.replace('.HK', '').replace('.hk', '')
            if not hk_symbol.isdigit():
                print(f"❌ 无效的港股代码格式: {symbol}")
                return None
            
            # 补齐港股代码到5位
            hk_symbol = hk_symbol.zfill(5)
            
            print(f"🔄 使用AKShare获取港股 {hk_symbol} 数据...")
            
            # 使用AKShare获取港股数据
            df = self.ak.stock_hk_hist(
                symbol=hk_symbol,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"
            )
            
            if df is not None and not df.empty:
                # 标准化列名 (港股数据格式可能不同)
                if len(df.columns) >= 6:
                    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume'] + list(df.columns[6:])
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                print(f"✅ AKShare获取港股 {hk_symbol} 数据成功")
                return df
            
        except Exception as e:
            print(f"❌ AKShare获取港股 {symbol} 失败: {e}")
        
        return None
    
    def _fetch_us_stock_data(self, symbol: str, start_date: str, 
                            end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取美股数据"""
        if not self.alpha_vantage_available:
            print("❌ Alpha Vantage不可用，无法获取美股数据")
            return None
        
        try:
            print(f"🔄 使用Alpha Vantage获取美股 {symbol} 数据...")
            
            # Alpha Vantage API参数映射
            function_map = {
                "1d": "TIME_SERIES_DAILY",
                "1w": "TIME_SERIES_WEEKLY", 
                "1m": "TIME_SERIES_MONTHLY"
            }
            
            function = function_map.get(timeframe, "TIME_SERIES_DAILY")
            
            # 构建API请求
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol.upper(),
                "apikey": self.alpha_vantage_key,
                "outputsize": "full"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查API响应
                if "Error Message" in data:
                    print(f"❌ Alpha Vantage错误: {data['Error Message']}")
                    return None
                
                if "Note" in data:
                    print(f"❌ Alpha Vantage限制: {data['Note']}")
                    return None
                
                # 获取时间序列数据
                time_series_key = None
                for key in data.keys():
                    if "Time Series" in key:
                        time_series_key = key
                        break
                
                if time_series_key and time_series_key in data:
                    time_series = data[time_series_key]
                    
                    # 转换为DataFrame
                    df_data = []
                    for date_str, values in time_series.items():
                        df_data.append({
                            'date': pd.to_datetime(date_str),
                            'open': float(values.get('1. open', 0)),
                            'high': float(values.get('2. high', 0)),
                            'low': float(values.get('3. low', 0)),
                            'close': float(values.get('4. close', 0)),
                            'volume': float(values.get('5. volume', 0))
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.set_index('date', inplace=True)
                        df.sort_index(inplace=True)
                        
                        # 过滤日期范围
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date)
                        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                        
                        print(f"✅ Alpha Vantage获取美股 {symbol} 数据成功")
                        
                        # API限制：避免频繁请求
                        time.sleep(0.5)
                        
                        return df
                
                print(f"❌ Alpha Vantage未返回有效的时间序列数据")
                return None
            
            else:
                print(f"❌ Alpha Vantage请求失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Alpha Vantage获取美股 {symbol} 失败: {e}")
            return None
    
    def get_benchmark_data(self, symbol: str, start_date, end_date, 
                          timeframe: str = "1d") -> Optional[pd.DataFrame]:
        """
        获取基准指数数据 (修复后的方法签名，支持多市场)
        
        Args:
            symbol: 指数代码 (如 000300.SH, HSI, ^GSPC)
            start_date: 开始日期
            end_date: 结束日期
            timeframe: 时间级别
            
        Returns:
            基准数据DataFrame
        """
        print(f"📈 正在获取基准指数数据: {symbol}")
        
        # 转换日期格式
        start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
        end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
        
        # 检测基准指数类型
        if symbol.startswith('^'):
            # 美股指数
            return self._fetch_us_benchmark_data(symbol, start_str, end_str, timeframe)
        elif symbol in ['HSI', 'HSTECH']:
            # 港股指数
            return self._fetch_hk_benchmark_data(symbol, start_str, end_str, timeframe)
        else:
            # A股指数
            return self._fetch_a_benchmark_data(symbol, start_str, end_str, timeframe)
    
    def _fetch_a_benchmark_data(self, symbol: str, start_date: str, 
                               end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取A股基准指数数据"""
        # 提取指数代码 (去掉.SH/.SZ后缀)
        index_code = symbol.split('.')[0]
        
        # 优先获取指数数据
        benchmark_data = self._fetch_benchmark_akshare(index_code, start_date, end_date)
        
        if benchmark_data is None or benchmark_data.empty:
            print("🔄 尝试Tushare获取基准数据...")
            benchmark_data = self._fetch_benchmark_tushare(symbol, start_date, end_date)
        
        if benchmark_data is not None and not benchmark_data.empty:
            processed_data = self._process_and_validate_data(benchmark_data, f"benchmark_{index_code}")
            if processed_data is not None:
                self._save_data(processed_data, f"benchmark_{index_code}", timeframe)
                print(f"✅ A股基准数据获取成功，共 {len(processed_data)} 条记录")
                return processed_data
        
        print(f"❌ A股基准数据获取失败: {symbol}")
        return None
    
    def _fetch_hk_benchmark_data(self, symbol: str, start_date: str, 
                                end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取港股基准指数数据"""
        if not self.akshare_available:
            print("❌ AKShare不可用，无法获取港股基准数据")
            return None
        
        try:
            print(f"🔄 使用AKShare获取港股指数 {symbol} 数据...")
            
            # 港股指数映射
            hk_index_map = {
                'HSI': '恒生指数',
                'HSTECH': '恒生科技指数'
            }
            
            if symbol == 'HSI':
                # 获取恒生指数
                df = self.ak.stock_hk_index_spot_em()
                # 查找恒生指数数据
                hsi_data = df[df['名称'].str.contains('恒生指数')]
                if not hsi_data.empty:
                    # 获取历史数据
                    df = self.ak.stock_hk_index_daily_em(symbol="HSI")
                else:
                    print(f"❌ 未找到恒生指数数据")
                    return None
            elif symbol == 'HSTECH':
                # 获取恒生科技指数
                df = self.ak.stock_hk_index_daily_em(symbol="HSTECH")
            else:
                print(f"❌ 不支持的港股指数: {symbol}")
                return None
            
            if df is not None and not df.empty:
                # 标准化数据格式
                if 'date' not in df.columns:
                    if '日期' in df.columns:
                        df.rename(columns={'日期': 'date'}, inplace=True)
                    elif df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex):
                        df.reset_index(inplace=True)
                
                # 标准化列名
                column_mapping = {
                    '开盘': 'open', '最高': 'high', '最低': 'low', 
                    '收盘': 'close', '成交量': 'volume',
                    'Open': 'open', 'High': 'high', 'Low': 'low',
                    'Close': 'close', 'Volume': 'volume'
                }
                
                df.rename(columns=column_mapping, inplace=True)
                
                # 确保有必要的列
                required_cols = ['date', 'open', 'high', 'low', 'close']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    print(f"❌ 港股指数数据缺少必要列: {missing_cols}")
                    return None
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                
                # 过滤日期范围
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close'] + (['volume'] if 'volume' in df.columns else [])]
                
                print(f"✅ 港股指数 {symbol} 数据获取成功")
                return df
            
        except Exception as e:
            print(f"❌ AKShare获取港股指数 {symbol} 失败: {e}")
        
        return None
    
    def _fetch_us_benchmark_data(self, symbol: str, start_date: str, 
                                end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """获取美股基准指数数据"""
        if not self.alpha_vantage_available:
            print("❌ Alpha Vantage不可用，无法获取美股基准数据")
            return None
        
        try:
            print(f"🔄 使用Alpha Vantage获取美股指数 {symbol} 数据...")
            
            # 美股指数符号转换
            symbol_clean = symbol.replace('^', '')
            
            # Alpha Vantage API参数映射
            function_map = {
                "1d": "TIME_SERIES_DAILY",
                "1w": "TIME_SERIES_WEEKLY", 
                "1m": "TIME_SERIES_MONTHLY"
            }
            
            function = function_map.get(timeframe, "TIME_SERIES_DAILY")
            
            # 构建API请求
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "full"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查API响应
                if "Error Message" in data:
                    print(f"❌ Alpha Vantage错误: {data['Error Message']}")
                    return None
                
                if "Note" in data:
                    print(f"❌ Alpha Vantage限制: {data['Note']}")
                    return None
                
                # 获取时间序列数据
                time_series_key = None
                for key in data.keys():
                    if "Time Series" in key:
                        time_series_key = key
                        break
                
                if time_series_key and time_series_key in data:
                    time_series = data[time_series_key]
                    
                    # 转换为DataFrame
                    df_data = []
                    for date_str, values in time_series.items():
                        df_data.append({
                            'date': pd.to_datetime(date_str),
                            'open': float(values.get('1. open', 0)),
                            'high': float(values.get('2. high', 0)),
                            'low': float(values.get('3. low', 0)),
                            'close': float(values.get('4. close', 0)),
                            'volume': float(values.get('5. volume', 0))
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.set_index('date', inplace=True)
                        df.sort_index(inplace=True)
                        
                        # 过滤日期范围
                        start_dt = pd.to_datetime(start_date)
                        end_dt = pd.to_datetime(end_date)
                        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                        
                        print(f"✅ Alpha Vantage获取美股指数 {symbol} 数据成功")
                        
                        # API限制：避免频繁请求
                        time.sleep(0.5)
                        
                        return df
                
                print(f"❌ Alpha Vantage未返回有效的时间序列数据")
                return None
            
            else:
                print(f"❌ Alpha Vantage请求失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Alpha Vantage获取美股指数 {symbol} 失败: {e}")
            return None
    
    def _fetch_with_akshare(self, stock_code: str, start_date: str, 
                           end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """使用AKShare获取数据"""
        if not self.akshare_available:
            return None
        
        try:
            # 时间级别映射
            period_map = {
                "1d": "daily",
                "1w": "weekly", 
                "1m": "monthly"
            }
            
            period = period_map.get(timeframe, "daily")
            
            # 获取数据
            df = self.ak.stock_zh_a_hist(
                symbol=stock_code,
                period=period,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"  # 前复权
            )
            
            if df is not None and not df.empty:
                # 标准化列名
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 
                             'turnover', 'amplitude', 'change_pct', 'change_amount', 'turnover_rate']
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                print(f"✅ AKShare获取 {stock_code} 数据成功")
                return df
                
        except Exception as e:
            print(f"❌ AKShare获取 {stock_code} 失败: {e}")
            return None
    
    def _fetch_with_tushare(self, stock_code: str, start_date: str, 
                           end_date: str) -> Optional[pd.DataFrame]:
        """使用Tushare获取数据"""
        if not self.tushare_available:
            return None
        
        try:
            # 转换股票代码格式
            ts_code = self._convert_to_tushare_code(stock_code)
            
            # 获取数据
            df = self.ts_pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                # 转换日期格式
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
                df.sort_index(inplace=True)
                
                # 重命名列
                df = df.rename(columns={'vol': 'volume'})
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                print(f"✅ Tushare获取 {stock_code} 数据成功")
                return df
                
        except Exception as e:
            print(f"❌ Tushare获取 {stock_code} 失败: {e}")
            return None
    
    def _fetch_benchmark_akshare(self, index_code: str, start_date: str, 
                                end_date: str) -> Optional[pd.DataFrame]:
        """使用AKShare获取指数数据"""
        if not self.akshare_available:
            return None
        
        try:
            # 获取指数数据
            df = self.ak.index_zh_a_hist(
                symbol=index_code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                # 标准化列名
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'turnover']
                
                # 设置日期索引
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                return df
                
        except Exception as e:
            print(f"❌ AKShare获取指数 {index_code} 失败: {e}")
            return None
    
    def _fetch_benchmark_tushare(self, index_code: str, start_date: str, 
                                end_date: str) -> Optional[pd.DataFrame]:
        """使用Tushare获取指数数据"""
        if not self.tushare_available:
            return None
        
        try:
            # 获取指数数据
            df = self.ts_pro.index_daily(
                ts_code=index_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df is not None and not df.empty:
                # 转换日期格式
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
                df.sort_index(inplace=True)
                
                # 重命名列
                df = df.rename(columns={'vol': 'volume'})
                
                # 选择核心列
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                return df
                
        except Exception as e:
            print(f"❌ Tushare获取指数 {index_code} 失败: {e}")
            return None
    
    def _process_and_validate_data(self, df: pd.DataFrame, 
                                  symbol: str) -> Optional[pd.DataFrame]:
        """
        数据处理和验证 - 自报错、自纠正算法 (增强版)
        
        Args:
            df: 原始数据
            symbol: 股票代码
            
        Returns:
            处理后的数据
        """
        try:
            print(f"🔧 正在处理 {symbol} 数据...")
            
            # 1. 基本检查
            if df is None or df.empty:
                print(f"❌ {symbol} 数据为空")
                return None
            
            # 2. 检测市场类型进行特殊处理
            market_type = self._detect_market_from_symbol(symbol)
            
            # 3. 列名检查和修正
            df = self._fix_column_issues(df, symbol, market_type)
            
            # 4. 数据类型检查和修正
            df = self._fix_data_types(df, symbol, market_type)
            
            # 5. 数据完整性检查
            df = self._fix_data_integrity(df, symbol, market_type)
            
            # 6. 异常值检查和修正
            df = self._fix_outliers(df, symbol, market_type)
            
            # 7. 市场特定验证
            df = self._market_specific_validation(df, symbol, market_type)
            
            # 8. 最终验证
            if self._final_validation(df, symbol, market_type):
                print(f"✅ {symbol} 数据清理完成，有效数据 {len(df)} 条")
                return df
            else:
                print(f"❌ {symbol} 数据验证失败")
                return None
                
        except Exception as e:
            print(f"❌ {symbol} 数据处理出错: {e}")
            return None
    
    def _detect_market_from_symbol(self, symbol: str) -> str:
        """从符号中检测市场类型"""
        if 'A_STOCK' in symbol or symbol.isdigit():
            return 'A_STOCK'
        elif 'HK_STOCK' in symbol or 'HSI' in symbol:
            return 'HK_STOCK'
        elif 'US_STOCK' in symbol or symbol.startswith('^'):
            return 'US_STOCK'
        else:
            return 'UNKNOWN'
    
    def _fix_column_issues(self, df: pd.DataFrame, symbol: str, market_type: str) -> pd.DataFrame:
        """修正列名问题 (增强版)"""
        
        # 确保必要的列存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        # 扩展列名映射（处理不同市场的数据格式）
        column_mapping = {
            # 英文列名
            'Open': 'open', 'OPEN': 'open',
            'High': 'high', 'HIGH': 'high',
            'Low': 'low', 'LOW': 'low',
            'Close': 'close', 'CLOSE': 'close',
            'Volume': 'volume', 'VOLUME': 'volume',
            'Vol': 'volume', 'VOL': 'volume',
            
            # 中文列名
            '开盘': 'open', '最高': 'high', '最低': 'low',
            '收盘': 'close', '成交量': 'volume',
            
            # 港股特殊列名
            '开盘价': 'open', '最高价': 'high', '最低价': 'low',
            '收盘价': 'close', '成交额': 'volume',
            
            # 美股特殊列名
            'Adj Close': 'close', 'Adjusted Close': 'close',
            'Close Price': 'close', 'Last Price': 'close'
        }
        
        # 应用列名映射
        df = df.rename(columns=column_mapping)
        
        # 检查是否有缺失的必要列
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️ {symbol} 缺失列: {missing_cols}")
            
            # 尝试自动修复某些缺失列
            if 'volume' not in df.columns:
                # 如果没有成交量数据，设置为0（某些指数没有成交量）
                if market_type in ['HK_STOCK', 'US_STOCK'] and 'benchmark' in symbol.lower():
                    df['volume'] = 0
                    print(f"✅ {symbol} 自动添加成交量列（指数数据）")
        
        return df
    
    def _fix_data_types(self, df: pd.DataFrame, symbol: str, market_type: str) -> pd.DataFrame:
        """修正数据类型问题 (增强版)"""
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        
        for col in numeric_cols:
            if col in df.columns:
                # 转换为数值类型，错误的值设为NaN
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 检查转换结果
                nan_count = df[col].isna().sum()
                if nan_count > 0:
                    print(f"⚠️ {symbol} 列 {col} 转换产生 {nan_count} 个NaN值")
                
                # 对于某些市场的特殊处理
                if market_type == 'US_STOCK' and col in ['open', 'high', 'low', 'close']:
                    # 美股价格通常是美元，应该大于0
                    invalid_prices = (df[col] <= 0) & df[col].notna()
                    if invalid_prices.any():
                        print(f"⚠️ {symbol} 美股价格异常: {invalid_prices.sum()} 条")
        
        return df
    
    def _fix_data_integrity(self, df: pd.DataFrame, symbol: str, market_type: str) -> pd.DataFrame:
        """修正数据完整性问题 (增强版)"""
        
        # 删除重复数据
        before_count = len(df)
        df = df.drop_duplicates()
        after_count = len(df)
        
        if before_count != after_count:
            print(f"⚠️ {symbol} 删除重复数据 {before_count - after_count} 条")
        
        # 删除全为NaN的行
        df = df.dropna(how='all')
        
        # 处理价格逻辑错误（如high < low）
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # 修正 high < low 的情况
            mask = df['high'] < df['low']
            if mask.any():
                print(f"⚠️ {symbol} 修正价格逻辑错误 {mask.sum()} 条")
                df.loc[mask, ['high', 'low']] = df.loc[mask, ['low', 'high']].values
            
            # 确保价格合理性
            for col in ['open', 'high', 'low', 'close']:
                # 删除价格为0或负数的记录
                invalid_mask = (df[col] <= 0) | df[col].isna()
                if invalid_mask.any():
                    print(f"⚠️ {symbol} 删除无效{col}价格 {invalid_mask.sum()} 条")
                    df = df[~invalid_mask]
        
        # 确保成交量非负
        if 'volume' in df.columns:
            invalid_volume = (df['volume'] < 0) | df['volume'].isna()
            if invalid_volume.any():
                print(f"⚠️ {symbol} 修正无效成交量 {invalid_volume.sum()} 条")
                df.loc[invalid_volume, 'volume'] = 0
        
        return df
    
    def _fix_outliers(self, df: pd.DataFrame, symbol: str, market_type: str) -> pd.DataFrame:
        """修正异常值 (增强版)"""
        
        if 'close' in df.columns and len(df) > 1:
            # 计算价格变化率
            df['price_change'] = df['close'].pct_change()
            
            # 根据市场类型设置不同的异常阈值
            if market_type == 'A_STOCK':
                # A股涨跌停限制通常是10%，科创板和创业板是20%
                outlier_threshold = 0.25  # 设置25%作为异常阈值
            elif market_type == 'HK_STOCK':
                # 港股没有涨跌停限制，但设置更宽松的阈值
                outlier_threshold = 0.5   # 50%
            else:  # US_STOCK
                # 美股没有涨跌停限制，但单日50%变化仍然异常
                outlier_threshold = 0.5   # 50%
            
            # 识别异常变化
            outlier_mask = abs(df['price_change']) > outlier_threshold
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                print(f"⚠️ {symbol} {market_type} 发现异常价格变化 {outlier_count} 条 (>{outlier_threshold*100:.0f}%)")
                
                # 可以选择删除或修正，这里选择保留但标记
                df.loc[outlier_mask, 'outlier_flag'] = True
                
                # 如果异常值过多，可能是数据质量问题
                if outlier_count > len(df) * 0.1:  # 超过10%的数据异常
                    print(f"⚠️ {symbol} 异常数据比例过高 ({outlier_count/len(df)*100:.1f}%)，建议检查数据源")
            
            # 删除临时列
            df = df.drop('price_change', axis=1)
        
        return df
    
    def _market_specific_validation(self, df: pd.DataFrame, symbol: str, market_type: str) -> pd.DataFrame:
        """市场特定验证"""
        
        if market_type == 'HK_STOCK':
            # 港股特定验证
            if 'close' in df.columns:
                # 港股价格通常以港币计价，最小变动单位是0.001
                close_prices = df['close'].dropna()
                if len(close_prices) > 0:
                    min_price = close_prices.min()
                    max_price = close_prices.max()
                    
                    if min_price < 0.001:
                        print(f"⚠️ {symbol} 港股价格过低: 最低 {min_price:.6f} HKD")
                    
                    if max_price > 10000:
                        print(f"⚠️ {symbol} 港股价格过高: 最高 {max_price:.2f} HKD")
        
        elif market_type == 'US_STOCK':
            # 美股特定验证
            if 'close' in df.columns:
                # 美股价格通常以美元计价
                close_prices = df['close'].dropna()
                if len(close_prices) > 0:
                    min_price = close_prices.min()
                    max_price = close_prices.max()
                    
                    if min_price < 0.01:
                        print(f"⚠️ {symbol} 美股价格过低: 最低 ${min_price:.6f}")
                    
                    if max_price > 50000:
                        print(f"⚠️ {symbol} 美股价格过高: 最高 ${max_price:.2f}")
        
        return df
    
    def _final_validation(self, df: pd.DataFrame, symbol: str, market_type: str) -> bool:
        """最终数据验证 (增强版)"""
        
        # 根据市场类型设置不同的最小数据量要求
        min_records = {
            'A_STOCK': 10,
            'HK_STOCK': 5,    # 港股可能数据较少
            'US_STOCK': 5,    # 美股可能数据较少
            'UNKNOWN': 10
        }
        
        required_min = min_records.get(market_type, 10)
        
        # 检查数据量
        if len(df) < required_min:
            print(f"❌ {symbol} {market_type} 数据量过少: {len(df)} 条 (最少需要{required_min}条)")
            return False
        
        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ {symbol} 缺失必要列: {col}")
                return False
            
            # 检查是否有过多的NaN值
            nan_ratio = df[col].isna().sum() / len(df)
            max_nan_ratio = 0.2 if market_type in ['HK_STOCK', 'US_STOCK'] else 0.1
            
            if nan_ratio > max_nan_ratio:
                print(f"❌ {symbol} {market_type} 列 {col} NaN值过多: {nan_ratio:.2%} (最大允许{max_nan_ratio:.1%})")
                return False
        
        # 市场特定验证
        if market_type == 'HK_STOCK':
            # 港股数据可能有周末数据，但应该有工作日数据
            if len(df) > 0:
                weekdays = df.index.weekday
                trading_days = len(weekdays[weekdays < 5])  # 周一到周五
                if trading_days < len(df) * 0.5:
                    print(f"⚠️ {symbol} 港股交易日数据比例较低: {trading_days}/{len(df)}")
        
        return True
    
    def _convert_to_tushare_code(self, stock_code: str) -> str:
        """转换为Tushare代码格式"""
        if stock_code.startswith('0') or stock_code.startswith('3'):
            return f"{stock_code}.SZ"
        elif stock_code.startswith('6'):
            return f"{stock_code}.SH"
        else:
            return f"{stock_code}.SH"
    
    def _save_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """保存数据到本地"""
        try:
            filename = f"{symbol}_{timeframe}.csv"
            filepath = os.path.join(self.data_dir, filename)
            df.to_csv(filepath)
            print(f"✅ 数据已保存到: {filepath}")
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
    
    def load_saved_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """加载已保存的数据"""
        try:
            filename = f"{symbol}_{timeframe}.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
                print(f"✅ 加载本地数据: {filepath}")
                return df
            else:
                print(f"⚠️ 本地数据文件不存在: {filepath}")
                return None
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return None
    
    def get_stock_data_batch(self, stock_codes: List[str], start_date: str, 
                      end_date: str, timeframe: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        批量获取股票数据 (保留原有功能，支持多市场)
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            timeframe: 时间级别 1d/1w/1m
            
        Returns:
            股票数据字典 {股票代码: DataFrame}
        """
        stock_data = {}
        
        for stock_code in stock_codes:
            # 自动检测市场类型
            market = self.detect_market(stock_code)
            data = self.get_stock_data(stock_code, start_date, end_date, timeframe, market)
            if data is not None:
                stock_data[stock_code] = data
                
            # 如果是美股，添加延时避免API限制
            if market == 'US_STOCK':
                time.sleep(1)  # Alpha Vantage API限制
        
        return stock_data
    
    def get_popular_stocks(self, market: str = 'A_STOCK') -> List[Dict]:
        """
        获取热门股票列表
        
        Args:
            market: 市场类型 'A_STOCK', 'HK_STOCK', 'US_STOCK'
            
        Returns:
            热门股票列表
        """
        if market == 'A_STOCK':
            return [
                {'code': '000001', 'name': '平安银行', 'market': 'A_STOCK'},
                {'code': '000002', 'name': '万科A', 'market': 'A_STOCK'},
                {'code': '000858', 'name': '五粮液', 'market': 'A_STOCK'},
                {'code': '600036', 'name': '招商银行', 'market': 'A_STOCK'},
                {'code': '600519', 'name': '贵州茅台', 'market': 'A_STOCK'},
                {'code': '600887', 'name': '伊利股份', 'market': 'A_STOCK'},
            ]
        elif market == 'HK_STOCK':
            return [
                {'code': '00700', 'name': '腾讯控股', 'market': 'HK_STOCK'},
                {'code': '00941', 'name': '中国移动', 'market': 'HK_STOCK'},
                {'code': '00005', 'name': '汇丰控股', 'market': 'HK_STOCK'},
                {'code': '01299', 'name': '友邦保险', 'market': 'HK_STOCK'},
                {'code': '00388', 'name': '香港交易所', 'market': 'HK_STOCK'},
                {'code': '02318', 'name': '中国平安', 'market': 'HK_STOCK'},
            ]
        elif market == 'US_STOCK':
            return [
                {'code': 'AAPL', 'name': 'Apple Inc.', 'market': 'US_STOCK'},
                {'code': 'MSFT', 'name': 'Microsoft Corp.', 'market': 'US_STOCK'},
                {'code': 'GOOGL', 'name': 'Alphabet Inc.', 'market': 'US_STOCK'},
                {'code': 'AMZN', 'name': 'Amazon.com Inc.', 'market': 'US_STOCK'},
                {'code': 'TSLA', 'name': 'Tesla Inc.', 'market': 'US_STOCK'},
                {'code': 'NVDA', 'name': 'NVIDIA Corp.', 'market': 'US_STOCK'},
            ]
        else:
            return []

if __name__ == "__main__":
    # 测试代码
    db = DatabaseModule()
    
    # 测试数据获取
    stock_codes = ["000001", "000002"]
    start_date = "2024-01-01"
    end_date = "2024-06-01"
    
    stock_data = db.get_stock_data(stock_codes, start_date, end_date)
    benchmark_data = db.get_benchmark_data(start_date, end_date)
    
    print(f"✅ 测试完成，获取到 {len(stock_data)} 只股票数据") 
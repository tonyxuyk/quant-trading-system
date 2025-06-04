#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易算法后台 - 策略库模块
功能：RSI策略、双均线策略、价格行为策略 + 动态仓位控制
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PositionManager:
    """动态仓位控制与管理"""
    
    def __init__(self, initial_cash: float, max_drawdown: float = 0.1, 
                 max_position_ratio: float = 0.95):
        """
        初始化仓位管理器
        
        Args:
            initial_cash: 初始资金
            max_drawdown: 最大回撤限制
            max_position_ratio: 最大仓位比例
        """
        self.initial_cash = initial_cash
        self.max_drawdown = max_drawdown
        self.max_position_ratio = max_position_ratio
        
        # A股交易费用设置
        self.commission_rate = 0.0003  # 万三佣金
        self.stamp_tax = 0.001  # 千一印花税（仅卖出）
        self.transfer_fee = 0.00002  # 万分之二过户费
        self.min_commission = 5.0  # 最低佣金5元
        
        print("💰 仓位管理器初始化完成")
    
    def calculate_position_size(self, current_value: float, price: float, 
                              signal_strength: float = 1.0) -> float:
        """
        计算动态仓位大小
        
        Args:
            current_value: 当前账户价值
            price: 股票价格
            signal_strength: 信号强度 (0-1)
            
        Returns:
            可购买股数
        """
        # 基础仓位 = 当前价值 * 最大仓位比例 * 信号强度
        base_position = current_value * self.max_position_ratio * signal_strength
        
        # 考虑交易费用后的可用资金
        available_cash = base_position * (1 - self.commission_rate - self.transfer_fee)
        
        # 减去最低佣金
        available_cash -= self.min_commission
        
        # 计算可购买股数（A股最小100股）
        shares = int(available_cash / price / 100) * 100
        
        return max(0, shares)
    
    def calculate_trade_cost(self, shares: float, price: float, is_buy: bool) -> float:
        """
        计算交易费用
        
        Args:
            shares: 股数
            price: 价格
            is_buy: 是否为买入
            
        Returns:
            交易费用
        """
        trade_value = shares * price
        
        # 佣金（买卖都有）
        commission = max(trade_value * self.commission_rate, self.min_commission)
        
        # 过户费（买卖都有）
        transfer = trade_value * self.transfer_fee
        
        # 印花税（仅卖出）
        stamp = trade_value * self.stamp_tax if not is_buy else 0
        
        total_cost = commission + transfer + stamp
        
        return total_cost
    
    def check_risk_control(self, current_value: float) -> bool:
        """
        检查风险控制
        
        Args:
            current_value: 当前账户价值
            
        Returns:
            是否通过风险检查
        """
        # 计算当前回撤
        current_drawdown = (self.initial_cash - current_value) / self.initial_cash
        
        if current_drawdown > self.max_drawdown:
            print(f"⚠️ 回撤超限: {current_drawdown:.2%} > {self.max_drawdown:.2%}")
            return False
        
        return True

class RSIStrategy:
    """RSI相对强弱指数策略"""
    
    def __init__(self, period: int = 14, oversold: int = 30, 
                 overbought: int = 70, position_manager: PositionManager = None):
        """
        初始化RSI策略
        
        Args:
            period: RSI计算周期
            oversold: 超卖阈值
            overbought: 超买阈值
            position_manager: 仓位管理器
        """
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position_manager = position_manager
        
        print(f"📈 RSI策略初始化 - 周期:{period}, 超卖:{oversold}, 超买:{overbought}")
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            data: 包含OHLCV的数据
            
        Returns:
            包含信号的数据
        """
        df = data.copy()
        
        # 计算RSI
        df['RSI'] = self.calculate_rsi(df['close'])
        
        # 生成信号
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        # 买入信号：RSI < 超卖线
        oversold_mask = df['RSI'] < self.oversold
        df.loc[oversold_mask, 'signal'] = 1
        
        # 信号强度：越接近极值强度越高
        df.loc[oversold_mask, 'signal_strength'] = (self.oversold - df.loc[oversold_mask, 'RSI']) / self.oversold
        
        # 卖出信号：RSI > 超买线
        overbought_mask = df['RSI'] > self.overbought
        df.loc[overbought_mask, 'signal'] = -1
        df.loc[overbought_mask, 'signal_strength'] = (df.loc[overbought_mask, 'RSI'] - self.overbought) / (100 - self.overbought)
        
        # 确保信号强度在0-1之间
        df['signal_strength'] = df['signal_strength'].clip(0, 1)
        
        return df
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': 'RSI策略',
            'type': '反转策略',
            'period': self.period,
            'oversold': self.oversold,
            'overbought': self.overbought,
            'description': '基于RSI指标的超买超卖策略，适合震荡市场'
        }

class MovingAverageStrategy:
    """双均线策略"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30, 
                 ma_type: str = "SMA", position_manager: PositionManager = None):
        """
        初始化双均线策略
        
        Args:
            fast_period: 快线周期
            slow_period: 慢线周期
            ma_type: 均线类型 SMA/EMA/WMA
            position_manager: 仓位管理器
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type
        self.position_manager = position_manager
        
        print(f"📊 双均线策略初始化 - 快线:{fast_period}, 慢线:{slow_period}, 类型:{ma_type}")
    
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """计算移动平均线"""
        if self.ma_type == "SMA":
            return prices.rolling(window=period).mean()
        elif self.ma_type == "EMA":
            return prices.ewm(span=period).mean()
        elif self.ma_type == "WMA":
            weights = np.arange(1, period + 1)
            return prices.rolling(window=period).apply(
                lambda x: np.dot(x, weights) / weights.sum(), raw=True
            )
        else:
            return prices.rolling(window=period).mean()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = data.copy()
        
        # 计算双均线
        df['MA_fast'] = self.calculate_ma(df['close'], self.fast_period)
        df['MA_slow'] = self.calculate_ma(df['close'], self.slow_period)
        
        # 计算均线差值比例
        df['MA_diff_ratio'] = (df['MA_fast'] - df['MA_slow']) / df['MA_slow']
        
        # 生成基础信号
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        # 金叉：快线上穿慢线
        golden_cross = (df['MA_fast'] > df['MA_slow']) & (df['MA_fast'].shift(1) <= df['MA_slow'].shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 死叉：快线下穿慢线
        death_cross = (df['MA_fast'] < df['MA_slow']) & (df['MA_fast'].shift(1) >= df['MA_slow'].shift(1))
        df.loc[death_cross, 'signal'] = -1
        
        # 信号强度：基于均线差值和成交量
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # 买入信号强度
        buy_mask = df['signal'] == 1
        df.loc[buy_mask, 'signal_strength'] = (
            df.loc[buy_mask, 'MA_diff_ratio'].abs() * 0.7 + 
            df.loc[buy_mask, 'volume_ratio'].clip(0, 2) * 0.3
        ).clip(0, 1)
        
        # 卖出信号强度
        sell_mask = df['signal'] == -1
        df.loc[sell_mask, 'signal_strength'] = (
            df.loc[sell_mask, 'MA_diff_ratio'].abs() * 0.7 + 
            df.loc[sell_mask, 'volume_ratio'].clip(0, 2) * 0.3
        ).clip(0, 1)
        
        return df
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': '双均线策略',
            'type': '趋势跟踪策略',
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'ma_type': self.ma_type,
            'description': '基于快慢均线交叉的趋势跟踪策略，适合趋势明显的市场'
        }

class PriceActionStrategy:
    """价格行为学策略"""
    
    def __init__(self, lookback_period: int = 20, breakout_threshold: float = 0.02,
                 pullback_threshold: float = 0.05, position_manager: PositionManager = None):
        """
        初始化价格行为策略
        
        Args:
            lookback_period: 观察周期
            breakout_threshold: 突破阈值
            pullback_threshold: 回撤阈值
            position_manager: 仓位管理器
        """
        self.lookback_period = lookback_period
        self.breakout_threshold = breakout_threshold
        self.pullback_threshold = pullback_threshold
        self.position_manager = position_manager
        
        print(f"📈 价格行为策略初始化 - 观察周期:{lookback_period}, 突破阈值:{breakout_threshold:.2%}")
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """计算支撑位和阻力位"""
        # 计算滚动最高价和最低价
        resistance = data['high'].rolling(window=self.lookback_period).max()
        support = data['low'].rolling(window=self.lookback_period).min()
        
        return support, resistance
    
    def detect_patterns(self, data: pd.DataFrame) -> pd.DataFrame:
        """检测价格形态"""
        df = data.copy()
        
        # 计算价格变化率
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        
        # 计算布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        df['BB_std'] = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + 2 * df['BB_std']
        df['BB_lower'] = df['BB_middle'] - 2 * df['BB_std']
        
        # 计算相对位置
        df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        df = self.detect_patterns(data)
        
        # 计算支撑阻力位
        support, resistance = self.calculate_support_resistance(df)
        df['support'] = support
        df['resistance'] = resistance
        
        # 初始化信号
        df['signal'] = 0
        df['signal_strength'] = 0.0
        
        # 突破策略信号
        self._generate_breakout_signals(df)
        
        # 反转策略信号
        self._generate_reversal_signals(df)
        
        # 形态识别信号
        self._generate_pattern_signals(df)
        
        return df
    
    def _generate_breakout_signals(self, df: pd.DataFrame):
        """生成突破信号"""
        # 向上突破阻力位
        upward_breakout = (
            (df['close'] > df['resistance']) & 
            (df['close'].shift(1) <= df['resistance'].shift(1)) &
            (df['volume'] > df['volume'].rolling(20).mean() * 1.5)  # 放量突破
        )
        
        # 向下跌破支撑位
        downward_breakout = (
            (df['close'] < df['support']) & 
            (df['close'].shift(1) >= df['support'].shift(1)) &
            (df['volume'] > df['volume'].rolling(20).mean() * 1.5)  # 放量跌破
        )
        
        # 设置信号
        df.loc[upward_breakout, 'signal'] = 1
        df.loc[downward_breakout, 'signal'] = -1
        
        # 突破信号强度
        df.loc[upward_breakout, 'signal_strength'] = (
            (df.loc[upward_breakout, 'close'] - df.loc[upward_breakout, 'resistance']) / 
            df.loc[upward_breakout, 'resistance'] / self.breakout_threshold
        ).clip(0, 1)
        
        df.loc[downward_breakout, 'signal_strength'] = (
            (df.loc[downward_breakout, 'support'] - df.loc[downward_breakout, 'close']) / 
            df.loc[downward_breakout, 'support'] / self.breakout_threshold
        ).clip(0, 1)
    
    def _generate_reversal_signals(self, df: pd.DataFrame):
        """生成反转信号"""
        # 在支撑位附近的反弹信号
        support_bounce = (
            (df['close'] <= df['support'] * 1.02) &  # 接近支撑位
            (df['close'] > df['close'].shift(1)) &   # 价格反弹
            (df['BB_position'] < 0.2)                # 在布林带下轨附近
        )
        
        # 在阻力位附近的回落信号
        resistance_rejection = (
            (df['close'] >= df['resistance'] * 0.98) &  # 接近阻力位
            (df['close'] < df['close'].shift(1)) &      # 价格回落
            (df['BB_position'] > 0.8)                   # 在布林带上轨附近
        )
        
        # 如果没有突破信号，则考虑反转信号
        no_signal_mask = df['signal'] == 0
        
        df.loc[support_bounce & no_signal_mask, 'signal'] = 1
        df.loc[resistance_rejection & no_signal_mask, 'signal'] = -1
        
        # 反转信号强度（通常较弱）
        df.loc[support_bounce & no_signal_mask, 'signal_strength'] = 0.5
        df.loc[resistance_rejection & no_signal_mask, 'signal_strength'] = 0.5
    
    def _generate_pattern_signals(self, df: pd.DataFrame):
        """生成形态信号"""
        # 锤子线形态（看涨）
        hammer_pattern = (
            (df['close'] > df['open']) &  # 阳线
            ((df['low'] - df[['open', 'close']].min(axis=1)) >= 
             2 * (df[['open', 'close']].max(axis=1) - df[['open', 'close']].min(axis=1))) &  # 长下影线
            (df['BB_position'] < 0.3)  # 在相对低位
        )
        
        # 射击之星形态（看跌）
        shooting_star = (
            (df['close'] < df['open']) &  # 阴线
            ((df['high'] - df[['open', 'close']].max(axis=1)) >= 
             2 * (df[['open', 'close']].max(axis=1) - df[['open', 'close']].min(axis=1))) &  # 长上影线
            (df['BB_position'] > 0.7)  # 在相对高位
        )
        
        # 如果没有其他信号，考虑形态信号
        no_signal_mask = df['signal'] == 0
        
        df.loc[hammer_pattern & no_signal_mask, 'signal'] = 1
        df.loc[shooting_star & no_signal_mask, 'signal'] = -1
        
        # 形态信号强度
        df.loc[hammer_pattern & no_signal_mask, 'signal_strength'] = 0.6
        df.loc[shooting_star & no_signal_mask, 'signal_strength'] = 0.6
    
    def get_strategy_info(self) -> Dict:
        """获取策略信息"""
        return {
            'name': '价格行为策略',
            'type': '综合策略',
            'lookback_period': self.lookback_period,
            'breakout_threshold': f"{self.breakout_threshold:.2%}",
            'pullback_threshold': f"{self.pullback_threshold:.2%}",
            'description': '基于支撑阻力、突破和K线形态的综合策略'
        }

class StrategyModule:
    """策略库模块 - 统一管理所有策略"""
    
    def __init__(self, strategy_config: Dict):
        """
        初始化策略模块
        
        Args:
            strategy_config: 策略配置参数
        """
        self.config = strategy_config
        
        # 初始化仓位管理器
        self.position_manager = PositionManager(
            initial_cash=strategy_config.get('initial_cash', 1000000),
            max_drawdown=strategy_config.get('max_drawdown', 0.1),
            max_position_ratio=strategy_config.get('position_size', 0.95)
        )
        
        # 初始化策略
        self.strategy = self._create_strategy(strategy_config)
        
        print("⚙️ 策略库模块初始化完成")
    
    def _create_strategy(self, config: Dict):
        """根据配置创建策略"""
        strategy_name = config.get('strategy_name', '双均线策略')
        
        if strategy_name == 'RSI策略':
            return RSIStrategy(
                period=config.get('rsi_period', 14),
                oversold=config.get('rsi_oversold', 30),
                overbought=config.get('rsi_overbought', 70),
                position_manager=self.position_manager
            )
        elif strategy_name == '双均线策略':
            return MovingAverageStrategy(
                fast_period=config.get('fast_period', 10),
                slow_period=config.get('slow_period', 30),
                ma_type=config.get('ma_type', 'SMA'),
                position_manager=self.position_manager
            )
        elif strategy_name == '价格行为策略':
            return PriceActionStrategy(
                lookback_period=config.get('lookback_period', 20),
                breakout_threshold=config.get('breakout_threshold', 0.02),
                pullback_threshold=config.get('pullback_threshold', 0.05),
                position_manager=self.position_manager
            )
        else:
            # 默认双均线策略
            return MovingAverageStrategy(position_manager=self.position_manager)
    
    def generate_trading_signals(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        为所有股票生成交易信号 (增强版 - 支持多市场)
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            包含信号的数据字典
        """
        signals_data = {}
        
        if not stock_data:
            print("❌ 股票数据为空，无法生成信号")
            return {}
        
        for symbol, data in stock_data.items():
            print(f"🔄 为 {symbol} 生成交易信号...")
            
            try:
                # 数据验证
                if not self._validate_stock_data(data, symbol):
                    print(f"❌ {symbol} 数据验证失败，跳过信号生成")
                    continue
                
                # 预处理数据
                processed_data = self._preprocess_data(data, symbol)
                if processed_data is None:
                    print(f"❌ {symbol} 数据预处理失败，跳过信号生成")
                    continue
                
                # 生成信号
                signals = self.strategy.generate_signals(processed_data)
                
                if signals is not None and not signals.empty:
                    # 后处理信号
                    final_signals = self._postprocess_signals(signals, symbol)
                    if final_signals is not None:
                        signals_data[symbol] = final_signals
                        print(f"✅ {symbol} 信号生成完成")
                    else:
                        print(f"❌ {symbol} 信号后处理失败")
                else:
                    print(f"❌ {symbol} 策略未生成有效信号")
                
            except Exception as e:
                print(f"❌ {symbol} 信号生成失败: {e}")
                # 添加详细错误信息
                import traceback
                print(f"详细错误: {traceback.format_exc()}")
                continue
        
        print(f"🎯 信号生成完成，成功处理 {len(signals_data)}/{len(stock_data)} 只股票")
        return signals_data
    
    def _validate_stock_data(self, data: pd.DataFrame, symbol: str) -> bool:
        """验证股票数据有效性"""
        
        if data is None:
            print(f"❌ {symbol} 数据为None")
            return False
        
        if data.empty:
            print(f"❌ {symbol} 数据为空")
            return False
        
        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            print(f"❌ {symbol} 缺失必要列: {missing_cols}")
            return False
        
        # 检查数据长度
        if len(data) < 20:  # 策略通常需要至少20个数据点
            print(f"❌ {symbol} 数据量过少: {len(data)} 条")
            return False
        
        # 检查价格数据有效性
        for col in required_cols:
            if data[col].isna().all():
                print(f"❌ {symbol} 列 {col} 全为NaN")
                return False
            
            if (data[col] <= 0).any():
                print(f"⚠️ {symbol} 列 {col} 存在非正值，将在预处理中清理")
        
        # 检查成交量
        if 'volume' in data.columns:
            if data['volume'].isna().all():
                print(f"⚠️ {symbol} 成交量全为NaN，将使用默认值")
        else:
            print(f"⚠️ {symbol} 缺失成交量数据，将添加默认值")
        
        return True
    
    def _preprocess_data(self, data: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """预处理数据"""
        
        try:
            df = data.copy()
            
            # 确保日期索引
            if not isinstance(df.index, pd.DatetimeIndex):
                print(f"⚠️ {symbol} 转换日期索引")
                df.index = pd.to_datetime(df.index)
            
            # 排序数据
            df = df.sort_index()
            
            # 处理缺失的成交量
            if 'volume' not in df.columns:
                df['volume'] = 0
                print(f"✅ {symbol} 添加默认成交量")
            elif df['volume'].isna().all():
                df['volume'] = 0
                print(f"✅ {symbol} 修复成交量NaN值")
            
            # 清理价格数据
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                # 移除非正值
                invalid_mask = (df[col] <= 0) | df[col].isna()
                if invalid_mask.any():
                    print(f"⚠️ {symbol} 清理 {col} 无效值: {invalid_mask.sum()} 条")
                    
                    # 使用前一个有效值填充
                    df[col] = df[col].mask(invalid_mask).fillna(method='ffill')
                    
                    # 如果开头有NaN，使用后一个值填充
                    df[col] = df[col].fillna(method='bfill')
            
            # 最终检查
            if df[price_cols].isna().any().any():
                print(f"❌ {symbol} 预处理后仍有NaN值")
                return None
            
            if len(df) < 10:
                print(f"❌ {symbol} 预处理后数据不足")
                return None
            
            # 检测市场类型并进行特殊处理
            self._market_specific_preprocessing(df, symbol)
            
            return df
            
        except Exception as e:
            print(f"❌ {symbol} 数据预处理失败: {e}")
            return None
    
    def _market_specific_preprocessing(self, df: pd.DataFrame, symbol: str):
        """市场特定预处理"""
        
        # 检测市场类型
        if any(market in symbol for market in ['HK_STOCK', 'HSI', 'HSTECH']):
            # 港股特殊处理
            print(f"🇭🇰 {symbol} 港股数据预处理")
            
            # 港股可能有特殊的价格格式
            if df['close'].max() > 1000:
                print(f"⚠️ {symbol} 港股价格偏高，检查数据单位")
            
        elif any(market in symbol for market in ['US_STOCK', '^']):
            # 美股特殊处理
            print(f"🇺🇸 {symbol} 美股数据预处理")
            
            # 美股价格通常较低
            if df['close'].max() > 10000:
                print(f"⚠️ {symbol} 美股价格异常，检查数据格式")
        
        else:
            # A股处理
            print(f"🇨🇳 {symbol} A股数据预处理")
    
    def _postprocess_signals(self, signals: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """后处理信号"""
        
        try:
            df = signals.copy()
            
            # 验证信号列
            required_signal_cols = ['signal', 'signal_strength']
            for col in required_signal_cols:
                if col not in df.columns:
                    print(f"❌ {symbol} 缺失信号列: {col}")
                    return None
            
            # 清理信号数据
            df['signal'] = df['signal'].fillna(0)
            df['signal_strength'] = df['signal_strength'].fillna(0)
            
            # 限制信号值范围
            df['signal'] = df['signal'].clip(-1, 1)
            df['signal_strength'] = df['signal_strength'].clip(0, 1)
            
            # 统计信号
            buy_signals = (df['signal'] == 1).sum()
            sell_signals = (df['signal'] == -1).sum()
            
            if buy_signals == 0 and sell_signals == 0:
                print(f"⚠️ {symbol} 未生成任何交易信号")
            else:
                print(f"📊 {symbol} 信号统计: 买入 {buy_signals} 次, 卖出 {sell_signals} 次")
            
            return df
            
        except Exception as e:
            print(f"❌ {symbol} 信号后处理失败: {e}")
            return None
    
    def get_strategy_summary(self) -> Dict:
        """获取策略摘要信息"""
        summary = {
            'strategy_info': self.strategy.get_strategy_info(),
            'position_config': {
                'initial_cash': self.position_manager.initial_cash,
                'max_drawdown': f"{self.position_manager.max_drawdown:.2%}",
                'max_position_ratio': f"{self.position_manager.max_position_ratio:.2%}",
                'commission_rate': f"{self.position_manager.commission_rate:.4%}",
                'stamp_tax': f"{self.position_manager.stamp_tax:.3%}",
                'transfer_fee': f"{self.position_manager.transfer_fee:.5%}",
                'min_commission': f"{self.position_manager.min_commission:.2f}元"
            },
            'trade_costs': self._get_cost_example()
        }
        
        return summary
    
    def _get_cost_example(self) -> Dict:
        """获取交易费用示例"""
        # 以10万元交易为例
        example_value = 100000
        example_price = 20
        example_shares = example_value / example_price
        
        buy_cost = self.position_manager.calculate_trade_cost(example_shares, example_price, True)
        sell_cost = self.position_manager.calculate_trade_cost(example_shares, example_price, False)
        
        return {
            'example_trade_value': f"{example_value:,.0f}元",
            'buy_cost': f"{buy_cost:.2f}元 ({buy_cost/example_value:.4%})",
            'sell_cost': f"{sell_cost:.2f}元 ({sell_cost/example_value:.4%})",
            'total_cost': f"{buy_cost + sell_cost:.2f}元 ({(buy_cost + sell_cost)/example_value:.4%})"
        }

if __name__ == "__main__":
    # 测试代码
    config = {
        'strategy_name': '双均线策略',
        'fast_period': 10,
        'slow_period': 30,
        'initial_cash': 1000000,
        'max_drawdown': 0.1,
        'position_size': 0.95
    }
    
    strategy_module = StrategyModule(config)
    summary = strategy_module.get_strategy_summary()
    
    print("📊 策略摘要:")
    for key, value in summary.items():
        print(f"{key}: {value}") 
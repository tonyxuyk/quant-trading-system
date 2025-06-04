#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易算法后台包
整合数据库、策略库、回测库三大模块
"""

from .database_module import DatabaseModule
from .strategy_module import StrategyModule, PositionManager, RSIStrategy, MovingAverageStrategy, PriceActionStrategy
from .backtest_module import BacktestModule, BacktestEngine

__version__ = "1.0.0"
__author__ = "Tony量化团队"

__all__ = [
    'DatabaseModule',
    'StrategyModule', 
    'BacktestModule',
    'PositionManager',
    'RSIStrategy',
    'MovingAverageStrategy', 
    'PriceActionStrategy',
    'BacktestEngine'
]

print("�� 量化交易算法后台模块加载完成") 
"""
首页模块
欢迎页面和库导入检测
"""

import streamlit as st
import time
import sys
import traceback

def show():
    """显示首页"""
    # 页面标题
    st.markdown("# 🚀 欢迎来到Tony的量化策略小助手")
    st.markdown("### 专业的A股量化交易回测系统")
    
    # 分割线
    st.markdown("---")
    
    # 系统介绍
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 📊 系统功能
        
        ### 🎯 核心特性
        - **智能选股**: 支持股票代码、中文名称、拼音输入
        - **多时间框架**: 1分钟到1月的K线数据
        - **策略丰富**: 双均线、RSI、价格行为学策略
        - **专业回测**: 考虑A股交易费用的真实回测
        
        ### 📈 数据源
        - **主要数据源**: AKShare (优先)
        - **备用数据源**: Tushare
        - **基准指数**: 沪深300、上证指数
        
        ### 🔧 风险管理
        - **动态仓位控制**
        - **最大回撤限制**
        - **交易费用计算**
        - **资金管理**
        """)
    
    with col2:
        st.markdown("""
        ## 🎮 使用流程
        
        ### 1️⃣ 库导入
        点击开始按钮导入必要库
        
        ### 2️⃣ 选择股票
        输入股票代码或名称
        
        ### 3️⃣ 配置策略
        选择交易策略和参数
        
        ### 4️⃣ 查看结果
        分析回测报告和图表
        """)
    
    st.markdown("---")
    
    # 库导入状态
    if not st.session_state.get('libraries_loaded', False):
        st.markdown("## 📦 系统初始化")
        st.info("请点击下方按钮开始导入必要的库文件")
        
        # 开始按钮
        if st.button("🚀 开始导入库", type="primary", use_container_width=True):
            import_libraries()
    else:
        # 已导入状态
        st.success("✅ 系统库已成功导入，可以进入选股页面！")
        
        # 显示已导入的库
        with st.expander("📋 查看已导入的库"):
            imported_libraries = [
                "pandas - 数据处理",
                "numpy - 数值计算", 
                "streamlit - Web界面",
                "akshare - A股数据获取",
                "tushare - 备用数据源",
                "backtrader - 回测框架",
                "matplotlib - 图表绘制",
                "plotly - 交互式图表"
            ]
            
            for lib in imported_libraries:
                st.markdown(f"✅ {lib}")
        
        # 进入下一步
        st.markdown("### 🎯 下一步")
        st.info("请在侧边栏点击 '📈 选股页' 开始选择要回测的股票")

def import_libraries():
    """导入库函数"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    libraries = [
        ("pandas", "import pandas as pd"),
        ("numpy", "import numpy as np"), 
        ("akshare", "import akshare as ak"),
        ("tushare", "import tushare as ts"),
        ("backtrader", "import backtrader as bt"),
        ("matplotlib", "import matplotlib.pyplot as plt"),
        ("plotly", "import plotly.graph_objects as go"),
        ("streamlit", "import streamlit as st")
    ]
    
    success_count = 0
    total_count = len(libraries)
    
    for i, (lib_name, import_cmd) in enumerate(libraries):
        try:
            status_text.text(f"正在导入 {lib_name}...")
            time.sleep(0.5)  # 模拟导入时间
            
            # 尝试导入
            exec(import_cmd)
            success_count += 1
            status_text.text(f"✅ {lib_name} 导入成功")
            
        except ImportError as e:
            status_text.text(f"❌ {lib_name} 导入失败: {str(e)}")
            time.sleep(1)
        except Exception as e:
            status_text.text(f"❌ {lib_name} 导入时发生错误: {str(e)}")
            time.sleep(1)
        
        # 更新进度条
        progress = (i + 1) / total_count
        progress_bar.progress(progress)
        time.sleep(0.3)
    
    # 导入完成
    if success_count == total_count:
        status_text.text("🎉 所有库导入成功！")
        st.session_state.libraries_loaded = True
        st.success("✅ 库导入完成！系统已准备就绪。")
        st.balloons()  # 庆祝动画
        time.sleep(2)
        st.rerun()  # 刷新页面
    else:
        failed_count = total_count - success_count
        status_text.text(f"⚠️ 导入完成，{failed_count} 个库导入失败")
        st.error(f"❌ 有 {failed_count} 个库导入失败，请检查环境配置")
        
        # 显示修复建议
        st.markdown("### 🔧 修复建议")
        st.code("""
        # 请在终端运行以下命令修复：
        pip install akshare tushare backtrader matplotlib plotly pandas numpy
        """)

# 添加页面底部信息
def show_footer():
    """显示页面底部信息"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        💡 Tony的量化策略小助手 v1.0 | 基于Streamlit构建
    </div>
    """, unsafe_allow_html=True) 
"""
Tony的量化策略小助手
主应用入口文件
"""

import streamlit as st
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from streamlit_option_menu import option_menu
from pages import home, stock_selection, strategy_selection, backtest_report

# 页面配置
st.set_page_config(
    page_title="Tony的量化策略小助手",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
def init_session_state():
    """初始化会话状态"""
    default_states = {
        'libraries_loaded': False,
        'data_loaded': False,
        'strategy_configured': False,
        'backtest_completed': False,
        'current_page': '🏠 首页',
        'stock_data': None,
        'strategy_params': None,
        'backtest_results': None,
        'selected_stocks': [],
        'selected_period': None,
        'selected_timeframe': '1日',
        'initial_cash': 1000000,
        'max_drawdown': 10,
        'selected_strategy': '双均线策略'
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# 侧边栏导航
def main():
    """主函数"""
    # 侧边栏标题
    st.sidebar.title("🚀 Tony的量化策略小助手")
    st.sidebar.markdown("---")
    
    # 页面选择菜单
    pages = ["🏠 首页", "📈 选股页", "⚙️ 策略选择", "📊 回测报告"]
    
    # 根据当前步骤显示可用页面
    available_pages = ["🏠 首页"]
    if st.session_state.get('libraries_loaded', False):
        available_pages.append("📈 选股页")
    if st.session_state.get('data_loaded', False):
        available_pages.append("⚙️ 策略选择")
    if st.session_state.get('backtest_completed', False):
        available_pages.append("📊 回测报告")
    
    # 选择页面
    selected_page = option_menu(
        menu_title=None,
        options=available_pages,
        icons=['house', 'graph-up', 'gear', 'clipboard-data'],
        menu_icon="cast",
        default_index=available_pages.index(st.session_state.current_page) if st.session_state.current_page in available_pages else 0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )
    
    st.session_state.current_page = selected_page
    
    # 状态显示
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 当前状态")
    
    # 状态指示器
    status_items = [
        ("库导入", st.session_state.get('libraries_loaded', False)),
        ("数据获取", st.session_state.get('data_loaded', False)),
        ("策略配置", st.session_state.get('strategy_configured', False)),
        ("回测完成", st.session_state.get('backtest_completed', False))
    ]
    
    for item, status in status_items:
        icon = "✅" if status else "⏳"
        status_text = "完成" if status else "待完成"
        st.sidebar.markdown(f"{icon} {item}: {status_text}")
    
    # 显示当前页面
    if selected_page == "🏠 首页":
        home.show()
    elif selected_page == "📈 选股页":
        stock_selection.show()
    elif selected_page == "⚙️ 策略选择":
        strategy_selection.show()
    elif selected_page == "📊 回测报告":
        backtest_report.show()

if __name__ == "__main__":
    main() 
# 🚀 Tony的量化策略小助手 - GitHub部署版

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## 📊 项目简介

这是一个专业的A股量化交易系统，集成了数据获取、策略开发、回测分析和风险控制功能。

### ✨ 核心功能

- **📈 股票选择** - 智能股票筛选和数据获取
- **⚙️ 策略配置** - RSI、双均线、价格行为等多种策略
- **📊 回测分析** - 完整的性能分析和风险评估
- **💰 费用计算** - 精确的A股交易费用模拟
- **📱 响应式界面** - 现代化的Web界面设计

## 🌐 在线体验

### 部署地址
- **主站**: [https://your-app-url.streamlit.app](https://your-app-url.streamlit.app)
- **备用**: [https://your-backup-url.streamlit.app](https://your-backup-url.streamlit.app)

### 快速开始
1. 点击上方链接访问应用
2. 在"📈 选股页"选择要分析的股票
3. 在"⚙️ 策略选择"配置交易策略
4. 在"📊 回测报告"查看分析结果

## 🛠️ 本地部署

### 环境要求
- Python 3.8+
- 2GB+ 内存
- 稳定的网络连接

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/quant-trading-system.git
cd quant-trading-system
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements_deploy.txt
```

4. **启动应用**
```bash
streamlit run app.py
```

5. **访问应用**
打开浏览器访问: http://localhost:8501

## 📋 功能模块

### 🏠 首页
- 系统介绍和库导入
- 功能概览
- 快速开始指南

### 📈 选股页面
- **数据源**: AKShare + Tushare双重保障
- **股票筛选**: 支持代码/名称搜索
- **数据获取**: 自动获取历史价格数据
- **数据验证**: 完整性检查和异常处理

### ⚙️ 策略配置
- **RSI策略**: 相对强弱指数反转策略
- **双均线策略**: 金叉死叉趋势跟踪
- **价格行为策略**: 支撑阻力突破分析
- **仓位管理**: 动态风险控制

### 📊 回测报告
- **性能指标**: 收益率、夏普比率、最大回撤
- **交易分析**: 胜率、盈亏比、交易次数
- **可视化图表**: 净值曲线、回撤分析
- **基准比较**: 与沪深300指数对比

## 🎯 技术栈

### 前端框架
- **Streamlit** - Web应用框架
- **Plotly** - 交互式图表
- **Streamlit-option-menu** - 导航菜单

### 数据处理
- **Pandas** - 数据分析
- **NumPy** - 数值计算
- **AKShare** - 免费数据源
- **Tushare** - 专业数据源

### 量化分析
- **Backtrader** - 回测框架
- **PyPinyin** - 中文处理
- **Matplotlib/Seaborn** - 数据可视化

## 📈 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Web界面                      │
├─────────────────────────────────────────────────────────┤
│  📈 选股页面  │  ⚙️ 策略配置  │  📊 回测报告  │  🏠 首页  │
├─────────────────────────────────────────────────────────┤
│                     后台处理模块                         │
│  📊 数据模块  │  ⚡ 策略模块  │  🧪 回测模块  │  🎛️ 控制器 │
├─────────────────────────────────────────────────────────┤
│                     数据源                               │
│       AKShare API        │        Tushare API           │
└─────────────────────────────────────────────────────────┘
```

## 🔧 配置说明

### 数据源配置
系统默认使用AKShare作为主要数据源，Tushare作为备用数据源。

### 策略参数
- **RSI周期**: 14天（可调整）
- **均线参数**: 快线10天，慢线30天
- **交易费用**: 万三佣金 + 千一印花税

### 风险控制
- **最大回撤**: 10%
- **最大仓位**: 95%
- **止损机制**: 动态调整

## 📱 界面预览

### 桌面端
![Desktop Preview](screenshots/desktop.png)

### 移动端
![Mobile Preview](screenshots/mobile.png)

## 🎓 使用教程

### 新手指南
1. **选择股票**: 在选股页面输入股票代码或名称
2. **配置策略**: 选择适合的交易策略和参数
3. **查看结果**: 在回测报告页面分析策略表现
4. **优化调整**: 根据结果调整策略参数

### 高级功能
- **多股票组合**: 同时分析多只股票
- **策略对比**: 比较不同策略的表现
- **风险分析**: 详细的风险指标分析
- **数据导出**: 导出分析结果

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork本仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 代码规范
- 遵循PEP 8代码风格
- 添加必要的注释和文档
- 确保代码测试通过

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 优秀的金融数据接口
- [Streamlit](https://streamlit.io/) - 强大的Web应用框架
- [Backtrader](https://www.backtrader.com/) - 专业的回测框架

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/yourusername/quant-trading-system)
- **问题反馈**: [Issues](https://github.com/yourusername/quant-trading-system/issues)
- **功能建议**: [Discussions](https://github.com/yourusername/quant-trading-system/discussions)

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！ 
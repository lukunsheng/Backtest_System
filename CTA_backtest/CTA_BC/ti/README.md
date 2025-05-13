# 技术指标策略框架

这个框架提供了一种声明式API，用于定义技术指标交易策略并生成交易信号，可与CTA_backtest系统无缝集成。

## 主要特点

- **声明式API**：使用链式调用定义交易条件
- **丰富的技术指标**：内置支持常用技术指标(MACD, RSI, 布林带等)
- **数据管理**：使用SQLAlchemy连接数据库，自动管理数据获取和缓存
- **信号生成**：自动根据条件生成符合回测系统要求格式的信号
- **与CTA_backtest系统兼容**：生成的信号可直接用于回测

## 基础用法

```python
from CTA_backtest.CTA_BC.ti import when, price, macd_line, macd_signal, generate_signals

# 定义MACD金叉买入条件
buy_condition = when(macd_line()).has_crossed_above(macd_signal())

# 定义MACD死叉卖出条件
sell_condition = when(macd_line()).has_crossed_below(macd_signal())

# 生成交易信号
signals = generate_signals(
    buy_condition=buy_condition,
    sell_condition=sell_condition,
    products=['rb', 'ru'],
    start_date='2022-01-01',
    end_date='2022-12-31'
)
```

## 模块结构

该框架包含四个主要模块：

1. **indicators.py**：提供技术指标计算功能
2. **conditions.py**：定义声明式条件API
3. **datamanager.py**：管理数据库连接和数据获取
4. **signals.py**：生成交易信号

## 高级用法

```python
from CTA_backtest.CTA_BC.ti import when, price, and_, or_, rsi, sma, generate_signals

# 组合条件：RSI超卖 AND 价格站上均线
buy_condition = and_(
    when(rsi()).is_below(30),
    when(price()).is_above(sma(20))
)

# 组合条件：RSI超买 OR 价格跌破均线
sell_condition = or_(
    when(rsi()).is_above(70),
    when(price()).is_below(sma(10))
)

signals = generate_signals(
    buy_condition=buy_condition,
    sell_condition=sell_condition,
    products=['ag', 'al'],
    start_date='2022-01-01',
    end_date='2022-12-31'
)
```

## 与回测系统集成

```python
from CTA_backtest.backtest import BackTest
from CTA_backtest.CTA_BC.ti import generate_signals, when, macd_line, macd_signal
from CTA_backtest.CTA_BC.ti import DataManager

# 获取信号
signals = generate_signals(
    buy_condition=when(macd_line()).has_crossed_above(macd_signal()),
    sell_condition=when(macd_line()).has_crossed_below(macd_signal()),
    products=['rb', 'ru'],
    start_date='2022-01-01',
    end_date='2022-12-31'
)

# 创建回测实例
bt = BackTest()

# 获取价格数据
dm = DataManager()
df_y = dm.get_close(['rb', 'ru'], '2022-01-01', '2022-12-31')

# 执行回测
bt.fit(
    df_x=signals,
    product_list=['rb', 'ru'],
    name="MACD_Strategy", 
    begin_date='2022-01-01',
    end_date='2022-12-31'
)

# 生成回测报告
bt.report(df_y=df_y)
```

## 注意事项

1. 信号输出格式为DataFrame，列名格式为`{product}_flag`，与backtest.py的要求匹配
2. 使用SQLAlchemy连接MySQL数据库，避免了pymysql的兼容性问题
3. 数据管理器支持异常处理，如果查询失败会返回空DataFrame而不是抛出异常
4. 所有模块都设计为可单独使用，也可以组合使用 
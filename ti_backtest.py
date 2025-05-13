import pandas as pd
from datetime import datetime
from CTA_backtest.CTA_BC.ti.indicators import RSI, MACD, BOLL, sma, ema, macd_line, macd_signal
from CTA_backtest.CTA_BC.ti.conditions import when, price, and_, or_, not_
from CTA_backtest.CTA_BC.ti.signals import generate_signals
from CTA_backtest.CTA_BC.ti.datamanager import DataManager

# 示例1: 简单的MACD金叉策略
def macd_cross_strategy():
    # 创建买入条件: MACD线从下向上穿越信号线
    buy_condition = when(macd_line(120,260,90)).has_crossed_above(macd_signal(120,260,90))
    
    # 创建卖出条件: MACD线从上向下穿越信号线
    sell_condition = when(macd_line(120,260,90)).has_crossed_below(macd_signal(120,260,90))
    
    # 设置数据管理器
    dm = DataManager()
    
    # 生成交易信号
    signals = generate_signals(
        buy_condition=buy_condition,
        sell_condition=sell_condition,
        products=['cj'],  # 期货品种
        start_date='2024-01-01',
        end_date='2024-12-31',
        data_manager=dm
    )
    
    return signals

# 示例2: 布林带突破策略
def bollinger_breakout_strategy():
    # 布林带参数
    period = 20
    std_dev = 2.0
    
    # 买入条件: 价格突破上轨
    upper_band = lambda df: BOLL(df['close'], period, std_dev)['upper']
    buy_condition = when(price()).has_crossed_above(upper_band)
    
    # 卖出条件: 价格突破下轨
    lower_band = lambda df: BOLL(df['close'], period, std_dev)['lower']
    sell_condition = when(price()).has_crossed_below(lower_band)
    
    # 平仓条件: 价格回到布林带中线
    middle_band = lambda df: BOLL(df['close'], period)['middle']
    exit_long_condition = when(price()).has_crossed_below(middle_band)
    exit_short_condition = when(price()).has_crossed_above(middle_band)
    
    # 生成交易信号
    signals = generate_signals(
        buy_condition=buy_condition,
        sell_condition=sell_condition,
        exit_long_condition=exit_long_condition,
        exit_short_condition=exit_short_condition,
        products=['ag', 'cu'],
        start_date='2022-01-01',
        end_date='2022-12-31'
    )
    
    return signals

# 示例3: 结合多个指标的复杂策略
def complex_strategy():
    # 买入条件: RSI<30 并且 价格在20日均线之上
    buy_condition = and_(
        when(lambda df: RSI(df['close'])).is_below(30),
        when(price()).is_above(lambda df: df['close'].rolling(20).mean())
    )
    
    # 卖出条件: RSI>70 或者 价格在10日均线之下
    sell_condition = or_(
        when(lambda df: RSI(df['close'])).is_above(70),
        when(price()).is_below(lambda df: df['close'].rolling(10).mean())
    )
    
    # 生成交易信号
    signals = generate_signals(
        buy_condition=buy_condition,
        sell_condition=sell_condition,
        products=['al', 'zn'],
        start_date='2022-01-01',
        end_date='2022-12-31'
    )
    
    return signals

# 如何使用生成的信号进行回测
def run_backtest():
    from CTA_backtest.backtest_ti import BackTest
    
    # 获取信号
    signals = macd_cross_strategy()
    
    # 创建回测实例
    bt = BackTest()
    
    # 加载价格数据
    dm = DataManager()
    price_data = dm.get_close(['cj'], '2024-01-01', '2024-12-31')
    
    # 执行回测
    bt.fit(
        df_x=signals,  # 使用我们生成的信号
        product_list=['cj'],
        name="MACD_Cross_Strategy",
        begin_date='2024-01-01',
        end_date='2025-12-31',
        cost=0.0002  # 设置交易成本
    )
    
    # 生成回测报告
    bt.report_html(df_y=price_data,fold = 24,path = '')
    
    return bt

# 主函数
if __name__ == "__main__":
    # 运行MACD交叉策略示例
    signals = macd_cross_strategy()
    print(f"生成的信号数量: {len(signals)}")
    print(signals.head())
    
    # 运行回测
    backtest_result = run_backtest()
    print(f"回测完成，性能指标: {backtest_result.df_pnl.head()}") 
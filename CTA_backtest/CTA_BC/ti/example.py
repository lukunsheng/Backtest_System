import pandas as pd
from datetime import datetime
import sys
import os

# 确保能够导入模块
sys.path.append(os.path.abspath('..'))

from CTA_backtest.CTA_BC.ti import (
    when, price, macd_line, macd_signal, rsi, bollinger_upper,
    bollinger_lower, bollinger_middle, and_, or_, not_, generate_signals,
    DataManager
)
from CTA_backtest.backtest import BackTest

# 示例1: 简单的MACD金叉策略
def macd_cross_strategy(products=['rb', 'ru'], start_date='2022-01-01', end_date='2022-12-31'):
    """
    MACD金叉/死叉策略
    """
    print(f"运行MACD策略: 产品={products}, 日期范围={start_date}到{end_date}")
    
    # 创建买入条件: MACD线从下向上穿越信号线
    buy_condition = when(macd_line()).has_crossed_above(macd_signal())
    
    # 创建卖出条件: MACD线从上向下穿越信号线
    sell_condition = when(macd_line()).has_crossed_below(macd_signal())
    
    # 设置数据管理器
    dm = DataManager()
    
    # 生成交易信号
    signals = generate_signals(
        buy_condition=buy_condition,
        sell_condition=sell_condition,
        products=products,
        start_date=start_date,
        end_date=end_date,
        data_manager=dm
    )
    
    if signals.empty:
        print("未能生成任何信号，请检查数据或条件设置")
        return None
        
    print(f"生成了 {len(signals.columns)} 个产品的信号")
    print("信号前5行:")
    print(signals.head())
    
    return signals

# 示例2: RSI超买超卖策略
def rsi_strategy(products=['a', 'ag'], start_date='2022-01-01', end_date='2022-12-31'):
    """
    RSI超买超卖策略
    """
    print(f"运行RSI策略: 产品={products}, 日期范围={start_date}到{end_date}")
    
    # RSI超卖买入
    buy_condition = when(rsi()).is_below(30)
    
    # RSI超买卖出
    sell_condition = when(rsi()).is_above(70)
    
    # 生成交易信号
    signals = generate_signals(
        buy_condition=buy_condition,
        sell_condition=sell_condition,
        products=products,
        start_date=start_date,
        end_date=end_date
    )
    
    if signals.empty:
        print("未能生成任何信号，请检查数据或条件设置")
        return None
        
    print(f"生成了 {len(signals.columns)} 个产品的信号")
    
    return signals

# 执行回测
def run_backtest(strategy_name='macd_cross', products=['rb', 'ru'], 
                start_date='2022-01-01', end_date='2022-12-31'):
    """
    执行回测并生成报告
    """
    print(f"执行回测: 策略={strategy_name}, 产品={products}")
    
    # 选择策略
    if strategy_name == 'macd_cross':
        signals = macd_cross_strategy(products, start_date, end_date)
        strategy_display_name = "MACD交叉策略"
    elif strategy_name == 'rsi':
        signals = rsi_strategy(products, start_date, end_date)
        strategy_display_name = "RSI超买超卖策略"
    else:
        print(f"未知策略: {strategy_name}")
        return None
    
    if signals is None or signals.empty:
        print("无法执行回测: 没有生成信号")
        return None
    
    # 创建回测实例
    bt = BackTest()
    
    # 加载价格数据
    dm = DataManager()
    price_data = dm.get_close(products, start_date, end_date)
    
    if price_data.empty:
        print("无法获取价格数据")
        return None
    
    print("价格数据前5行:")
    print(price_data.head())
    
    # 执行回测
    print("开始执行回测...")
    bt.fit(
        df_x=signals,
        product_list=products,
        name=strategy_display_name,
        begin_date=start_date,
        end_date=end_date,
        cost=0.0002
    )
    
    # 生成回测报告
    print("生成回测报告...")
    bt.report(df_y=price_data)
    
    print("回测完成!")
    return bt

# 主函数
if __name__ == "__main__":
    # 设置参数
    strategy = 'macd_cross'  # 'macd_cross' 或 'rsi'
    products = ['rb', 'ru', 'au']  # 期货产品
    start_date = '2022-01-01'
    end_date = '2022-12-31'
    
    # 运行回测
    result = run_backtest(strategy, products, start_date, end_date)
    
    if result is not None:
        print("\n回测结果:")
        if hasattr(result, 'df_pnl') and not result.df_pnl.empty:
            print(result.df_pnl.head())
        else:
            print("回测未产生有效结果")
    else:
        print("回测执行失败") 
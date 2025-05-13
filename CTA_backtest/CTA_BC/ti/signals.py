import pandas as pd
import numpy as np
from typing import Dict, List, Union, Callable, Optional
from .conditions import Condition
from .datamanager import DataManager

def generate_signals(
    buy_condition: Condition,
    sell_condition: Optional[Condition] = None,
    exit_long_condition: Optional[Condition] = None,
    exit_short_condition: Optional[Condition] = None,
    products: Union[str, List[str]] = None,
    start_date: str = None,
    end_date: str = None,
    data_manager: Optional[DataManager] = None,
    use_custom_data: Optional[Dict[str, pd.DataFrame]] = None
) -> pd.DataFrame:
    """
    根据条件生成交易信号
    
    参数:
    buy_condition: 买入条件
    sell_condition: 卖出条件(做空)
    exit_long_condition: 平多条件
    exit_short_condition: 平空条件
    products: 期货品种列表
    start_date: 开始日期
    end_date: 结束日期
    data_manager: 数据管理器
    use_custom_data: 自定义数据(如果不使用数据库)
    
    返回:
    符合backtest.py要求的信号DataFrame
    """
    if isinstance(products, str):
        products = [products]
    
    if use_custom_data is not None:
        data = use_custom_data
    else:
        if data_manager is None:
            data_manager = DataManager()
            
        data = {}
        for product in products:
            try:
                # 获取OHLC数据
                ohlc = data_manager.get_ohlc([product], start_date, end_date)
                
                # 创建包含产品数据的DataFrame
                product_data = pd.DataFrame({
                    'open': ohlc['open'][product] if product in ohlc['open'].columns else pd.Series(dtype='float64'),
                    'high': ohlc['high'][product] if product in ohlc['high'].columns else pd.Series(dtype='float64'),
                    'low': ohlc['low'][product] if product in ohlc['low'].columns else pd.Series(dtype='float64'),
                    'close': ohlc['close'][product] if product in ohlc['close'].columns else pd.Series(dtype='float64')
                })
                
                # 尝试获取成交量数据
                try:
                    volume_data = data_manager.get_volume([product], start_date, end_date)
                    if product in volume_data.columns:
                        product_data['volume'] = volume_data[product]
                    else:
                        product_data['volume'] = 0
                except Exception:
                    product_data['volume'] = 0
                
                if not product_data.empty:
                    data[product] = product_data
            except Exception as e:
                print(f"处理产品 {product} 时出错: {e}")
    
    # 存储每个产品的交易信号
    signal_dict = {}
    
    # 处理每个产品的信号
    for product in products:
        if product not in data or data[product].empty:
            continue
            
        product_data = data[product]
        
        # 评估交易条件
        buy_signals = buy_condition.evaluate(product_data)
        
        if sell_condition is not None:
            sell_signals = sell_condition.evaluate(product_data)
        else:
            sell_signals = pd.Series(False, index=product_data.index)
            
        if exit_long_condition is not None:
            exit_long_signals = exit_long_condition.evaluate(product_data)
        else:
            exit_long_signals = pd.Series(False, index=product_data.index)
            
        if exit_short_condition is not None:
            exit_short_signals = exit_short_condition.evaluate(product_data)
        else:
            exit_short_signals = pd.Series(False, index=product_data.index)
        
        # 初始化信号序列
        position = 0
        signal_values = []
        
        # 遍历每个时间点生成交易信号
        for date in product_data.index:
            if position == 0:  # 当前无持仓
                if buy_signals.get(date, False):
                    signal_values.append(1)  # 买入信号
                    position = 1
                elif sell_signals.get(date, False):
                    signal_values.append(-1)  # 卖出信号
                    position = -1
                else:
                    signal_values.append(0)  # 不操作
            elif position == 1:  # 当前多头持仓
                if exit_long_signals.get(date, False):
                    signal_values.append(0)  # 平多信号
                    position = 0
                elif sell_signals.get(date, False):
                    signal_values.append(-1)  # 反转至空头
                    position = -1
                else:
                    signal_values.append(0)  # 保持多头
            elif position == -1:  # 当前空头持仓
                if exit_short_signals.get(date, False):
                    signal_values.append(0)  # 平空信号
                    position = 0
                elif buy_signals.get(date, False):
                    signal_values.append(1)  # 反转至多头
                    position = 1
                else:
                    signal_values.append(0)  # 保持空头
        
        # 创建信号序列
        signal_series = pd.Series(signal_values, index=product_data.index)
        
        # 使用产品名作为列名(注意这里不带_flag后缀，与backtest_ti.py兼容)
        signal_dict[f"{product}"] = signal_series
    
    # 检查是否有任何信号数据
    if not signal_dict:
        print("警告: 没有生成任何交易信号")
        # 返回空的DataFrame
        return pd.DataFrame()
    
    # 创建包含所有信号的DataFrame
    return pd.DataFrame(signal_dict)


def convert_for_backtest(signals_df: pd.DataFrame, begin_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    将信号转换为backtest.py所需的格式
    
    参数:
    signals_df: 信号DataFrame
    begin_date: 开始日期
    end_date: 结束日期
    
    返回:
    符合backtest.py要求的DataFrame
    """
    if begin_date is not None or end_date is not None:
        mask = pd.Series(True, index=signals_df.index)
        if begin_date is not None:
            mask = mask & (signals_df.index >= begin_date)
        if end_date is not None:
            mask = mask & (signals_df.index <= end_date)
        signals_df = signals_df[mask].copy()
    
    return signals_df 
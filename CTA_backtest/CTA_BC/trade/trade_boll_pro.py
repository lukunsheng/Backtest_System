# 当前版本还没有给指定品种和指定时间段留出接口
import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

def trade_ori(df, open_thre=2, close_thre=0.8, len_ma=500):
    """
    基础交易信号生成函数，根据信号强度开平仓
    
    参数:
    df (DataFrame): 信号数据，包含一列信号值
    open_thre (float): 开仓阈值系数，默认为2
    close_thre (float): 平仓阈值系数，默认为0.8
    len_ma (int): 移动平均窗口长度，默认为500
    
    返回:
    DataFrame: 包含交易标志的DataFrame，1为开多，-1为开空，0为平仓
    """
    _df = df.copy()
    _df.dropna(inplace=True)
    _df.columns = ['signal']
    _df['pre_signal'] = _df['signal'].shift(1)  # 信号前移一位，用于下一时刻交易
    _df['signal_ma'] = (_df['pre_signal'].abs()).rolling(len_ma).mean()  # 计算信号绝对值的移动平均
    _df.dropna(inplace=True)
    
    # 计算开仓和平仓阈值
    _df['long_threshold'] = _df['signal_ma'] * open_thre  # 开多仓阈值
    _df['short_threshold'] = -_df['signal_ma'] * open_thre  # 开空仓阈值
    _df['close_long_threshold'] = -_df['signal_ma'] * close_thre  # 平多仓阈值
    _df['close_short_threshold'] = _df['signal_ma'] * close_thre  # 平空仓阈值
    
    # 获取各阈值列的值
    signal_values = _df['pre_signal'].values
    long_threshold = _df['long_threshold'].values
    short_threshold = _df['short_threshold'].values
    close_long_threshold = _df['close_long_threshold'].values
    close_short_threshold = _df['close_short_threshold'].values
    
    flags = np.full(len(_df), np.nan)  # 初始化交易标志数组
    close_num = 0  # 记录最近一次平仓位置
    
    # 循环生成交易标志
    for i in range(len(signal_values)):
        if i <= close_num:
            continue  # 跳过已处理的位置
            
        # 开多仓条件：信号值大于开多仓阈值
        if signal_values[i] > long_threshold[i]:
            for j in range(i, len(signal_values)):
                # 平多仓条件：信号值小于平多仓阈值
                if signal_values[j] < close_long_threshold[j]:
                    flags[i] = 1  # 开多仓
                    flags[j] = 0  # 平多仓
                    close_num = j
                    break
                # 到达序列末尾，强制平仓
                elif j == len(signal_values) - 1:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                    
        # 开空仓条件：信号值小于开空仓阈值
        elif signal_values[i] < short_threshold[i]:
            for j in range(i, len(signal_values)):
                # 平空仓条件：信号值大于平空仓阈值
                if signal_values[j] > close_short_threshold[j]:
                    flags[i] = -1  # 开空仓
                    flags[j] = 0  # 平空仓
                    close_num = j
                    break
                # 到达序列末尾，强制平仓
                elif j == len(signal_values) - 1:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break
    
    _df['flag'] = flags
    return _df.loc[:,['flag']]

def trade_factor_mean(df,open_thre,close_thre,len_ma):
    """
    因子均值化交易信号生成函数，先对信号均值中心化再生成交易标志
    
    参数:
    df (DataFrame): 信号数据，包含一列信号值
    open_thre (float): 开仓阈值系数
    close_thre (float): 平仓阈值系数
    len_ma (int): 移动平均窗口长度
    
    返回:
    DataFrame: 包含交易标志的DataFrame，1为开多，-1为开空，0为平仓
    """
    _df = df.copy()
    _df.dropna(inplace = True)
    _df.columns = ['signal']
    _df['pre_signal'] = _df['signal'].shift(1) #收益率计算用的是open开仓，所以在这里需要shift1
    _df['pre_signal'] = _df['pre_signal'] - _df['pre_signal'].mean()
    _df['signal_ma'] = (_df['pre_signal'].abs()).rolling(len_ma).mean()
    _df.dropna(inplace = True)
    
    _df['long_threshold'] = _df['signal_ma'] * open_thre
    _df['short_threshold'] = -_df['signal_ma'] * open_thre
    _df['close_long_threshold'] = -_df['signal_ma'] * close_thre
    _df['close_short_threshold'] = _df['signal_ma'] * close_thre
    
    signal_values = _df['pre_signal'].values
    long_threshold = _df['long_threshold'].values
    short_threshold = _df['short_threshold'].values
    close_long_threshold = _df['close_long_threshold'].values
    close_short_threshold = _df['close_short_threshold'].values
    
    flags = np.full(len(_df), np.nan)
    close_num = 0
    
    # 使用向量化操作
    for i in range(len(signal_values)):
        if i <= close_num:
            continue
            
        # 开多仓条件
        if signal_values[i] > long_threshold[i]:
            for j in range(i, len(signal_values)):
                if signal_values[j] < close_long_threshold[j]:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                    
        # 开空仓条件
        elif signal_values[i] < short_threshold[i]:
            for j in range(i, len(signal_values)):
                if signal_values[j] > close_short_threshold[j]:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break
    
    _df['flag'] = flags
    return _df.loc[:,['flag']]


def trade_ori_amtclean(df, df_amt , open_thre=2, close_thre=0.8, len_ma=500 , amt_threshold = 20 * 1e8):
    """
    考虑成交量的交易信号生成函数，只在成交量超过阈值时开仓
    
    参数:
    df (DataFrame): 信号数据，包含一列信号值
    df_amt (DataFrame): 成交量数据
    open_thre (float): 开仓阈值系数，默认为2
    close_thre (float): 平仓阈值系数，默认为0.8
    len_ma (int): 移动平均窗口长度，默认为500
    amt_threshold (float): 成交量阈值，默认为20*1e8
    
    返回:
    DataFrame: 包含交易标志的DataFrame，1为开多，-1为开空，0为平仓
    """
    _df = df.copy()
    _df.dropna(inplace=True)

    _amt = df_amt.loc[:,_df.columns]
    _amt.columns = ['amt_ma22']

    _df.columns = ['signal']
    _df['pre_signal'] = _df['signal'].shift(1)
    _df['signal_ma'] = (_df['pre_signal'].abs()).rolling(len_ma).mean()
    _df.dropna(inplace=True)
    
    _df['long_threshold'] = _df['signal_ma'] * open_thre
    _df['short_threshold'] = -_df['signal_ma'] * open_thre
    _df['close_long_threshold'] = -_df['signal_ma'] * close_thre
    _df['close_short_threshold'] = _df['signal_ma'] * close_thre
    
    signal_values = _df['pre_signal'].values
    long_threshold = _df['long_threshold'].values
    short_threshold = _df['short_threshold'].values
    close_long_threshold = _df['close_long_threshold'].values
    close_short_threshold = _df['close_short_threshold'].values

    _df = pd.merge(_df,_amt,on = 'datetime',how = 'left')
    amt_ma22 = _df['amt_ma22'].values
    
    flags = np.full(len(_df), np.nan)
    close_num = 0
    
    # 使用向量化操作
    for i in range(len(signal_values)):
        if i <= close_num:
            continue
            
        # 开多仓条件
        if (signal_values[i] > long_threshold[i]) and (amt_ma22[i] > amt_threshold):
            for j in range(i, len(signal_values)):
                if signal_values[j] < close_long_threshold[j]:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                    
        # 开空仓条件
        elif (signal_values[i] < short_threshold[i]) and (amt_ma22[i] > amt_threshold):
            for j in range(i, len(signal_values)):
                if signal_values[j] > close_short_threshold[j]:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break

    _df['flag'] = flags
    return _df.loc[:,['flag']]

def trade_factor_mean_amtclean(df, df_amt , open_thre=2, close_thre=0.8, len_ma=500 , amt_threshold = 20 * 1e8):
    """
    考虑成交量的因子均值化交易信号生成函数，综合了均值中心化和成交量过滤
    
    参数:
    df (DataFrame): 信号数据，包含一列信号值
    df_amt (DataFrame): 成交量数据
    open_thre (float): 开仓阈值系数，默认为2
    close_thre (float): 平仓阈值系数，默认为0.8
    len_ma (int): 移动平均窗口长度，默认为500
    amt_threshold (float): 成交量阈值，默认为20*1e8
    
    返回:
    DataFrame: 包含交易标志的DataFrame，1为开多，-1为开空，0为平仓
    """
    _df = df.copy()
    _df.dropna(inplace=True)

    _amt = df_amt.loc[:,_df.columns]
    _amt.columns = ['amt_ma22']

    _df.columns = ['signal']
    _df['pre_signal'] = _df['signal'].shift(1) #收益率计算用的是open开仓，所以在这里需要shift1
    _df['pre_signal'] = _df['pre_signal'] - _df['pre_signal'].mean()
    _df['signal_ma'] = (_df['pre_signal'].abs()).rolling(len_ma).mean()
    _df.dropna(inplace=True)
    
    _df['long_threshold'] = _df['signal_ma'] * open_thre
    _df['short_threshold'] = -_df['signal_ma'] * open_thre
    _df['close_long_threshold'] = -_df['signal_ma'] * close_thre
    _df['close_short_threshold'] = _df['signal_ma'] * close_thre
    
    signal_values = _df['pre_signal'].values
    long_threshold = _df['long_threshold'].values
    short_threshold = _df['short_threshold'].values
    close_long_threshold = _df['close_long_threshold'].values
    close_short_threshold = _df['close_short_threshold'].values

    _df = pd.merge(_df,_amt,on = 'datetime',how = 'left')
    amt_ma22 = _df['amt_ma22'].values
    
    flags = np.full(len(_df), np.nan)
    close_num = 0
    
    # 使用向量化操作
    for i in range(len(signal_values)):
        if i <= close_num:
            continue
            
        # 开多仓条件
        if (signal_values[i] > long_threshold[i]) and (amt_ma22[i] > amt_threshold):
            for j in range(i, len(signal_values)):
                if signal_values[j] < close_long_threshold[j]:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = 1
                    flags[j] = 0
                    close_num = j
                    break
                    
        # 开空仓条件
        elif (signal_values[i] < short_threshold[i]) and (amt_ma22[i] > amt_threshold):
            for j in range(i, len(signal_values)):
                if signal_values[j] > close_short_threshold[j]:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break
                elif j == len(signal_values) - 1:
                    flags[i] = -1
                    flags[j] = 0
                    close_num = j
                    break

    _df['flag'] = flags
    return _df.loc[:,['flag']]


def create_trade_flag(df, product_list, begin_date='2018-01-01', end_date='2024-08-04', mode='trade_ori', ratio=1, df_amt=None, amt_threshold=20 * 1e8):
    """
    根据选定模式为多品种创建交易标志
    
    参数:
    df (DataFrame): 信号数据，每列对应一个品种的信号
    product_list (list): 品种列表
    begin_date (str): 回测开始日期，默认为'2018-01-01'
    end_date (str): 回测结束日期，默认为'2024-08-04'
    mode (str): 交易模式，可选'trade_ori'/'trade_factor_mean'/'trade_ori_amtclean'等
    ratio (float): 信号比例调整因子，默认为1
    df_amt (DataFrame): 成交量数据，仅在需要考虑成交量的模式下使用
    amt_threshold (float): 成交量阈值，仅在需要考虑成交量的模式下使用
    
    返回:
    DataFrame: 包含所有品种交易标志的DataFrame
    """
    _df = pd.DataFrame()
    open_thre = 2 * ratio  # 根据ratio调整开仓阈值
    close_thre = 0.8  # 保持平仓阈值不变

    # 遍历每个品种生成交易标志
    for product in tqdm(product_list):
        signal_data = df.loc[:, [product]]

        # 筛选日期范围内的数据
        signal_data = signal_data[(signal_data.index >= begin_date) & (signal_data.index <= end_date)]

        # 根据指定的模式生成交易标志
        if mode == 'trade_ori_old':
            df_trade = trade_ori_old(df=signal_data, open_thre=open_thre, close_thre=close_thre, len_ma=500)
        elif mode == 'trade_factor_mean':
            df_trade = trade_factor_mean(df=signal_data, open_thre=open_thre, close_thre=close_thre, len_ma=500)
        elif mode == 'trade_ori':
            df_trade = trade_ori(df=signal_data, open_thre=open_thre, close_thre=close_thre, len_ma=500)
        elif mode == 'trade_ori_amtclean':
            df_trade = trade_ori_amtclean(df=signal_data, df_amt=df_amt, open_thre=open_thre, close_thre=close_thre, len_ma=500, amt_threshold=amt_threshold)
        elif mode == 'trade_factor_amtclean':
            df_trade = trade_factor_mean_amtclean(df=signal_data, df_amt=df_amt, open_thre=open_thre, close_thre=close_thre, len_ma=500, amt_threshold=amt_threshold)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        # 将结果添加到总DataFrame中
        df_trade.columns = [f'{signal_data.columns[0]}']
        _df = pd.concat([_df, df_trade], axis=1)

    return _df
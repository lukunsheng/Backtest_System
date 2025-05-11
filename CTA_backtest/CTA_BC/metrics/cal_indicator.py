import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from tqdm import tqdm

def cal_metric(df_all,df_long,df_short):
    """
    计算策略的各项绩效指标
    
    参数:
    df_all (DataFrame): 总体收益数据，包含多头和空头
    df_long (DataFrame): 多头收益数据
    df_short (DataFrame): 空头收益数据
    
    返回:
    df_pnl (DataFrame): 累计收益曲线数据
    _dict (dict): 包含各项绩效指标的字典
    """
    
    # 合并总体、多头和空头的收益数据
    _df_all = pd.DataFrame(df_all.sum(axis = 1),columns = ['return_all'])
    _df_long = pd.DataFrame(df_long.sum(axis = 1),columns = ['return_long'])
    _df_short = pd.DataFrame(df_short.sum(axis = 1),columns = ['return_short'])

    df_plot = pd.merge(_df_all,_df_long,on = 'datetime',how = 'left')
    df_plot = pd.merge(df_plot,_df_short,on = 'datetime',how = 'left')
    df_pnl = df_plot.cumsum()  # 计算累计收益

    # 计算胜率 (正收益交易占比)
    all_win_rate = (df_all > 0).sum().sum() / (pd.notnull(df_all)).sum().sum()
    long_win_rate = (df_long > 0).sum().sum() / (pd.notnull(df_long)).sum().sum()
    short_win_rate = (df_short > 0).sum().sum() / (pd.notnull(df_short)).sum().sum()

    # 计算盈亏比 (盈利交易总和/亏损交易总和的绝对值)
    all_ProfitLoss_ratio = df_all[df_all > 0].sum().sum() / abs(df_all[df_all < 0]).sum().sum()
    long_ProfitLoss_ratio = df_long[df_long > 0].sum().sum() / abs(df_long[df_long < 0]).sum().sum()
    short_ProfitLoss_ratio = df_short[df_short > 0].sum().sum() / abs(df_short[df_short < 0]).sum().sum()

    # 计算交易次数
    count_all = (pd.notnull(df_all)).sum().sum()
    count_long = (pd.notnull(df_long)).sum().sum()
    count_short = (pd.notnull(df_short)).sum().sum()

    # 计算平均收益率
    MeanRet_all = df_all.sum().sum() / count_all
    MeanRet_long = df_long.sum().sum() / count_long
    MeanRet_short = df_short.sum().sum() / count_short
    
    # 计算交易天数和日均交易次数
    day_len = len(pd.Series(df_all.index).apply(lambda x: str(x)[:10]).unique())
    count_all_D = count_all/day_len
    count_long_D = count_long/day_len
    count_short_D = count_short/day_len

    # 计算总利润
    all_profit = df_pnl['return_all'][-1]
    long_profit = df_pnl['return_long'][-1]
    short_profit = df_pnl['return_short'][-1]

    # 汇总所有指标到字典
    _dict = {
            'all_win_rate': all_win_rate,         # 总体胜率
            'long_win_rate': long_win_rate,       # 多头胜率
            'short_win_rate': short_win_rate,     # 空头胜率
            'all_ProfitLoss_ratio': all_ProfitLoss_ratio,     # 总体盈亏比
            'long_ProfitLoss_ratio': long_ProfitLoss_ratio,   # 多头盈亏比
            'short_ProfitLoss_ratio': short_ProfitLoss_ratio, # 空头盈亏比
            'MeanRet_all': MeanRet_all,           # 总体平均收益
            'MeanRet_long': MeanRet_long,         # 多头平均收益
            'MeanRet_short': MeanRet_short,       # 空头平均收益
            'count_all': count_all,               # 总交易次数
            'count_long': count_long,             # 多头交易次数
            'count_short': count_short,           # 空头交易次数
            'count_all_D': count_all_D,           # 日均总交易次数
            'count_long_D': count_long_D,         # 日均多头交易次数
            'count_short_D': count_short_D,       # 日均空头交易次数
            'all_profit': all_profit,             # 总利润
            'long_profit': long_profit,           # 多头总利润
            'short_profit': short_profit          # 空头总利润
            }
    
    return df_pnl,_dict
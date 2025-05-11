import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

def _plot_pnl(df,df_fold,_dict,name,path = None):
    """
    绘制策略的PnL曲线和收益分布图
    
    参数:
    df (DataFrame): 累计收益数据
    df_fold (DataFrame): 周期收益分布数据
    _dict (dict): 绩效指标字典
    name (str): 策略名称
    path (str): 结果保存路径，默认为None
    """
    # 创建图形和网格布局，高度比为4:1
    fig = plt.figure(figsize=(16, 8))
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[4, 1])
    
    # 创建折线图子图 - PnL曲线
    ax1 = fig.add_subplot(gs[0, 0])
    for column in df.columns:
        ax1.plot(df.index, df[column], label=column)
    ax1.set_ylabel('PNL Values')
    ax1.set_title(f'{name} PNL')
    ax1.grid(True)
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # 在图表中添加统计指标文本框
    textstr = (
        f'总利润: {_dict["all_profit"]:.2f}\n'
        f'多头总利润: {_dict["long_profit"]:.2f}\n'
        f'空头总利润: {_dict["short_profit"]:.2f}\n'
        f'交易次数: {_dict["count_all"]} (日均: {_dict["count_all_D"]:.2f})\n'
        f'多头交易次数: {_dict["count_long"]} (日均: {_dict["count_long_D"]:.2f})\n'
        f'空头交易次数: {_dict["count_short"]} (日均: {_dict["count_short_D"]:.2f})\n'
        f'盈亏比: {_dict["all_ProfitLoss_ratio"]:.3f} (胜率: {_dict["all_win_rate"]:.2%})\n'
        f'多头盈亏比: {_dict["long_ProfitLoss_ratio"]:.3f} (胜率: {_dict["long_win_rate"]:.2%})\n'
        f'空头盈亏比: {_dict["short_ProfitLoss_ratio"]:.3f} (胜率: {_dict["short_win_rate"]:.2%})\n'
        f'平均利润: {_dict["MeanRet_all"] * 1000:.3f} ‰\n'
        f'多头平均利润: {_dict["MeanRet_long"] * 1000:.3f} ‰\n'
        f'空头平均利润: {_dict["MeanRet_short"] * 1000:.3f} ‰'
    )
    
    # 设置文本框样式
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props)

    # 创建柱状图子图 - 周期收益分布
    ax2 = fig.add_subplot(gs[1, 0])
    bar_width = 0.25
    indices = range(len(df_fold))
    ax2.bar(indices, df_fold['all_fold'], bar_width, label='fold_all')
    ax2.bar([i + bar_width for i in indices], df_fold['long_fold'], bar_width, label='fold_long')
    ax2.bar([i + 2 * bar_width for i in indices], df_fold['short_fold'], bar_width, label='fold_short')
    ax2.set_xlabel('Categories')
    ax2.set_xticks([i + bar_width for i in indices])
    ax2.set_xticklabels(df_fold.index)
    ax2.set_ylabel('Values')
    ax2.set_title(f'{name} Fold Ret')
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax2.grid(axis='y', alpha=0.75)

    # 调整子图间距
    plt.subplots_adjust(hspace=0.2)

    # 如果指定了保存路径，则保存图像
    if path:
        os.makedirs(f'{path}/result/{name}', exist_ok=True)
        plt.savefig(f'{path}/result/{name}/{name}_pnl.png') 
        
def _plot_pnl_product(df,df_fold,_dict,name,p,path = None):
    """
    绘制单个品种的PnL曲线和收益分布图
    
    参数:
    df (DataFrame): 累计收益数据
    df_fold (DataFrame): 周期收益分布数据
    _dict (dict): 绩效指标字典
    name (str): 策略名称
    p (str): 品种名称
    path (str): 结果保存路径，默认为None
    """
    # 创建图形和网格布局，高度比为4:1
    fig = plt.figure(figsize=(16, 8))
    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[4, 1])
    
    # 创建折线图子图 - PnL曲线
    ax1 = fig.add_subplot(gs[0, 0])
    for column in df.columns:
        ax1.plot(df.index, df[column], label=column)
    ax1.set_ylabel('PNL Values')
    ax1.set_title(f'{name}{p} PNL')
    ax1.grid(True)
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # 在图表中添加统计指标文本框
    textstr = (
        f'总利润: {_dict["all_profit"]:.2f}\n'
        f'多头总利润: {_dict["long_profit"]:.2f}\n'
        f'空头总利润: {_dict["short_profit"]:.2f}\n'
        f'交易次数: {_dict["count_all"]} (日均: {_dict["count_all_D"]:.2f})\n'
        f'多头交易次数: {_dict["count_long"]} (日均: {_dict["count_long_D"]:.2f})\n'
        f'空头交易次数: {_dict["count_short"]} (日均: {_dict["count_short_D"]:.2f})\n'
        f'盈亏比: {_dict["all_ProfitLoss_ratio"]:.3f} (胜率: {_dict["all_win_rate"]:.2%})\n'
        f'多头盈亏比: {_dict["long_ProfitLoss_ratio"]:.3f} (胜率: {_dict["long_win_rate"]:.2%})\n'
        f'空头盈亏比: {_dict["short_ProfitLoss_ratio"]:.3f} (胜率: {_dict["short_win_rate"]:.2%})\n'
        f'平均利润: {_dict["MeanRet_all"] * 1000:.3f} ‰\n'
        f'多头平均利润: {_dict["MeanRet_long"] * 1000:.3f} ‰\n'
        f'空头平均利润: {_dict["MeanRet_short"] * 1000:.3f} ‰'
    )
    
    # 设置文本框样式
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props)

    # 创建柱状图子图 - 周期收益分布
    ax2 = fig.add_subplot(gs[1, 0])
    bar_width = 0.25
    indices = range(len(df_fold))
    ax2.bar(indices, df_fold['all_fold'], bar_width, label='fold_all')
    ax2.bar([i + bar_width for i in indices], df_fold['long_fold'], bar_width, label='fold_long')
    ax2.bar([i + 2 * bar_width for i in indices], df_fold['short_fold'], bar_width, label='fold_short')
    ax2.set_xlabel('Categories')
    ax2.set_xticks([i + bar_width for i in indices])
    ax2.set_xticklabels(df_fold.index)
    ax2.set_ylabel('Values')
    ax2.set_title(f'{name}{p} Fold Ret')
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))
    ax2.grid(axis='y', alpha=0.75)

    # 调整子图间距
    plt.subplots_adjust(hspace=0.2)

    # 如果指定了保存路径，则保存图像
    if path:
        os.makedirs(f'{path}/result/{name}', exist_ok=True)
        plt.savefig(f'{path}/result/{name}/{name}{p}_pnl.png') 
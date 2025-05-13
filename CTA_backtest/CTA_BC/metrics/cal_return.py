import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from tqdm import tqdm

def calculate_returns(df,cost):
    """
    计算单个品种的交易收益
    
    参数:
    df (DataFrame): 包含价格和仓位数据的DataFrame
    cost (float): 交易成本
    
    返回:
    _df_pnl (DataFrame): 包含多头、空头和总体收益的DataFrame
    """
    open_prices = {'long': None, 'short': None}
    for i, row in df.iterrows():
        if row['position'] == 1:
            # 开多仓
            open_prices['long'] = row['price']
        elif row['position'] == -1:
            # 开空仓
            open_prices['short'] = row['price']
        elif row['position'] == 0:
            if open_prices['long'] is not None:
                # 平多仓，计算收益 = (平仓价/开仓价-1)-成本
                df.at[i, 'return_long'] = ((row['price'] / open_prices['long']) - 1) - cost
                open_prices['long'] = None
            if open_prices['short'] is not None:
                # 平空仓，计算收益 = (1-平仓价/开仓价)-成本
                df.at[i, 'return_short'] = (1 - (row['price'] / open_prices['short'])) - cost
                open_prices['short'] = None
    
    # 提取收益数据并计算总收益
    _df_pnl = df.loc[:,['return_long','return_short']]    
    _df_pnl['return'] = np.where(
                                (_df_pnl['return_long'].isna() & _df_pnl['return_short'].isna()), 
                                np.nan, 
                                _df_pnl['return_long'].fillna(0) + _df_pnl['return_short'].fillna(0)
                            )
    return _df_pnl



def calculate_returns_all(df_x,df_y,product_list,cost = 0):
    """
    计算多品种的总体收益
    
    参数:
    df_x (DataFrame): 交易信号数据
    df_y (DataFrame): 价格数据
    product_list (list): 品种列表
    cost (float): 交易成本，默认为0
    
    返回:
    _df_ret_all (DataFrame): 所有品种的总体收益
    _df_ret_long (DataFrame): 所有品种的多头收益
    _df_ret_short (DataFrame): 所有品种的空头收益
    """
    _df_ret_long = pd.DataFrame(index=df_y.index)
    _df_ret_short = pd.DataFrame(index=df_y.index)
    _df_ret_all = pd.DataFrame(index=df_y.index)
    
    # 遍历每个品种计算收益
    for product in tqdm(product_list):
        # 获取价格数据
        if product not in df_y.columns:
            warnings.warn(f"产品 {product} 在价格数据中不存在，跳过")
            continue
            
        base_price = df_y.loc[:,[product]]
        
        # 获取信号数据 - 修复：兼容直接使用产品名或带_flag后缀
        flag_column = f"{product}_flag"
        if flag_column in df_x.columns:
            factor_flag = df_x.loc[:,[flag_column]].dropna()
        elif product in df_x.columns:
            factor_flag = df_x.loc[:,[product]].dropna()
        else:
            warnings.warn(f"产品 {product} 的信号数据不存在 (检查了 '{product}' 和 '{flag_column}')，跳过")
            continue
        
        # 过滤日期
        base_price = base_price[base_price.index >= '2018-01-01']
        base_price.columns = ['price']
        factor_flag.columns = ['position']
        
        # 确保索引名称一致，以便合并
        if base_price.index.name != factor_flag.index.name:
            # 如果索引名称不同，让我们确保至少一个为'datetime'
            if base_price.index.name != 'datetime':
                base_price.index.name = 'datetime'
            if factor_flag.index.name != 'datetime':
                factor_flag.index.name = 'datetime'
        
        # 合并价格和信号数据
        try:
            _df = pd.merge(base_price, factor_flag, left_index=True, right_index=True)
            # _df = pd.merge(base_price, factor_flag, on='datetime', how='right') # 旧代码
        except Exception as e:
            warnings.warn(f"合并产品 {product} 的价格和信号数据时出错: {str(e)}，尝试重置索引名称")
            # 如果合并失败，尝试重置索引名称后再次合并
            base_price_reset = base_price.reset_index()
            factor_flag_reset = factor_flag.reset_index()
            _df = pd.merge(base_price_reset, factor_flag_reset, on=base_price_reset.columns[0], how='right')
            _df = _df.set_index(base_price_reset.columns[0])
        
        _df.sort_index(inplace = True)

        # 初始化收益列
        _df['return_long'] = np.nan
        _df['return_short'] = np.nan
        # _df.columns = ['price', 'position', 'return_long', 'return_short']
        
        # 计算收益
        _df_ret = calculate_returns(df=_df, cost=cost)

        # 将收益存入结果DataFrame
        _df_ret_long[f'{product}_long'] = np.nan
        _df_ret_short[f'{product}_short'] = np.nan
        _df_ret_all[f'{product}_all'] = np.nan
        _df_ret_long.loc[_df_ret.index, f'{product}_long'] = _df_ret['return_long']
        _df_ret_short.loc[_df_ret.index, f'{product}_short'] = _df_ret['return_short']
        _df_ret_all.loc[_df_ret.index, f'{product}_all'] = _df_ret['return']
        
    return _df_ret_all,_df_ret_long,_df_ret_short


def calculate_returns_folds(df_x,df_y,product_list,fold = 24):
    """
    计算不同持仓周期的收益分布
    
    参数:
    df_x (DataFrame): 交易信号数据
    df_y (DataFrame): 价格数据
    product_list (list): 品种列表
    fold (int): 分析的周期数，默认为24
    
    返回:
    df_fold (DataFrame): 不同周期的收益贡献分布
    """
    long_fold = pd.DataFrame()
    long_fold.index.name = 'fold_num'
    short_fold = pd.DataFrame()
    short_fold.index.name = 'fold_num'
    df_y = df_y.sort_index()
    
    # 遍历每个品种
    for product in product_list:
        base_data = df_y.loc[:,[product]].dropna()

        # 计算每个周期的收益率
        for i in range(1,fold+1):
            base_data[f'fold_{i}'] = (base_data[product].shift(-i) - base_data[product].shift(-i+1))/base_data[product]
        _fold_data = base_data.loc[:,[f'fold_{i}' for i in range(1,fold+1)]]

        # 分别计算多头和空头持仓的周期收益
        _f = df_x.loc[:,[product]]
        _f_long = _fold_data.loc[_f[_f[_f.columns[0]] == 1].index,:]  # 多头开仓点的周期收益
        _f_short = _fold_data.loc[_f[_f[_f.columns[0]] == -1].index,:]  # 空头开仓点的周期收益
        
        # 计算每个周期的累计收益
        _t_long = pd.DataFrame(_f_long.sum())
        _t_short = pd.DataFrame(_f_short.sum()) 
        _t_short = -_t_short  # 空头收益取负
        _t_long.index.name = 'fold_num'
        _t_long.columns = [product]
        _t_short.index.name = 'fold_num'
        _t_short.columns = [product]
        
        # 合并结果
        long_fold = pd.merge(long_fold, _t_long, on = 'fold_num',how = 'outer')
        short_fold = pd.merge(short_fold, _t_short, on = 'fold_num',how = 'outer')
    
    # 计算多空总收益
    df_fold = pd.concat([long_fold.sum(axis = 1),short_fold.sum(axis = 1)],axis=1)
    df_fold.columns = ['long_fold','short_fold']
    df_fold['all_fold'] = df_fold.sum(axis = 1)
    
    # 归一化收益分布
    df_fold = df_fold/abs(df_fold).sum()
    df_fold = round(df_fold * 100, 1)  # 转为百分比
    
    # 整理索引
    df_fold.index = [j.split('_')[1] for j in df_fold.index]
    df_fold.index = df_fold.index.astype(int)
    df_fold = df_fold.sort_index()
    
    return df_fold
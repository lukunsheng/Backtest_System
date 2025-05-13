from __future__ import division
import pandas as pd
import numpy as np
import os
import datetime

class Factor_template(object):
    """
    因子计算模板基类。
    主要功能：
    1. 加载配置。
    2. 读取和预处理市场数据 (包括重采样)。
    3. 提供接口给子类实现具体的因子计算逻辑。
    4. 保存计算出的信号到Parquet文件。
    """
    def __init__(self, config):
        self.config = config
        self.signals_data = {} # 用来存储每个品种的信号Series: {future_code: signal_series}
        
        # 定义基础的OHLCVA列，以及复权后因子脚本期望的列名
        self.base_ohlcv_columns = ['open', 'high', 'low', 'close', 'volume', 'amount', 'open_interest', 'twap', 'vwap']
        self.hfq_column_map = {
            'open': 'hfq_openPrice',
            'high': 'hfq_highPrice',
            'low': 'hfq_lowPrice',
            'close': 'hfq_closePrice',
            # volume等其他列如果因子脚本需要hfq_前缀，也可以在这里添加映射
        }
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.base_data_file = os.path.join(self.data_path, 'BackTest_BaseData_5min.h5')

    def _get_hdf_key(self, future_code_with_suffix):
        """从 'A_main' 转换为 'A' 作为HDF5的key"""
        if future_code_with_suffix.endswith('_main'):
            return future_code_with_suffix[:-5]
        if future_code_with_suffix.endswith('_dominant'):
            return future_code_with_suffix[:-9]
        return future_code_with_suffix # 如果没有特定后缀，直接返回

    def read_market_data(self, future_code):
        """
        读取单个品种的市场数据，并进行重采样。
        """
        hdf_key = self._get_hdf_key(future_code)
        try:
            df_5min = pd.read_hdf(self.base_data_file, key=hdf_key)
        except KeyError:
            print(f"警告: 在 {self.base_data_file} 中未找到品种 {future_code} (尝试的key: {hdf_key})。跳过此品种。")
            return None

        if not isinstance(df_5min.index, pd.DatetimeIndex):
            df_5min['datetime'] = pd.to_datetime(df_5min['datetime'])
            df_5min.set_index('datetime', inplace=True)

        # 确保所有基础列存在，不存在的用NaN填充
        for col in self.base_ohlcv_columns:
            if col not in df_5min.columns:
                df_5min[col] = np.nan
        
        df_5min = df_5min[self.base_ohlcv_columns] # 只保留需要的列

        timeframe = self.config.get('cycle', '5min')

        if timeframe == '5min':
            df_resampled = df_5min.copy()
        else:
            resample_config = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'amount': 'sum',
                'open_interest': 'last',
                'twap': 'mean', # TWAP和VWAP的重采样规则可能需要更复杂的逻辑，这里用均值作为示例
                'vwap': 'mean'
            }
            df_resampled = df_5min.resample(timeframe).agg(resample_config)
            df_resampled.dropna(subset=['open'], inplace=True) # 通常如果开盘价为空，则该周期无效

        # 添加因子脚本期望的 hfq_ 前缀列 (简单复制)
        for base_col, hfq_col in self.hfq_column_map.items():
            if base_col in df_resampled.columns:
                df_resampled[hfq_col] = df_resampled[base_col]
            else:
                df_resampled[hfq_col] = np.nan
                
        return df_resampled

    def adjust_market_data(self, market_data_df):
        """
        调整行情数据，例如过滤夜盘。
        子类可以重写此方法以实现特定的调整逻辑。
        这里的实现基于F066中的时间过滤。
        """
        if market_data_df is None or market_data_df.empty:
            return market_data_df
        
        # F066中的过滤逻辑: (market_data[:,barTime]>='08:00')&(market_data[:,barTime]<='22:45')
        # 注意：'22:45' 可能意味着包含22:45这一刻的数据。
        # pd.Timestamp.time() 比较时，结束时间如果是 '22:45'，通常指到 '22:45:00' (含)。
        min_time = datetime.time(8, 0)
        max_time = datetime.time(22, 45) # F066 使用 <= '22:45'

        # 创建一个Series来表示每天的时间，然后进行比较
        times = market_data_df.index.time
        
        # 确保比较的是 time 对象
        market_data_df = market_data_df[(times >= min_time) & (times <= max_time)]
        return market_data_df

    def calculate_factor_for_future(self, market_data_df, future_code):
        """
        计算单个品种的因子信号。
        这是子类必须重写的方法。
        market_data_df: 经过重采样和基础调整的Pandas DataFrame。
        future_code: 当前处理的品种代码。
        应返回一个Pandas DataFrame，至少包含 'signal' 列，以及其他希望保存的额外列。
        """
        raise NotImplementedError("子类必须实现 calculate_factor_for_future 方法")

    def process_and_save_signals(self):
        """
        处理所有品种的信号计算并保存到Parquet文件。
        """
        print(f"开始处理因子: {self.config.get('factor_name', '未知因子')}")
        all_signals_for_parquet = {}

        for future_code in self.config.get('futurePool', []):
            print(f"  正在处理品种: {future_code}")
            market_data_raw = self.read_market_data(future_code)
            
            if market_data_raw is None or market_data_raw.empty:
                print(f"  品种 {future_code} 数据为空或读取失败，跳过。")
                continue

            market_data_adjusted = self.adjust_market_data(market_data_raw.copy()) # 使用副本避免修改原始缓存（如果未来添加缓存）
            
            if market_data_adjusted is None or market_data_adjusted.empty:
                print(f"  品种 {future_code} 调整后数据为空，跳过。")
                continue

            # 调用子类实现的具体因子计算逻辑
            # 子类实现的 calculate_factor_for_future 应该返回一个包含 'signal' 列的DataFrame
            try:
                # 传递给子类的数据应该包含hfq_列，因为F066等脚本依赖它们
                factor_output_df = self.calculate_factor_for_future(market_data_adjusted.copy(), future_code)
            except Exception as e:
                print(f"  计算品种 {future_code} 信号时发生错误: {e}")
                continue

            if 'signal' not in factor_output_df.columns:
                print(f"  警告: 品种 {future_code} 的因子计算结果未包含 'signal' 列。跳过此品种的信号保存。")
                continue
            
            # 存储最终的信号列 (Series)
            all_signals_for_parquet[future_code] = factor_output_df['signal']

        if not all_signals_for_parquet:
            print("没有计算得到任何信号数据，不生成Parquet文件。")
            return

        # 合并所有品种的信号为一个DataFrame
        final_signals_df = pd.DataFrame(all_signals_for_parquet)
        final_signals_df.sort_index(inplace=True) # 按datetime排序

        # 重命名列名，去掉 '_main' 或 '_dominant' 后缀以匹配期望的Parquet格式
        renamed_columns = {col: self._get_hdf_key(col) for col in final_signals_df.columns}
        final_signals_df.rename(columns=renamed_columns, inplace=True)

        output_filename = f"{self.config.get('factor_name', 'untitled_factor')}.parquet"
        output_path = os.path.join(self.data_path, output_filename)
        
        try:
            final_signals_df.to_parquet(output_path)
            print(f"信号已成功保存到: {output_path}")
        except Exception as e:
            print(f"保存信号到Parquet文件 {output_path} 时发生错误: {e}")

    # 辅助方法，如果子类需要动态添加列到DataFrame中，可以直接操作DataFrame
    # def add_market_data_column(self, df, column_name, initial_value):
    #    df[column_name] = initial_value
    #    return df

    # def add_extra_column_to_signal_df(self, extra_columns_list):
    #    # 这个方法在当前架构下（子类返回包含所有需要列的DataFrame）可能不太需要由模板直接调用
    #    # 但可以作为子类通知模板哪些列是额外产出的方式，如果保存逻辑更复杂的话
    #    if 'extra_signal_columns' not in self.config:
    #        self.config['extra_signal_columns'] = []
    #    self.config['extra_signal_columns'].extend(extra_columns_list)
    #    self.config['extra_signal_columns'] = list(set(self.config['extra_signal_columns']))


# ---- 使用示例 ----
# 以下是如何修改 F066_15min_factor_52fut.py 来使用这个模板：
#
# from __future__ import division
# import datetime
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # 确保能找到Factor_template
# import numpy as np
# import pandas as pd # 子类也可能需要pandas
# from Factor_template import Factor_template # 导入基类
#
# class Factor(Factor_template): # 继承 Factor_template
#     """
#     signal 因子类
#     主要功能：
#     1、构建期货策略单因子 (基于KDJ)
#     """
#     # __init__ 会被父类调用，传入config
#     # adjust_market_data 如果需要特定调整，可以重写，否则使用父类的默认实现
#
#     def calculate_factor_for_future(self, market_data_df, future_code):
#         """
#         计算F066因子的信号。
#         market_data_df: 包含hfq_openPrice等列的Pandas DataFrame。
#         """
#         # 初始化信号列 (父类已确保market_data_df中没有'signal'列，或者由子类全权负责输出)
#         market_data_df['signal'] = 0.0 # 初始化信号，可以根据需要用np.nan或0
#         
#         # 初始化指标列
#         market_data_df['KDJ_0'] = np.nan
#         market_data_df['KDJ_1'] = 50.0 # 初始值根据原脚本
#         market_data_df['KDJ_2'] = 50.0 # 初始值根据原脚本
#         market_data_df['KDJ_3'] = np.nan
#
#         # 获取所需的字段 (已经是DataFrame的列名)
#         # hfq_openPrice = 'hfq_openPrice' # 等等，直接用字符串作为key
#
#         Len = 300
#         f = 200
#         # beta = 1.2 # beta 在原F066中未被使用，注释掉
#
#         kdjLen = Len
#         std_len = f
#         window = max([Len, f]) + 1
#
#         if market_data_df.shape[0] <= window:
#             # print(f"数据不足以计算因子 {future_code}, 需要 {window} 行, 实际 {market_data_df.shape[0]} 行")
#             return market_data_df # 返回带有初始化信号的DataFrame
#
#         # 使用 .loc 避免 SettingWithCopyWarning
#         for i in range(window, market_data_df.shape[0]):
#             current_time_idx = market_data_df.index[i]
#             prev_time_idx = market_data_df.index[i-1]
#
#             market_data_df.loc[current_time_idx, 'signal'] = market_data_df.loc[prev_time_idx, 'signal']
#
#             # 计算KDJ
#             # 注意：DataFrame的rolling操作可能更高效，但这里为了贴近原逻辑使用循环和iloc/loc
#             low_min_kdjlen = np.min(market_data_df['hfq_lowPrice'].iloc[i-kdjLen:i])
#             high_max_kdjlen = np.max(market_data_df['hfq_highPrice'].iloc[i-kdjLen:i])
#             
#             denominator = high_max_kdjlen - low_min_kdjlen
#             if denominator == 0: # 避免除以零
#                 kdj_0_val = 50 # 或者其他合理的默认值
#             else:
#                 kdj_0_val = 100 * (market_data_df['hfq_closePrice'].iloc[i-1] - low_min_kdjlen) / denominator
#             
#             market_data_df.loc[current_time_idx, 'KDJ_0'] = kdj_0_val
#             market_data_df.loc[current_time_idx, 'KDJ_1'] = (2/3) * market_data_df.loc[prev_time_idx, 'KDJ_1'] + market_data_df.loc[current_time_idx, 'KDJ_0'] * (1/3)
#             market_data_df.loc[current_time_idx, 'KDJ_2'] = (2/3) * market_data_df.loc[prev_time_idx, 'KDJ_2'] + market_data_df.loc[current_time_idx, 'KDJ_1'] * (1/3)
#             market_data_df.loc[current_time_idx, 'KDJ_3'] = 3 * market_data_df.loc[current_time_idx, 'KDJ_1'] - 2 * market_data_df.loc[current_time_idx, 'KDJ_2']
#
#             k = market_data_df.loc[current_time_idx, 'KDJ_1']
#             j_val = market_data_df.loc[current_time_idx, 'KDJ_3'] # 避免与列名 'J' 冲突
#
#             if j_val > 90 and k > 80:
#                 market_data_df.loc[current_time_idx, 'signal'] = 1
#             elif j_val < 10 and k < 20:
#                 market_data_df.loc[current_time_idx, 'signal'] = -1
#
#             # beta = 1.2，原脚本的这个波动率过滤部分
#             volatility = np.std(market_data_df['hfq_closePrice'].iloc[i-std_len:i], ddof=1) / market_data_df['hfq_closePrice'].iloc[i-1]
#             if volatility > (1.2 / 100) : # beta/100
#                 market_data_df.loc[current_time_idx, 'signal'] = 0
#
#         # 信号值限制 (原脚本的逻辑)
#         market_data_df['signal'] = np.clip(market_data_df['signal'], -1, 1)
#         
#         # 如果希望KDJ值也保存到最终的Parquet，需要修改保存逻辑
#         # 目前模板只保存 'signal' 列。
#         # 如果需要保存KDJ列，可以让此方法返回包含这些列的DataFrame，
#         # 然后修改 Factor_template 的 save_signals_to_parquet 方法。
#         # 为了简单起见，并匹配现有parquet格式，我们只返回包含'signal'的DataFrame部分
#         # 但DataFrame本身包含了KDJ列，如果将来需要，它们是可用的。
#         return market_data_df # 返回包含 'signal' 和 KDJ 列的DataFrame
#
# def factor_config(): # 这个函数保持不变
#     return {
#         'factor_name':'F066_15min_factor_52fut',
#         'factor_description':'066号因子-趋势-15min-KDJ-52个品种',
#         'futurePool': [
#             'A_main','B_main','M_main','Y_main','RM_main','OI_main','P_main',
#             'CF_main','SR_main','JD_main','CS_main','C_main','AP_main','CJ_main','LH_main','PK_main',
#             'AG_main','AU_main','CU_main','AL_main','ZN_main','PB_main','NI_main','SN_main',
#             'RB_main','HC_main','J_main','JM_main','I_main', 'SM_main','SF_main','SS_main',
#             'PP_main','L_main','V_main','TA_main','PF_main','MA_main','RU_main','NR_main','BU_main','EG_main','FG_main','UR_main','EB_main','SA_main','SP_main',
#             'SC_main','FU_main','ZC_main','LU_main','PG_main',
#             ],
#         'cycle':'15min',
#         'incremental_calculation_rows':301, # 这个参数在当前模板中未直接使用，但保留配置
#     }
#
# if __name__ == '__main__':
#     factor_instance = Factor(factor_config()) # 实例化
#     factor_instance.process_and_save_signals() # 调用模板提供的处理和保存方法 
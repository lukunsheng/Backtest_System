import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决保存图像是负号'-'显示为方块的问题
import seaborn as sns
import warnings
from tqdm import tqdm
from .CTA_BC.preprocess._plot_pro import generate_report_for_product    # 导入单个产品报告生成函数
from .CTA_BC.trade.trade_boll import trade_ori,create_trade_flag  # 导入交易信号生成函数
from .CTA_BC.metrics.cal_return import calculate_returns_all,calculate_returns_folds  # 导入收益率计算函数
from .CTA_BC.metrics.cal_indicator import cal_metric      # 导入绩效指标计算函数
from sklearn.utils.validation import check_is_fitted      # 导入模型检查工具

class BackTest:
    """
    CTA策略回测框架主类
    提供策略信号生成、回测执行、绩效评估和结果可视化功能
    """
    def __init__(self):
        self.df_x_input = None # 保存原始策略信号
        self.df_amt_input = None # 保存成交量数据
        self._fitted = False # 标记是否已执行回测

    def fit(self, df_x, product_list, name, begin_date='2018-01-01', end_date='2024-08-04', cost=0, mode='trade_ori', ratio=1, df_amt=None, amt_threshold=20*1e8):
        """
        执行回测主函数
        
        参数:
        df_x (DataFrame): 策略信号数据，index为datetime，columns为品种名称
        product_list (list): 要回测的品种列表 (干净的产品名)
        name (str): 策略名称
        begin_date (str): 回测开始日期，默认'2018-01-01'
        end_date (str): 回测结束日期，默认'2024-08-04'
        cost (float): 交易成本，默认0
        mode (str): 交易模式，可选'trade_ori'/'trade_factor_mean'/'trade_ori_amtclean'等
        ratio (float): 信号比例调整因子，默认1
        df_amt (DataFrame): 成交量数据，仅在需要考虑成交量的模式下使用
        amt_threshold (float): 成交量阈值，仅在需要考虑成交量的模式下使用
        """
        self.df_x_input = df_x
        if df_amt is not None:
            self.df_amt_input = df_amt.copy()
        else:
            self.df_amt_input = None
        
        _df_x_sorted = df_x.sort_index()  
        self.product_list = product_list  
        self.name = name  
        self.cost = cost  
        self.begin_date = begin_date  
        self.end_date = end_date  
        
        # 生成交易信号，create_trade_flag 应返回列名为 PRODUCT_flag 的 DataFrame
        self.flag = self.df_x_input.copy()
        self.flag.columns=[item + "_flag" for item in self.flag.columns]
        
        self._fitted = True  

    def report(self,df_y,fold = 24,path = None):
        """
        生成回测报告和可视化结果
        
        参数:
        df_y (DataFrame): 价格数据，index为datetime，columns为品种名称
        fold (int): 周期收益分析的周期数，默认24
        path (str): 结果保存路径，默认None (不保存)
        """
        check_is_fitted(self,attributes=['_fitted'])
        
        filtered_df_y = df_y[(df_y.index>=self.begin_date)&(df_y.index<=self.end_date)]
        
        # self.flag 的列名应为 PRODUCT_flag 格式
        # 过滤 self.flag 的日期，使其与 filtered_df_y 的日期对齐
        common_index = filtered_df_y.index.intersection(self.flag.index)
        filtered_flag = self.flag.loc[common_index]
        
        # 从 self.product_list (干净的产品名列表) 中筛选出在 filtered_flag 中实际存在的信号
        products_to_calculate = []
        for p_clean in self.product_list:
            print(p_clean)
            if f"{p_clean}" in filtered_flag.columns:
                products_to_calculate.append(f"{p_clean}")
        
        if not products_to_calculate:
            warnings.warn(f"Strategy '{self.name}': No common products with signals found for the given date range. Report generation skipped.")
            self._df_ret_all = pd.DataFrame()
            self._df_ret_long = pd.DataFrame()
            self._df_ret_short = pd.DataFrame()
            self.df_pnl = pd.DataFrame()
            self._dict = {}
            self.clean_product_list = []
            return
        
        # 计算总体、多头和空头的收益
        self._df_ret_all,self._df_ret_long,self._df_ret_short = calculate_returns_all(
            df_x=filtered_flag, # 应包含 PRODUCT_flag 列
            df_y=filtered_df_y,
            product_list=products_to_calculate, # 干净的产品名列表
            cost=self.cost
        )

        # calculate_returns_all 返回的 DataFrame 列名是干净的产品名
        self.clean_product_list = list(self._df_ret_all.columns)
        
        # 计算绩效指标
        self.df_pnl,self._dict = cal_metric(
            df_all=self._df_ret_all,
            df_long=self._df_ret_long,
            df_short=self._df_ret_short
        )
            
    def report_html(self,df_y,fold = 24,path = None):
        """
        为每个产品生成交互式HTML格式的回测报告和可视化结果
        
        参数:
        df_y (DataFrame): 价格数据，index为datetime，columns为品种名称
        fold (int): 周期收益分析的周期数，默认24 (此参数在此方法中未直接使用，但保持接口一致性)
        path (str): 结果保存路径的根目录，默认None (不保存，直接Jupyter显示)
        """
        check_is_fitted(self,attributes=['_fitted'])
        df_y_filtered = df_y[(df_y.index>=self.begin_date)&(df_y.index<=self.end_date)]
        
        # self.flag 的列名应为 PRODUCT_flag 格式, 按日期过滤
        common_index_flag = df_y_filtered.index.intersection(self.flag.index)
        actual_flag_df_filtered_by_date = self.flag.loc[common_index_flag]

        # 使用 self.product_list (干净品种名列表) 进行迭代
        for product_name in tqdm(self.product_list, desc=f"Generating reports for {self.name}"):
            price_series_product = df_y_filtered.get(product_name)
            raw_signal_series_product = self.df_x_input.get(product_name) 
            turnover_series_product = None
            if self.df_amt_input is not None:
                turnover_series_product = self.df_amt_input.get(product_name)
            
            expected_signal_col_in_flag = f"{product_name}_flag" # 例如 "AP_flag"

            if price_series_product is None:
                warnings.warn(f"Price data for {product_name} not found. Skipping this product for HTML report.")
                continue
            
            if expected_signal_col_in_flag not in actual_flag_df_filtered_by_date.columns:
                warnings.warn(f"Processed signal column '{expected_signal_col_in_flag}' not found for product {product_name} in self.flag. Skipping this product for HTML report.")
                continue
            
            signal_series_product = actual_flag_df_filtered_by_date[expected_signal_col_in_flag]

            if raw_signal_series_product is None:
                warnings.warn(f"Raw strategy signal data for {product_name} not found in df_x_input. Plotting without raw signal.")

            if turnover_series_product is None and self.df_amt_input is not None:
                 warnings.warn(f"Turnover data (df_amt) for {product_name} not found. Plotting without turnover information.")

            # 数据格式处理 (确保为 Series)
            if isinstance(price_series_product, pd.DataFrame):
                price_series_product = price_series_product.squeeze() if price_series_product.shape[1] == 1 else price_series_product.iloc[:, 0]
            if isinstance(signal_series_product, pd.DataFrame):
                signal_series_product = signal_series_product.squeeze() if signal_series_product.shape[1] == 1 else signal_series_product.iloc[:,0]
            if raw_signal_series_product is not None and isinstance(raw_signal_series_product, pd.DataFrame):
                raw_signal_series_product = raw_signal_series_product.squeeze() if raw_signal_series_product.shape[1] == 1 else raw_signal_series_product.iloc[:,0]
            if turnover_series_product is not None and isinstance(turnover_series_product, pd.DataFrame):
                turnover_series_product = turnover_series_product.squeeze() if turnover_series_product.shape[1] == 1 else turnover_series_product.iloc[:,0]

            # 为单个产品计算日收益 (all, long, short)
            # df_x_single_product 需要包含带 _flag 后缀的列名
            df_x_single_product = pd.DataFrame({expected_signal_col_in_flag: signal_series_product})
            df_y_single_product = pd.DataFrame({product_name: price_series_product})

            df_ret_all_prod, df_ret_long_prod, df_ret_short_prod = calculate_returns_all(
                df_x=df_x_single_product, 
                df_y=df_y_single_product, 
                product_list=[product_name], # 干净的产品名
                cost=self.cost
            )
            
            df_pnl_product, metrics_product = cal_metric(
                df_all=df_ret_all_prod, 
                df_long=df_ret_long_prod, 
                df_short=df_ret_short_prod
            )
            
            df_pnl_product = df_pnl_product.rename(columns={
                'return_all': 'all_pnl',
                'return_long': 'long_pnl',
                'return_short': 'short_pnl'
            })

            product_output_dir = None
            if path:
                product_output_dir = os.path.join(path, "result", self.name, product_name)
                os.makedirs(product_output_dir, exist_ok=True)

            generate_report_for_product(
                product_name=product_name,
                df_price_product_series=price_series_product,
                df_signal_product_series=signal_series_product, # 这是处理后的信号 (0,1,-1)
                df_raw_signal_product_series=raw_signal_series_product, # 这是原始输入信号
                df_turnover_product_series=turnover_series_product,
                df_cumulative_pnl_for_this_product=df_pnl_product,
                metrics_for_this_product=metrics_product,
                strategy_name_overall=self.name,
                output_dir_for_product_charts=product_output_dir
            )
        
        print(f"HTML reports generation for all products of strategy '{self.name}' completed.")
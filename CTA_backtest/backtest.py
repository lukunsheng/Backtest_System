import pandas as pd  
import numpy as np 
import os 
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决保存图像是负号'-'显示为方块的问题
import seaborn as sns
import warnings
from tqdm import tqdm
from .CTA_BC.preprocess._plot import _plot_pnl            # 导入绘图函数
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
        self.df_x_input = None # Initialize to store raw strategy signals
        self.df_amt_input = None # Initialize to store df_amt if provided
        self._fitted = False # Moved initialization here for clarity
        
    def fit(self,df_x,product_list,name,begin_date = '2018-01-01',end_date = '2024-08-04',cost = 0,mode = 'trade_ori',ratio = 1,df_amt = None,amt_threshold = 20 * 1e8):
        """
        执行回测主函数
        
        参数:
        df_x (DataFrame): 策略信号数据，index为datetime，columns为品种名称
        product_list (list): 要回测的品种列表
        name (str): 策略名称
        begin_date (str): 回测开始日期，默认'2018-01-01'
        end_date (str): 回测结束日期，默认'2024-08-04'
        cost (float): 交易成本，默认0
        mode (str): 交易模式，可选'trade_ori'/'trade_factor_mean'/'trade_ori_amtclean'等
        ratio (float): 信号比例调整因子，默认1
        df_amt (DataFrame): 成交量数据，仅在需要考虑成交量的模式下使用
        amt_threshold (float): 成交量阈值，仅在需要考虑成交量的模式下使用
        """
        self.df_x_input = df_x.copy() # Store the original df_x for raw signal plotting
        if df_amt is not None:
            self.df_amt_input = df_amt.copy() # Store df_amt if provided
        else:
            self.df_amt_input = None
        _df_x = df_x.sort_index()  # 按时间排序
        self.product_list = product_list  # 保存品种列表
        self.name = name  # 保存策略名称
        self.cost = cost  # 保存交易成本
        self.begin_date = begin_date  # 保存开始日期
        self.end_date = end_date  # 保存结束日期
        # 生成交易信号
        self.flag = create_trade_flag(df = _df_x,product_list = product_list,begin_date = begin_date,end_date = end_date,mode = mode,ratio = ratio,df_amt = df_amt,amt_threshold = amt_threshold)
        self._fitted = True  # 标记已执行回测

    def report(self,df_y,fold = 24,path = None):
        """
        生成回测报告和可视化结果
        
        参数:
        df_y (DataFrame): 价格数据，index为datetime，columns为品种名称
        fold (int): 周期收益分析的周期数，默认24
        path (str): 结果保存路径，默认None (不保存)
        """
        check_is_fitted(self,attributes=['_fitted'])  # 检查是否已执行回测
        df_y = df_y[(df_y.index>=self.begin_date)&(df_y.index<=self.end_date)]  # 筛选日期范围内的价格数据
        self.clean_product_list = [i.split('_')[0] for i in self.flag.columns]  # 获取干净的品种列表
        # 计算总体、多头和空头的收益
        self._df_ret_all,self._df_ret_long,self._df_ret_short = calculate_returns_all(df_x = self.flag,df_y = df_y,product_list = self.clean_product_list,cost = self.cost)
        self.clean_product_list = [i.split('_')[0] for i in self._df_ret_all.columns]  # 更新品种列表
        # 计算不同周期的收益分布
        self.df_fold = calculate_returns_folds(df_x = self.flag,df_y = df_y,product_list = self.clean_product_list,fold = fold)
        # 计算绩效指标
        self.df_pnl,self._dict = cal_metric(df_all = self._df_ret_all,df_long = self._df_ret_long,df_short = self._df_ret_short)
        # 绘制PnL曲线和收益分布图
        _plot_pnl(df = self.df_pnl,_dict = self._dict,df_fold = self.df_fold,name = self.name,path = path)
        
    def report_html(self,df_y,fold = 24,path = None):
        """
        为每个产品生成交互式HTML格式的回测报告和可视化结果
        
        参数:
        df_y (DataFrame): 价格数据，index为datetime，columns为品种名称
        fold (int): 周期收益分析的周期数，默认24
        path (str): 结果保存路径的根目录，默认None (不保存，直接Jupyter显示)
        """
        check_is_fitted(self,attributes=['_fitted'])
        df_y_filtered = df_y[(df_y.index>=self.begin_date)&(df_y.index<=self.end_date)]

        # 使用 self.product_list，它应该是在 fit 方法中保存的干净品种名列表
        for product_name in tqdm(self.product_list, desc=f"Generating reports for {self.name}"):
            # 1. 准备该产品的数据
            price_series_product = df_y_filtered.get(product_name)
            raw_signal_series_product = self.df_x_input.get(product_name) 
            turnover_series_product = None # Default to None
            if self.df_amt_input is not None:
                turnover_series_product = self.df_amt_input.get(product_name)
            
            if product_name in self.flag.columns:
                signal_col_name = product_name
            else:
                warnings.warn(f"Signal column for {product_name} (tried {product_name}_flag and {product_name}) not found in self.flag. Skipping this product.")
                continue
            
            signal_series_product = self.flag[signal_col_name]

            if price_series_product is None:
                warnings.warn(f"Price data for {product_name} not found. Skipping this product.")
                continue
            
            if raw_signal_series_product is None:
                warnings.warn(f"Raw strategy signal data for {product_name} not found in df_x_input. Plotting without raw signal.")

            if turnover_series_product is None and self.df_amt_input is not None:
                 warnings.warn(f"Turnover data (df_amt) for {product_name} not found. Plotting without turnover information.")

            # 确保是Series
            if isinstance(price_series_product, pd.DataFrame):
                if price_series_product.shape[1] == 1:
                    price_series_product = price_series_product.squeeze()
                else:
                    warnings.warn(f"Price data for {product_name} has multiple columns. Taking the first one. Please verify.")
                    price_series_product = price_series_product.iloc[:, 0]

            if isinstance(signal_series_product, pd.DataFrame):
                if signal_series_product.shape[1] == 1:
                    signal_series_product = signal_series_product.squeeze()
                else:
                     warnings.warn(f"Signal data for {product_name} has multiple columns. Taking the first one. Please verify.")
                     signal_series_product = signal_series_product.iloc[:,0]

            if raw_signal_series_product is not None and isinstance(raw_signal_series_product, pd.DataFrame):
                if raw_signal_series_product.shape[1] == 1:
                    raw_signal_series_product = raw_signal_series_product.squeeze()
                else:
                    warnings.warn(f"Raw signal data for {product_name} has multiple columns. Taking the first one. Please verify.")
                    raw_signal_series_product = raw_signal_series_product.iloc[:,0]

            if turnover_series_product is not None and isinstance(turnover_series_product, pd.DataFrame):
                if turnover_series_product.shape[1] == 1:
                    turnover_series_product = turnover_series_product.squeeze()
                else:
                    warnings.warn(f"Turnover data for {product_name} has multiple columns. Taking the first one. Please verify.")
                    turnover_series_product = turnover_series_product.iloc[:,0]


            # a. 为单个产品计算日收益 (all, long, short)
            # 创建符合 calculate_returns_all 期望的输入 DataFrame
            # 信号DataFrame，列名需要与 calculate_returns_all 中 product_list 参数对应（即不带_flag）
            # 但 calculate_returns_all 内部会查找 df_x[{product}_flag]
            # 所以 df_x 的列名应该是 "ProductA_flag" 等
            df_x_single_product = pd.DataFrame({signal_col_name: signal_series_product}) 
            
            # 价格DataFrame，列名是干净的产品名
            df_y_single_product = pd.DataFrame({product_name: price_series_product})

            # 调用 calculate_returns_all，传入的 product_list 是干净的产品名
            # calculate_returns_all 会在 df_x_single_product 中查找 product_name + "_flag"
            df_ret_all_prod, df_ret_long_prod, df_ret_short_prod = calculate_returns_all(
                df_x=df_x_single_product, 
                df_y=df_y_single_product, 
                product_list=[product_name], # 传入干净的产品名
                cost=self.cost
            )
            
            # b. 为单个产品计算累计PNL和指标
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

            # c. 确定输出路径 (如果需要)
            product_output_dir = None
            if path:
                product_output_dir = os.path.join(path, "result", self.name, product_name)
                os.makedirs(product_output_dir, exist_ok=True)

            # 2. 为该产品生成并保存/显示三个图表
            generate_report_for_product(
                product_name=product_name,
                df_price_product_series=price_series_product,
                df_signal_product_series=signal_series_product,
                df_raw_signal_product_series=raw_signal_series_product,
                df_turnover_product_series=turnover_series_product,
                df_cumulative_pnl_for_this_product=df_pnl_product,
                metrics_for_this_product=metrics_product,
                strategy_name_overall=self.name,
                output_dir_for_product_charts=product_output_dir
            )
        
        print(f"HTML reports generation for all products of strategy '{self.name}' completed.")
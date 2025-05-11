# CTA_backtest 量化交易回测框架

## 1. 项目简介

CTA_backtest 是一个专为商品交易顾问(Commodity Trading Advisor)策略设计的量化回测框架，支持多品种、多周期的策略信号回测、绩效评估和结果可视化。该框架集成了信号生成、回测执行、绩效评估和结果可视化等完整功能链，适合量化研究员和策略开发者快速验证和评估交易策略的有效性。

### 主要特点

- **多品种支持**：内置大量期货品种，支持同时回测多个市场品种
- **灵活的信号生成**：提供多种交易信号生成方式，也可自定义交易信号
- **全面的绩效评估**：计算胜率、盈亏比、平均收益等多种绩效指标
- **直观的结果可视化**：自动生成PnL曲线和收益分布图表
- **周期收益分析**：支持细分不同周期的收益贡献分析

## 2. 项目结构

```
CTA_backtest/
│
├── backtest.py                # 回测主类，核心入口
├── CTA_BC/
│   ├── metrics/               # 绩效指标与收益率计算
│   │   ├── cal_indicator.py   # 绩效指标统计（胜率、盈亏比等）
│   │   ├── cal_return.py      # 收益率计算（总收益、多空收益等）
│   │   └── __init__.py
│   ├── preprocess/            # 数据预处理与可视化
│   │   ├── _plot.py           # 回测结果绘图（PnL曲线、收益分布等）
│   │   ├── _utils.py          # 辅助功能（品种列表、品种分组等）
│   │   └── __init__.py
│   ├── trade/                 # 交易信号生成
│   │   ├── trade_boll.py      # 各种交易信号生成方法
│   │   └── __init__.py
│   └── __init__.py
└── __init__.py
```

## 3. 模块功能详解

### 3.1 BackTest 类 (backtest.py)

BackTest 类是整个框架的核心，集成了从信号生成到结果可视化的全流程。

**主要方法**：

- **fit**：接收信号数据，设置回测参数，生成交易标志
  ```python
  fit(df_x, product_list, name, begin_date, end_date, cost, mode, ratio, df_amt, amt_threshold)
  ```
  
- **report**：计算绩效指标，生成回测报告和可视化结果
  ```python
  report(df_y, fold, path)
  ```

**参数说明**：

| 参数名 | 说明 | 类型 | 默认值 |
|--------|------|------|--------|
| df_x | 策略信号数据 | DataFrame | - |
| product_list | 要回测的品种列表 | list | - |
| name | 策略名称 | str | - |
| begin_date | 回测开始日期 | str | '2018-01-01' |
| end_date | 回测结束日期 | str | '2024-08-04' |
| cost | 交易成本 | float | 0 |
| mode | 交易模式 | str | 'trade_ori' |
| ratio | 信号比例 | float | 1 |
| df_amt | 成交量数据 | DataFrame | None |
| amt_threshold | 成交量阈值 | float | 20 * 1e8 |
| fold | 周期收益分析的周期数 | int | 24 |
| path | 结果保存路径 | str | None |

### 3.2 交易信号生成 (CTA_BC/trade/)

trade_boll.py 提供了多种交易信号生成方法，可以根据不同需求选择。

**主要函数**：

- **trade_ori**：基础交易信号生成，根据信号强度开平仓
- **trade_factor_mean**：因子均值化后的信号生成
- **trade_ori_amtclean**：考虑成交量的交易信号生成
- **trade_factor_mean_amtclean**：考虑成交量的因子均值化信号生成
- **create_trade_flag**：根据选定模式创建交易标志

### 3.3 收益率计算 (CTA_BC/metrics/cal_return.py)

**主要函数**：

- **calculate_returns**：计算单个品种的交易收益
- **calculate_returns_all**：计算多品种的总体收益，返回多空收益分别统计
- **calculate_returns_folds**：计算不同周期的收益分布

### 3.4 绩效指标 (CTA_BC/metrics/cal_indicator.py)

**cal_metric 函数**：计算全面的绩效指标，包括：

- 胜率：总体、多头、空头
- 盈亏比：总体、多头、空头
- 平均收益：总体、多头、空头
- 交易次数：总体、多头、空头（含日均统计）
- 总利润：总体、多头、空头

### 3.5 结果可视化 (CTA_BC/preprocess/_plot.py)

**主要函数**：

- **_plot_pnl**：绘制整体PnL曲线和收益分布图
- **_plot_pnl_product**：绘制单个品种的PnL曲线和收益分布图

### 3.6 辅助工具 (CTA_BC/preprocess/_utils.py)

- **get_clean_product**：获取可交易的品种列表
- **get_group_product**：获取按类别分组的品种字典

## 4. 使用指南

### 4.1 安装依赖

```bash
pip install pandas numpy matplotlib seaborn tqdm scikit-learn
```

### 4.2 基础用法

```python
import pandas as pd
from backtest import BackTest

# 加载数据
df_x = pd.read_csv('your_factor_signal.csv', index_col=0, parse_dates=True)
df_y = pd.read_csv('your_price_data.csv', index_col=0, parse_dates=True)

# 选择品种
from CTA_BC.preprocess._utils import get_clean_product
product_list = get_clean_product()  # 或者自定义品种列表，如 ['CU', 'AL', 'ZN']

# 初始化并执行回测
bt = BackTest()
bt.fit(
    df_x=df_x,
    product_list=product_list,
    name='my_strategy',
    begin_date='2018-01-01',
    end_date='2024-08-04',
    cost=0.0005,  # 设置交易成本
    mode='trade_ori'  # 选择信号生成模式
)

# 生成报告
bt.report(
    df_y=df_y,
    fold=24,  # 分析24个周期的收益
    path='./'  # 结果保存路径
)
```

### 4.3 进阶用法

#### 考虑成交量的回测

```python
import pandas as pd
from backtest import BackTest

# 加载数据
df_x = pd.read_csv('your_factor_signal.csv', index_col=0, parse_dates=True)
df_y = pd.read_csv('your_price_data.csv', index_col=0, parse_dates=True)
df_amt = pd.read_csv('your_volume_data.csv', index_col=0, parse_dates=True)  # 成交量数据

# 初始化并执行回测
bt = BackTest()
bt.fit(
    df_x=df_x,
    product_list=['CU', 'AL', 'ZN'],
    name='volume_strategy',
    begin_date='2018-01-01',
    end_date='2024-08-04',
    cost=0.0005,
    mode='trade_ori_amtclean',  # 使用考虑成交量的模式
    df_amt=df_amt,  # 传入成交量数据
    amt_threshold=15 * 1e8  # 设置成交量阈值
)

# 生成报告
bt.report(df_y=df_y, fold=24, path='./')
```

#### 按品种分组回测

```python
import pandas as pd
from backtest import BackTest
from CTA_BC.preprocess._utils import get_group_product

# 加载数据
df_x = pd.read_csv('your_factor_signal.csv', index_col=0, parse_dates=True)
df_y = pd.read_csv('your_price_data.csv', index_col=0, parse_dates=True)

# 按分组回测
product_dict = get_group_product()
for group_name, group_products in product_dict.items():
    bt = BackTest()
    bt.fit(
        df_x=df_x,
        product_list=group_products,
        name=f'strategy_{group_name}',
        begin_date='2018-01-01',
        end_date='2024-08-04',
        cost=0.0005
    )
    bt.report(df_y=df_y, fold=24, path=f'./results/{group_name}')
```

## 5. 回测结果解读

回测完成后，系统会生成以下内容：

1. **PnL曲线图**：展示总体、多头和空头随时间的累计收益变化
2. **周期收益分布图**：展示不同周期的收益贡献分布
3. **绩效指标统计**：展示在图表中，包括：
   - 总利润/多头利润/空头利润
   - 交易次数及日均交易次数
   - 盈亏比和胜率
   - 平均收益率

### 关键指标解读：

- **胜率**：成功交易占总交易的比例，越高越好
- **盈亏比**：平均盈利交易额与平均亏损交易额之比，越高越好
- **平均利润**：每笔交易的平均收益率，以‰（千分之一）显示
- **周期收益分布**：展示策略在不同持仓周期的收益分布情况，帮助分析最佳持仓周期

## 6. 常见问题

### 6.1 数据格式要求

- **df_x**（信号数据）：
  - index为datetime格式
  - columns为品种名称
  - 值为信号强度

- **df_y**（价格数据）：
  - index为datetime格式
  - columns为品种名称
  - 值为价格

- **df_amt**（成交量数据，可选）：
  - index为datetime格式
  - columns为品种名称
  - 值为成交量

### 6.2 品种命名规则

系统内置的品种列表遵循大写字母命名，如'CU'（铜）、'AL'（铝）等，使用自定义品种时应保持一致的命名规则。

### 6.3 信号生成模式选择指南

- **trade_ori**：适用于基础信号回测，不考虑额外条件
- **trade_factor_mean**：适用于需要去除信号均值影响的情况
- **trade_ori_amtclean**：适用于需要考虑成交量的基础信号回测
- **trade_factor_mean_amtclean**：适用于既需要去除信号均值影响又需要考虑成交量的情况

## 7. 自定义扩展

### 7.1 添加新的交易信号生成方法

可以在`CTA_BC/trade/trade_boll.py`中添加新的信号生成函数，并在`create_trade_flag`函数中添加对应的处理逻辑。

### 7.2 添加新的绩效指标

可以在`CTA_BC/metrics/cal_indicator.py`的`cal_metric`函数中添加新的指标计算。

### 7.3 自定义结果可视化

可以修改`CTA_BC/preprocess/_plot.py`中的绘图函数，添加或修改可视化内容。

## 8. 联系方式

如有问题或建议，欢迎联系作者或提交issue。 
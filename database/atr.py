import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np

# --- 1. 用户配置 (请根据您的实际情况修改) ---
MYSQL_USER = 'root'  # 例如 'root'
MYSQL_PASSWORD = '' # 您的 MySQL 密码
MYSQL_HOST = 'localhost'  # 如果 MySQL 在本机，通常是 'localhost' 或 '127.0.0.1'
MYSQL_PORT = '3306'       # MySQL 默认端口
DATABASE_NAME = 'futures_data' # 您在 MySQL 中创建的数据库名
TABLE_NAME_OPEN = 'open'  # 存储 open 数据的表名
TABLE_NAME_HIGH = 'high'  # 存储 high 数据的表名
TABLE_NAME_LOW = 'low'    # 存储 low 数据的表名
TABLE_NAME_CLOSE = 'close' # 存储 close 数据的表名
ATR_TABLE_NAME = 'atr'    # 存储 ATR 结果的表名
ATR_PERIOD = 14                 # ATR 周期，默认为 14

# --- 2. 创建 SQLAlchemy 引擎 ---
try:
    engine_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{DATABASE_NAME}"
    engine = create_engine(engine_url)
    # 测试连接
    with engine.connect() as connection:
        print(f"成功连接到 MySQL 数据库 '{DATABASE_NAME}'!")
except Exception as e:
    print(f"连接 MySQL 时发生错误: {e}")
    print("请检查：")
    print("1. MySQL 服务是否正在运行。")
    print("2. 用户名、密码、主机、端口是否正确。")
    print(f"3. 数据库 '{DATABASE_NAME}' 是否已创建。如果未创建，请先在 MySQL 中执行 'CREATE DATABASE {DATABASE_NAME};'")
    exit()

# --- 3. 从数据库读取数据 ---
def get_data(table_name):
    try:
        query = f"SELECT * FROM {table_name} ORDER BY datetime"
        df = pd.read_sql(query, con=engine, parse_dates=['datetime'])
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        print(f"读取表 {table_name} 时发生错误: {e}")
        return None

# --- 4. 计算 ATR ---
def calculate_atr(df_open, df_high, df_low, df_close, period=14):
    # 初始化 ATR DataFrame
    atr_df = pd.DataFrame(index=df_close.index)
    
    # 遍历每个品种列
    for column in df_close.columns:
        # 获取当前品种的 OHLC 数据
        open_series = df_open[column]
        high_series = df_high[column]
        low_series = df_low[column]
        close_series = df_close[column]
        
        # 计算真实波幅（True Range）
        prev_close = close_series.shift(1)
        high_minus_low = high_series - low_series
        high_minus_prev_close = (high_series - prev_close).abs()
        low_minus_prev_close = (low_series - prev_close).abs()
        true_range = pd.concat([high_minus_low, high_minus_prev_close, low_minus_prev_close], axis=1).max(axis=1)
        
        # 计算 ATR
        atr = true_range.rolling(window=period).mean()
        
        # 将 ATR 添加到结果 DataFrame
        atr_df[column] = atr
    
    return atr_df

# --- 5. 示例：计算并写回 ATR ---
def calculate_and_store_atr():
    try:
        # 读取 OHLC 数据
        df_open = get_data(TABLE_NAME_OPEN)
        df_high = get_data(TABLE_NAME_HIGH)
        df_low = get_data(TABLE_NAME_LOW)
        df_close = get_data(TABLE_NAME_CLOSE)
        
        if df_open is None or df_high is None or df_low is None or df_close is None:
            print("读取 OHLC 数据失败，无法计算 ATR。")
            return
        
        # 计算 ATR
        atr_df = calculate_atr(df_open, df_high, df_low, df_close, ATR_PERIOD)
        
        # 将 ATR 写回数据库
        atr_df.to_sql(name=ATR_TABLE_NAME, con=engine, if_exists='replace', index=True, index_label='datetime')
        print(f"ATR 已成功计算并存储到表 {ATR_TABLE_NAME}")
        
    except Exception as e:
        print(f"计算或写入 ATR 时发生错误: {e}")

if __name__ == "__main__":
    calculate_and_store_atr()
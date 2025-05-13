import pandas as pd
from sqlalchemy import create_engine
import os

# --- 1. 用户配置 (请根据您的实际情况修改) ---
H5_FILE_PATH = r'D:\Files\WORKING\WorkSpace\Xtech\data\BackTest_BaseData_5min.h5'

# MySQL 连接信息 (请务必替换为您的真实凭据)
MYSQL_USER = 'root'  # 例如 'root'
MYSQL_PASSWORD = '' # 您的 MySQL 密码
MYSQL_HOST = 'localhost'  # 如果 MySQL 在本机，通常是 'localhost' 或 '127.0.0.1'
MYSQL_PORT = '3306'       # MySQL 默认端口
DATABASE_NAME = 'futures_data' # 您在 MySQL 中创建的数据库名
MYSQL_TABLE_NAME = 'volume'  # 目标表名

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

# --- 3. 从 HDF5 读取数据并整合 ---
try:
    # 获取所有品种的键名
    with pd.HDFStore(H5_FILE_PATH, 'r') as store:
        product_keys = store.keys()
        if not product_keys:
            print(f"在 HDF5 文件中没有找到数据: {H5_FILE_PATH}")
            exit()

        # 初始化空的宽表
        df_wide = pd.DataFrame()

        for key in product_keys:
            product_code = key.strip('/').lower()

            # 读取该品种的数据到 DataFrame
            df = store[key]

            # 确保 'datetime' 是索引，并转换为标准时间格式
            df.index = pd.to_datetime(df.index)
            df.index.name = 'datetime'

            # 提取 close 列，并重命名为品种代码
            close_series = df['volume'].rename(product_code)

            # 合并到宽表中，自动对齐时间
            df_wide = df_wide.join(close_series, how='outer')

        # 查看结果
        print(f"整合后的宽表数据：")
        print(df_wide.head())

except FileNotFoundError:
    print(f"错误: HDF5 文件未找到路径 {H5_FILE_PATH}")
except Exception as e:
    print(f"访问 HDF5 文件时发生错误: {e}")
    exit()

# --- 4. 写入 MySQL ---
try:
    print(f"正在将宽表写入 MySQL 表 '{MYSQL_TABLE_NAME}'...")

    # 写入 SQL 表，将索引 (datetime) 作为列保存
    df_wide.to_sql(
        name=MYSQL_TABLE_NAME,
        con=engine,
        if_exists='replace',  # 如果表存在，则替换
        index=True,
        index_label='datetime'
    )

    print(f"数据已成功写入 MySQL 表 '{MYSQL_TABLE_NAME}'。")

except Exception as e:
    print(f"写入 MySQL 时发生错误: {e}")
    exit()
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- 1. 用户配置 (请根据您的实际情况修改) ---
H5_FILE_PATH = r'D:\Files\WORKING\WorkSpace\Xtech\data\BackTest_BaseData_5min.h5'

# MySQL 连接信息 (请务必替换为您的真实凭据)
MYSQL_USER = 'root'  # 例如 'root'
MYSQL_PASSWORD = '' # 您的 MySQL 密码
MYSQL_HOST = 'localhost'  # 如果 MySQL 在本机，通常是 'localhost' 或 '127.0.0.1'
MYSQL_PORT = '3306'       # MySQL 默认端口
DATABASE_NAME = 'futures_data' # 您在 MySQL 中创建的数据库名

# --- 2. 创建 SQLAlchemy 引擎 ---
# 引擎的连接字符串格式: "mysql+pymysql://user:password@host:port/database_name"
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

# --- 3. 从 HDF5 读取数据并写入 MySQL ---
try:
    with pd.HDFStore(H5_FILE_PATH, 'r') as store:
        product_keys = store.keys()  # 获取 HDF5 文件中的所有 key (例如 ['/RB', '/CU', ...])

        if not product_keys:
            print(f"在 HDF5 文件中没有找到数据: {H5_FILE_PATH}")
        else:
            print(f"在 HDF5 文件中找到以下品种: {product_keys}")

        for key in product_keys:
            product_code = key.strip('/')  # 例如 '/RB' -> 'RB'
            
            # 将品种代码用作表名 (建议使用小写，并确保是合法的 SQL 表名)
            # 您可以根据需要调整表名生成逻辑
            table_name = product_code.lower() 
            # 例如，如果您想让表名更具描述性，可以是 f"{product_code.lower()}_5min"
            
            print(f"\n正在处理品种: {product_code} (将存入表: {table_name})")

            try:
                df = store[key]  # 读取该品种的数据到 DataFrame

                # 确保 'datetime' 索引是 Pandas DatetimeIndex 类型
                df.index = pd.to_datetime(df.index)
                
                # 给索引命名，这样 to_sql 会使用这个名字作为 SQL 中的列名
                if df.index.name is None:
                    df.index.name = 'datetime'

                # 观察到您提供的示例数据最后几行 twap, vwap, volume, amount 数值异常
                # 这里仅作提示，实际迁移会按原样迁移。建议您检查源数据质量。
                if 'amount' in df.columns and (df['amount'] < -0.001).any(): # 允许微小负数，但大的负数可能异常
                    print(f"  警告: 品种 {product_code} 的 'amount' 列中存在负值，请关注数据质量。")
                if 'volume' in df.columns and (df['volume'] < -0.001).any():
                     print(f"  警告: 品种 {product_code} 的 'volume' 列中存在负值，请关注数据质量。")

                print(f"  正在将 {product_code} 的数据写入 MySQL 表 '{table_name}'...")
                
                # 将 DataFrame 写入 SQL 表
                # if_exists='replace': 如果表已存在，则删除重建。请谨慎使用，会丢失原有数据。
                #                  可选值: 'fail' (如果表存在则报错), 'append' (追加数据)
                df.to_sql(name=table_name,
                          con=engine,
                          if_exists='replace', 
                          index=True,          # 将 DataFrame 的索引写入为列
                          index_label='datetime',# 指定索引列在 SQL 表中的名称
                          chunksize=10000)      # 可选: 分块写入，对大数据量有帮助

                print(f"  数据已写入。正在为表 '{table_name}' 的 'datetime' 列设置主键...")

                # 将 'datetime' 列设置为主键
                with engine.connect() as connection:
                    try:
                        # 使用反引号 ` ` 来包裹表名和列名，以防它们是 SQL 关键字或包含特殊字符
                        connection.execute(text(f"ALTER TABLE `{table_name}` ADD PRIMARY KEY (`datetime`);"))
                        connection.commit() # 提交 DDL (数据定义语言) 更改
                        print(f"  已为表 '{table_name}' 设置主键。")
                    except Exception as pk_e:
                        print(f"  警告: 未能为表 '{table_name}' 设置主键。错误信息: {pk_e}")
                        print(f"  表 '{table_name}' 已创建，但 'datetime' 列可能未被设置为主键。")
                        print(f"  您可能需要检查 'datetime' 列的数据类型是否适合作为主键，或手动设置。")
                
                print(f"  品种 {product_code} 处理完成。")

            except Exception as e_product:
                print(f"  处理品种 {product_code} 时发生错误: {e_product}")
                # 可以选择跳过这个品种继续处理下一个
                continue 

except FileNotFoundError:
    print(f"错误: HDF5 文件未找到路径 {H5_FILE_PATH}")
except Exception as e_h5:
    print(f"访问 HDF5 文件时发生错误: {e_h5}")

print("\n数据迁移过程结束。")
print("现在您可以从 MySQL 中查询数据了。例如，如果 HDF5 中有 'RB' 品种:")
print("SELECT * FROM rb WHERE datetime >= '2020-01-02 09:00:00' AND datetime < '2020-01-02 10:00:00';")

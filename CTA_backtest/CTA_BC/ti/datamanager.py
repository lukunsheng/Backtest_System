import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from sqlalchemy import create_engine

class DataManager:
    def __init__(self, user='root', password='', host='localhost', port=3306, db='futures_data'):
        """
        初始化数据管理器，使用SQLAlchemy连接数据库
        """
        self.connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
        self.engine = create_engine(self.connection_string)
        self._cache = {}
        
    def get_data(self, table_name: str, products: Union[str, List[str]], 
                 start_date: str, end_date: str) -> pd.DataFrame:
        """
        从数据库获取数据
        """
        cache_key = f"{table_name}_{','.join(products) if isinstance(products, list) else products}_{start_date}_{end_date}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if isinstance(products, str):
            products = [products]
        
        # 构建查询
        columns = ['datetime'] + products
        columns_str = ', '.join(columns)
        query = f"""
        SELECT {columns_str} FROM {table_name}
        WHERE datetime BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY datetime
        """
        
        try:
            # 使用SQLAlchemy引擎执行查询
            data = pd.read_sql(query, self.engine, index_col='datetime', parse_dates=['datetime'])
            self._cache[cache_key] = data
            return data
        except Exception as e:
            print(f"数据查询错误: {e}")
            # 返回空DataFrame，保持列结构
            empty_df = pd.DataFrame(columns=products)
            empty_df.index.name = 'datetime'
            return empty_df
    
    def get_close(self, products: Union[str, List[str]], 
                  start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_data('close', products, start_date, end_date)
    
    def get_open(self, products: Union[str, List[str]], 
                start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_data('open', products, start_date, end_date)
    
    def get_high(self, products: Union[str, List[str]], 
                start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_data('high', products, start_date, end_date)
    
    def get_low(self, products: Union[str, List[str]], 
               start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_data('low', products, start_date, end_date)
    
    def get_volume(self, products: Union[str, List[str]], 
                  start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_data('volume', products, start_date, end_date)
    
    def get_ohlc(self, products: Union[str, List[str]], 
                start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取OHLC数据
        """
        return {
            'open': self.get_open(products, start_date, end_date),
            'high': self.get_high(products, start_date, end_date),
            'low': self.get_low(products, start_date, end_date),
            'close': self.get_close(products, start_date, end_date)
        }
    
    def clear_cache(self):
        """
        清除缓存
        """
        self._cache = {} 
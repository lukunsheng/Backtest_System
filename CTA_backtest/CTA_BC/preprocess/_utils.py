def get_clean_product():
   """
   获取可交易的品种列表
   
   返回:
   product_list (list): 包含所有可交易期货品种代码的列表
   """
   product_list = ['CJ',  'SP',  'NR',  'P',  'BU',  'CU',  'AO',  'V',  'FG',  'L',  'UR',  'CF',  'IF',  'SM',  'RR',  'SC',  'PF',  'TL',  'IH',  'JM',  'EC',  'AU','C',  
                'AG',  'RS',  'MA',  'PG',  'RM',  'T',  'LH',  'SH',  'RU',  'CS','TA',  'IC',  'EB',  'SR',  'FU',  'CY',  'TF',  'SS',  'ZC',  'TS',  'SF','AP',
                'I',  'SN',  'WH',  'OI',  'ZN',  'B',  'Y',  'IM',  'LC',  'SA',  'M',  'RB',  'PX',  'EG',  'PP',  'AL',  'J',  'JD',  'LU',  'NI',  'HC',  'A',  'PK'] 
   return product_list

def get_group_product():
   """
   获取按类别分组的品种字典
   
   返回:
   product_dict (dict): 品种分组字典，键为分组名称，值为该分组下的品种代码列表
   
   分组说明:
   - 农产品: 油脂油料和农产品
   - 化工和能源: 化工品和能源类产品
   - 金属: 有色金属和贵金属
   - 股指: 股指期货
   - 债券: 国债期货
   - 黑色系: 钢铁、煤炭等黑色金属
   """
   product_dict = {'农产品': ['OI', 'B', 'RM', 'P', 'M', 'Y'],
                   '化工和能源': ['PG','L','EB','EG','BU','LU','PP','V','PF','MA','FU','PX','SC','TA'],
                   '金属': ['ZN', 'CU', 'AL', 'BC', 'SN'],
                   '股指': ['IC', 'IH', 'IF', 'IM'],
                   '债券': ['TS', 'TL', 'T', 'TF'],
                   '黑色系': ['HC', 'JM', 'I', 'J', 'RB']}
   return product_dict

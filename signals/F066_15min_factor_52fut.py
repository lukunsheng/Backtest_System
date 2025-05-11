from __future__ import division
import datetime
import sys
sys.path.append('../')
import numpy as np
from Factor_template import Factor_template



class Factor(Factor_template):
    """
    signal 因子类
    主要功能：
    1、构建期货策略单因子
    """                            
    def adjust_market_data(self,market_data_column,market_data):
        """
        主要功能：
        1、调整行情数据
        """                              
        #把夜盘数据去掉
        barTime = market_data_column.index('barTime')      
        market_data = market_data[(market_data[:,barTime]>='08:00')&(market_data[:,barTime]<='22:45'),:]#筛选数组，保留第5列满足条件的行                  
        return market_data    
    
    def calculate_signal(self,):
        """
        主要功能：
        1、自行计算信号，继承模板后重写该函数
        2、信号计算后保存在self.singal
        """                                    
        for future_code in self.futurePool:
            # print('正在处理',future_code)
            # =============================================================================
            '''获取行情数据的数据'''
            # =============================================================================
            (market_data_column,market_data)=self.read_market_data('15min',future_code)
            # =============================================================================
            '''初始化信号(根据你获取的行情序列)'''
            # =============================================================================              
            (signal,market_data_column,market_data) = self.initialize_signal(future_code, market_data_column,market_data)
            # =============================================================================
            '''初始化指标列'''
            # =============================================================================
            (KDJ0Idx,market_data_column,market_data) = self.add_market_data_column(future_code,'KDJ_0',np.nan,market_data_column,market_data)
            (KDJ1Idx,market_data_column,market_data) = self.add_market_data_column(future_code,'KDJ_1',50,market_data_column,market_data)
            (KDJ2Idx,market_data_column,market_data) = self.add_market_data_column(future_code,'KDJ_2',50,market_data_column,market_data)
            (KDJ3Idx,market_data_column,market_data) = self.add_market_data_column(future_code,'KDJ_3',np.nan,market_data_column,market_data)
            # =============================================================================
            '''获取所需的字段索引'''
            # =============================================================================
            hfq_openPrice = market_data_column.index('hfq_openPrice')
            hfq_closePrice = market_data_column.index('hfq_closePrice')
            hfq_highPrice = market_data_column.index('hfq_highPrice')
            hfq_lowPrice = market_data_column.index('hfq_lowPrice')                    
            # =============================================================================
            '''计算信号'''
            # =============================================================================
            Len = 300
            f = 200
            beta = 1.2

            kdjLen = Len
            std_len = f
            window = max([Len,f]) + 1


            for i in range(window,market_data.shape[0]):
                market_data[i,signal] =  market_data[i-1,signal]
                KDJ_0 = market_data[:,KDJ0Idx]
                KDJ_1 = market_data[:,KDJ1Idx]
                KDJ_2 = market_data[:,KDJ2Idx]
                KDJ_3 = market_data[:,KDJ3Idx]

                # 计算KDJ
                KDJ_0[i] = 100 * (market_data[i-1,hfq_closePrice] - np.min(market_data[i-kdjLen:i,hfq_lowPrice])) / (np.max(market_data[i-kdjLen:i,hfq_highPrice])-np.min(market_data[i-kdjLen:i,hfq_lowPrice]))
                KDJ_1[i] = (2 / 3) * KDJ_1[i-1] + KDJ_0[i] * 1 / 3
                KDJ_2[i] = (2 / 3) * KDJ_2[i-1] + KDJ_1[i] * 1 / 3
                KDJ_3[i] = 3 * KDJ_1[i] - 2 * KDJ_2[i]

                k = KDJ_1[i]
                j = KDJ_3[i]
                if j>90 and k>80:
                    market_data[i,signal] = 1
                elif j<10 and k<20:
                    market_data[i,signal] = -1


                if np.std(market_data[i - std_len:i, hfq_closePrice],ddof=1) / market_data[i - 1, hfq_closePrice] >beta/100:
                    market_data[i,signal] = 0

                market_data[i, KDJ0Idx] = KDJ_0[i]
                market_data[i, KDJ1Idx] = KDJ_1[i]
                market_data[i, KDJ2Idx] = KDJ_2[i]
                market_data[i, KDJ3Idx] = KDJ_3[i]

            market_data[:,signal][market_data[:,signal]>1] = 1
            market_data[:,signal][market_data[:,signal]<-1] = -1
            # =============================================================================
            '''保存信号'''
            # =============================================================================
            #如果有想额外添加到信号中展示的列，可以在这里添加
            self.add_extra_column_to_signal_df(['KDJ_0','KDJ_1','KDJ_2','KDJ_3'])
            self.signal[future_code] = market_data[:,[market_data_column.index(i) for i in self.signal_df_column]]

                           
def factor_config():
    factor_config={
        #因子名称
        'factor_name':'F066_15min_factor_52fut',
        #因子描述
        'factor_description':'066号因子-趋势-15min-KDJ-52个品种',
        #品种池
        'futurePool': [
            #油脂油料
            'A_main','B_main','M_main','Y_main','RM_main','OI_main','P_main',
            #农产品
            'CF_main','SR_main','JD_main','CS_main','C_main','AP_main','CJ_main','LH_main','PK_main',
            #金属
            'AG_main','AU_main','CU_main','AL_main','ZN_main','PB_main','NI_main','SN_main',
            #黑色
            'RB_main','HC_main','J_main','JM_main','I_main', 'SM_main','SF_main','SS_main',
            #化工
            'PP_main','L_main','V_main','TA_main','PF_main','MA_main','RU_main','NR_main','BU_main','EG_main','FG_main','UR_main','EB_main','SA_main','SP_main',
            #能源
            'SC_main','FU_main','ZC_main','LU_main','PG_main',
            ],    # 52个品种

        # 'futurePool': [
        #     # 油脂油料
        #     'A_main', 'M_main', 'Y_main', 'RM_main', 'OI_main', 'P_main',
        #     # 农产品
        #     'CF_main', 'SR_main', 'JD_main', 'CS_main', 'C_main', 'AP_main',
        #     # 金属
        #     'AG_main', 'AU_main', 'CU_main', 'AL_main', 'ZN_main', 'PB_main', 'NI_main',
        #     # 黑色
        #     'RB_main', 'HC_main', 'J_main', 'JM_main', 'I_main',
        #     # 化工
        #     'PP_main', 'L_main', 'V_main', 'TA_main', 'MA_main', 'RU_main', 'BU_main', 'EG_main', 'FG_main', 'SP_main',
        #     # 能源
        #     'SC_main', 'FU_main', 'ZC_main',
        # ],  # 37个品种

        #交易周期
        'cycle':'15min',
        #增量计算所需要的最少行情数量
        'incremental_calculation_rows':301,
        }
    return factor_config        
    
if __name__ == '__main__':    
    # import time
    # start_time = time.process_time()
    # print('------开始时间:',datetime.datetime.now().time())

    factor=Factor(factor_config())
    factor.calculate_signal()

    # print('------结束时间:',datetime.datetime.now().time())
    # end_time = time.process_time()
    # cost_time = end_time-start_time
    # print('耗时：',cost_time)

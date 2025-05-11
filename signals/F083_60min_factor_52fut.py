from __future__ import division
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
            # =============================================================================
            '''获取行情数据的数据'''
            # =============================================================================
            (market_data_column,market_data)=self.read_market_data('60min',future_code)
            # =============================================================================
            '''初始化信号(根据你获取的行情序列)'''
            # =============================================================================              
            (signal,market_data_column,market_data) = self.initialize_signal(future_code, market_data_column,market_data)     
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
            Len = 200
            c = 1.6
            cmean = 1 / 500
            pre = 5

            ATRLen = Len-1
            window = Len


            for i in range(window,market_data.shape[0]):
                market_data[i,signal] =  market_data[i-1,signal]

                closem = np.mean(market_data[i-Len:i,hfq_closePrice])
                openm = np.mean(market_data[i-1-pre:i,hfq_openPrice])
                open = market_data[i-1,hfq_openPrice]

                # 计算ATR
                ATR = np.mean(np.max(np.array([(market_data[i-ATRLen:i,hfq_highPrice] - market_data[i-ATRLen:i,hfq_lowPrice]),
                                               (market_data[i-ATRLen:i,hfq_highPrice] - market_data[i-1-ATRLen:i-1,hfq_closePrice]),
                                               (market_data[i-1-ATRLen:i-1,hfq_closePrice] - market_data[i-ATRLen:i,hfq_lowPrice])]),axis=0))

                if closem > open+c*ATR or openm > open+c*ATR:
                    market_data[i,signal] = -cmean * (np.mean(market_data[i-pre-1:i,hfq_closePrice])) / (np.mean(market_data[i-Len:i-1,hfq_highPrice])-np.mean(market_data[i-Len:i-1,hfq_lowPrice]))
                elif closem < open-c*ATR or openm < open-c*ATR:
                    market_data[i,signal] = cmean * (np.mean(market_data[i-pre-1:i,hfq_closePrice])) / (np.mean(market_data[i-Len:i-1,hfq_highPrice])-np.mean(market_data[i-Len:i-1,hfq_lowPrice]))

                if np.std(market_data[i - Len:i, hfq_closePrice],ddof=1) / open > 0.015:
                    market_data[i,signal] = 0


            market_data[:,signal][market_data[:,signal]>1] = 1
            market_data[:,signal][market_data[:,signal]<-1] = -1
            # =============================================================================
            '''保存信号'''
            # =============================================================================
            #如果有想额外添加到信号中展示的列，可以在这里添加
            #self.add_extra_column_to_signal_df()
            self.signal[future_code] = market_data[:,[market_data_column.index(i) for i in self.signal_df_column]]

                           
def factor_config():
    factor_config={
        #因子名称
        'factor_name':'F083_60min_factor_52fut',
        #因子描述
        'factor_description':'083号因子-趋势-60min-均线突破-52个品种',
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

        #交易周期
        'cycle':'60min',
        #增量计算所需要的最少行情数量
        'incremental_calculation_rows':200,
        }
    return factor_config        
    
if __name__ == '__main__':    
    factor=Factor(factor_config())     
    factor.calculate_signal()

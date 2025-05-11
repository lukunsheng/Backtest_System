from __future__ import division
import datetime
import sys
sys.path.append('../')
import numpy as np
import pandas as pd
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


        #60min数据对应11:00和13:30合成为1根
        hfq_highPrice = market_data_column.index('hfq_highPrice')
        hfq_lowPrice = market_data_column.index('hfq_lowPrice')
        hfq_closePrice = market_data_column.index('hfq_closePrice')

        for i_1100 in np.where(market_data[:,barTime] == '11:00')[0]:
            if i_1100+1 == len(market_data):
                continue
            if market_data[i_1100 + 1, barTime] != '13:30':
                continue
            market_data[i_1100,hfq_highPrice] = max(market_data[i_1100+1,hfq_highPrice],market_data[i_1100,hfq_highPrice])
            market_data[i_1100,hfq_lowPrice] = min(market_data[i_1100+1,hfq_lowPrice],market_data[i_1100,hfq_lowPrice])
            market_data[i_1100,hfq_closePrice] = market_data[i_1100+1,hfq_closePrice]

        market_data = market_data[(market_data[:,barTime]!='13:30'),:]#删除13:30的那根bar

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
            '''60min数据特殊处理：合并11:00和13:00两根k线【只处理了OHLC】'''
            # =============================================================================
            (market_data_column,market_data)=self.read_market_data('60min',future_code)
            # =============================================================================
            '''初始化信号(根据你获取的行情序列)'''
            # =============================================================================              
            (signal,market_data_column,market_data) = self.initialize_signal(future_code, market_data_column,market_data)     
            # =============================================================================
            '''初始化指标列'''
            # =============================================================================
            (posIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'position',-1,market_data_column,market_data)
            (posPriceIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'position_price',0,market_data_column,market_data)
            # =============================================================================
            '''获取所需的字段索引'''
            # =============================================================================
            hfq_openPrice = market_data_column.index('hfq_openPrice')
            hfq_closePrice = market_data_column.index('hfq_closePrice')
            hfq_highPrice = market_data_column.index('hfq_highPrice')
            hfq_lowPrice = market_data_column.index('hfq_lowPrice')
            Vol = market_data_column.index('turnoverVol')
            # =============================================================================
            '''计算信号'''
            # =============================================================================
            Len1 = 71
            a = 2.9
            p = 2.1
            b = 0.9

            atr_len = Len1-1
            window = Len1


            for i in range(window,market_data.shape[0]):
                market_data[i,signal] =  market_data[i-1,signal]
                position = market_data[i-1,posIdx]
                position_price = market_data[i-1,posPriceIdx]

                Mid = np.mean(market_data[i-window:i,hfq_closePrice])
                Upline = Mid + p*np.std(market_data[i - window:i, hfq_closePrice],ddof=0)
                Downline = Mid - p*np.std(market_data[i - window:i, hfq_closePrice],ddof=0)

                # 计算ATR
                ATR = np.mean(np.max(np.array([(market_data[i-atr_len:i,hfq_highPrice] - market_data[i-atr_len:i,hfq_lowPrice]),
                                               np.abs(market_data[i-atr_len:i,hfq_highPrice] - market_data[i-1-atr_len:i-1,hfq_closePrice]),
                                               np.abs(market_data[i-1-atr_len:i-1,hfq_closePrice] - market_data[i-atr_len:i,hfq_lowPrice])]),axis=0))

                # 上穿做多
                if position == 0 and market_data[i-1,hfq_closePrice]>Upline and ATR/market_data[i-1,hfq_closePrice] < 0.006:
                    position= 1
                    position_price = market_data[i-1,hfq_closePrice]
                # 下穿做空
                elif position == 0 and market_data[i-1,hfq_closePrice]<Downline and ATR/market_data[i-1,hfq_closePrice] < 0.006:
                    position = -1
                    position_price = market_data[i-1,hfq_closePrice]
                # 空头移动波动止损
                elif position == -1:
                    if market_data[i-1,hfq_closePrice] - position_price > a * ATR:
                        position = 0
                        position_price = 0
                    elif market_data[i-1,hfq_closePrice] < position_price:
                        position_price = market_data[i-1,hfq_closePrice]
                # 空头移动波动止损
                elif position == 1:
                    if market_data[i-1,hfq_closePrice] - position_price < -a * ATR:
                        position = 0
                        position_price = 0
                    elif market_data[i-1,hfq_closePrice] > position_price:
                        position_price = market_data[i-1,hfq_closePrice]

                market_data[i,signal] = position * 0.02 * market_data[i-1,hfq_closePrice]/(max(market_data[i-window:i,hfq_highPrice]) - min(market_data[i-window:i,hfq_lowPrice]))

                market_data[i, posIdx] = position
                market_data[i, posPriceIdx] = position_price

            market_data[:,signal][market_data[:,signal]>1] = 1
            market_data[:,signal][market_data[:,signal]<-1] = -1
            # =============================================================================
            '''保存信号'''
            # =============================================================================
            #如果有想额外添加到信号中展示的列，可以在这里添加
            self.add_extra_column_to_signal_df(['position','position_price'])
            self.signal[future_code] = market_data[:,[market_data_column.index(i) for i in self.signal_df_column]]

                           
def factor_config():
    factor_config={
        #因子名称
        'factor_name':'F099_60min_factor_52fut',
        #因子描述
        'factor_description':'099号因子-趋势-60min-布林线-52个品种',
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
        'incremental_calculation_rows':71,
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

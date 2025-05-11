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
            # ----------【！！！回测截取特定时间段，否则会用全样本数据计算信号，极其耗时，但上传跟盘系统时需要去掉此代码！！！】
            # market_data = market_data[(market_data[:,0]>'2014-01-01') & (market_data[:,0]<'2019-07-01'),:] # 【样本内】
            # =============================================================================
            '''初始化信号(根据你获取的行情序列)'''
            # =============================================================================              
            (signal,market_data_column,market_data) = self.initialize_signal(future_code, market_data_column,market_data)     
            # =============================================================================
            '''初始化指标列'''
            # =============================================================================
            (entryPriceIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'EntryPrice',np.nan,market_data_column,market_data)
            (stdEntryFlagIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'stdEntryFlag',np.nan,market_data_column,market_data)
            (coverFlagIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'CoverFlag',np.nan,market_data_column,market_data)
            (mktPosVirtualIdx,market_data_column,market_data) = self.add_market_data_column(future_code,'mktPosVirtual',0,market_data_column,market_data)
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
            maLen = 178
            std_len = 40
            stdRatio = 1.25
            SLfactor = 3.98
            rsi_len = 27
            RSILimit = 47
            k = 410

            ATRLen = std_len
            window = max([maLen,rsi_len, std_len]) + 1


            for i in range(window,market_data.shape[0]):
                market_data[i,signal] =  market_data[i-1,signal]
                EntryPrice = market_data[i-1,entryPriceIdx]
                stdEntryFlag= market_data[i-1,stdEntryFlagIdx]
                CoverFlag = market_data[i-1,coverFlagIdx]
                mktPosVirtual= market_data[i-1,mktPosVirtualIdx]

                # 计算boll【左开右闭，计算出来的指标没有使用当前k线数据】
                boll_len = window
                mid = np.mean(market_data[i-boll_len:i,hfq_closePrice])
                up = mid + 2*np.std(market_data[i - boll_len:i, hfq_closePrice],ddof=1)
                down = mid - 2*np.std(market_data[i - boll_len:i, hfq_closePrice],ddof=1)

                # 计算rsi
                diff_val = np.diff(market_data[i - rsi_len:i, hfq_closePrice])
                A = np.sum(diff_val[diff_val > 0])
                B = -1 * np.sum(diff_val[diff_val < 0])
                if A+B == 0:
                    rsi = np.nan
                else:
                    rsi = A / (A + B) * 100

                # 计算ATR
                ATR = np.mean(np.max(np.array([(market_data[i-ATRLen:i,hfq_highPrice] - market_data[i-ATRLen:i,hfq_lowPrice]),
                                               (market_data[i-ATRLen:i,hfq_highPrice] - market_data[i-1-ATRLen:i-1,hfq_closePrice]),
                                               (market_data[i-1-ATRLen:i-1,hfq_closePrice] - market_data[i-ATRLen:i,hfq_lowPrice])]),axis=0))
                lotsBS = market_data[i-1,hfq_closePrice] / (k * ATR)
                lotsBB = ATR / market_data[i-1,hfq_closePrice] * k / 3


                # 开仓
                std_val = np.std(market_data[i - std_len:i, hfq_closePrice],ddof=0) / market_data[i-1, hfq_closePrice]
                if std_val < stdRatio/100:
                    if market_data[i-1,hfq_closePrice]>up and mktPosVirtual<=0 and rsi>RSILimit:
                        mktPosVirtual = lotsBS
                        market_data[i,signal] = 0
                        EntryPrice = market_data[i-1,hfq_closePrice]
                        stdEntryFlag = 0
                        CoverFlag = 23
                    elif market_data[i-1,hfq_closePrice]<down and mktPosVirtual>=0 and rsi<RSILimit:
                        mktPosVirtual = -lotsBS
                        market_data[i,signal] = 0
                        EntryPrice = market_data[i-1,hfq_closePrice]
                        stdEntryFlag = 0
                        CoverFlag = 23

                # 平仓
                if stdEntryFlag != 1:
                    if mktPosVirtual >0 and market_data[i-1,hfq_closePrice]<mid:
                        mktPosVirtual = 0
                        CoverFlag = 1
                    elif mktPosVirtual <0 and market_data[i-1,hfq_closePrice]>mid:
                        mktPosVirtual = 0
                        CoverFlag = 1


                if std_val > stdRatio/100 and stdEntryFlag != 1:
                    if mktPosVirtual > 0:
                        mktPosVirtual = 0
                        market_data[i,signal] = -lotsBB
                        CoverFlag = 2
                        stdEntryFlag = 1
                        EntryPrice = market_data[i-1,hfq_closePrice]
                    elif mktPosVirtual < 0:
                        mktPosVirtual = 0
                        market_data[i,signal] = lotsBB
                        CoverFlag = 2
                        stdEntryFlag = 1
                        EntryPrice = market_data[i-1,hfq_closePrice]

                if stdEntryFlag == 1:
                    if market_data[i,signal] >0 and market_data[i-1,hfq_closePrice]>mid:
                        market_data[i,signal] = 0
                        stdEntryFlag = 0
                        CoverFlag = 21
                    elif market_data[i,signal] <0 and market_data[i-1,hfq_closePrice]<mid:
                        market_data[i,signal] = 0
                        stdEntryFlag = 0
                        CoverFlag = 21

                if stdEntryFlag == 1:
                    if market_data[i-1,hfq_closePrice] <= EntryPrice - SLfactor / 100 * market_data[i-1,hfq_closePrice] and market_data[i,signal] > 0:
                        market_data[i,signal] = 0
                        stdEntryFlag = 0
                        CoverFlag = 22

                    if market_data[i-1,hfq_closePrice] >= EntryPrice + SLfactor / 100 * market_data[i-1,hfq_closePrice] and market_data[i,signal] < 0:
                        market_data[i,signal] = 0
                        stdEntryFlag = 0
                        CoverFlag = 22


                market_data[i, entryPriceIdx] = EntryPrice
                market_data[i, stdEntryFlagIdx] = stdEntryFlag
                market_data[i, coverFlagIdx] = CoverFlag
                market_data[i, mktPosVirtualIdx] = mktPosVirtual

            market_data[:,signal][market_data[:,signal]>1] = 1
            market_data[:,signal][market_data[:,signal]<-1] = -1
            # =============================================================================
            '''保存信号'''
            # =============================================================================
            #如果有想额外添加到信号中展示的列，可以在这里添加
            self.add_extra_column_to_signal_df(['EntryPrice','stdEntryFlag','CoverFlag','mktPosVirtual'])
            self.signal[future_code] = market_data[:,[market_data_column.index(i) for i in self.signal_df_column]]

                           
def factor_config():
    factor_config={
        #因子名称
        'factor_name':'RevP01_15min_factor_Filt_6NewFut',
        #因子描述
        'factor_description':'纯反转-01号因子-15min-布林带-筛选6个新品种',
        #品种池
        'futurePool': [
            'B_main','PG_main','NR_main','LU_main','SS_main','PK_main',
            ],    # 6个品种

        #交易周期
        'cycle':'15min',
        #增量计算所需要的最少行情数量
        'incremental_calculation_rows':179,
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

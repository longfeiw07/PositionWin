# -*- coding: utf-8 -*-

from gmsdk.api import StrategyBase
import logging
import logging.config

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from matplotlib.pylab import date2num
import datetime
import time

'''
Steps:
    1.实时更新打印：计算仓位和开收盘价，实时打印
        实时行情模式或模拟行情模式
        主类中增加私有变量，保存Bar数据和仓位数据
        onBar中更新数据，做下单判断
        开始前要准备好当天已经出来的数据
    2.实时更新画图：画出仓位变化图和K线图
    3.K线合并，画出K线图和合并后的K线图
    4.给出买卖点建议
    5.回测（回测不画图）
    6.添加多只期货
'''


class Mystrategy(StrategyBase):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        super(Mystrategy, self).__init__(*args, **kwargs)

        self.postitionTrend = pd.DataFrame() #保存持仓数据，总共5列：date,time,symbol,longPosition,shortPosition
        self.dailyBar=pd.DataFrame()        #保存Bar数据
        self.combindBar=pd.DataFrame()      #合并后的数据
        self.pltConfig=plt.figure(1) #创建一个公共画布，用来画走势图和K线图

        #准备好数据和画布
        self.dataPrepare(self)
        self.pltPrepare(self)

    def on_login(self):
        pass

    def on_error(self, code, msg):
        pass

    def on_bar(self, bar):

        self.dataUpdate(self,bar)
        self.pltUpdate(self)
        pass

    #开始运行时，准备好数据，主要是把当天的数据加载到缓存中
    def dataPrepare(self):
        #先处理时间，判断当前时间是否在当天晚上21点到24点之间，如果是，start time为当天21点，如果不是，start time为前一天21天
        #end time为当前时间
        cTime = time.strftime("%H:%M:%S")
        cDate = time.strftime("%Y-%m-%d")
        print cTime
        if (cDate + ' ' + cTime) > (cDate + ' 21:00:00'):
            startTime = cDate + " 21:00:00"
            endTime = cDate + ' ' + cTime
        else:
            startTime = str(datetime.date.today() - datetime.timedelta(days=1)) + " 21:00:00"
            endTime = cDate + ' ' + cTime
        #取数并装入缓存中
        bars = self.get_bars(self.subscribe_symbols, 180, startTime, endTime)
        databuf=[]
        i = 0
        k1 = 0
        kk1 = 0
        kkk1 = 0
        k2 = 0
        kk2 = 0
        qq = 0
        do = 0
        ko = 0
        lastposition = 0
        lastdo = 0
        lastko = 0
        for b in bars:
            if i > 0:
                qq = b.position - lastposition  # 计算QQ的值
                if b.close > b.open and qq >= 0:  # 计算K1的值
                    k1 = qq
                else:
                    k1 = 0
                if b.close < b.open and qq < 0:  # 计算KK1的值
                    kk1 = qq
                else:
                    kk1 = 0
                if b.close == b.open:  # 计算KKK1的值
                    kkk1 = qq / 2
                else:
                    kkk1 = 0
                if b.close < b.open and qq >= 0:
                    k2 = qq
                else:
                    k2 = 0
                if b.close > b.open and qq < 0:
                    kk2 = qq
                else:
                    kk2 = 0
                do = k1 + kk1 + kkk1 + lastdo
                ko = k2 + kk2 + kkk1 + lastko
            databuf.append([i, b.strtime, b.open, b.high, b.low, b.close, b.position, k1, kk1, kkk1, k2, kk2, do, ko])
            self.dailyBar.append(b)
            self.combineBar(self,b)
            i += 1
            lastposition = b.position
            lastdo = do
            lastko = ko
        self.postitionTrend = pd.DataFrame(databuf, columns=['index', 'start_time', 'open', 'high', 'low', 'close', 'position', 'k1', 'kk1',
                                         'kkk1', 'k2', 'kk2', 'do', 'ko'])
        self.logger.info("data prepared")
        pass

    #将Bar数据更新到缓存positionTrend，dailyBar和combinedBar中
    def dataUpdate(self,b):
        rownum=pd.nrow(self.postitionTrend)
        if rownum<1:
            databuf=[1,b.strtime,b.open,b.high,b.low,b.close,b.position,0,0,0,0,0,0,0]
        else:
            lastposition=self.postitionTrend.iloc[rownum,'position']
            lastdo=self.postitionTrend.iloc[rownum,'do']
            lastko=self.postitionTrend.iloc[rownum,'kl']
            qq=b.postion-lastposition
            if b.close > b.open and qq >= 0:  # 计算K1的值
                k1 = qq
            else:
                k1 = 0
            if b.close < b.open and qq < 0:  # 计算KK1的值
                kk1 = qq
            else:
                kk1 = 0
            if b.close == b.open:  # 计算KKK1的值
                kkk1 = qq / 2
            else:
                kkk1 = 0
            if b.close < b.open and qq >= 0:
                k2 = qq
            else:
                k2 = 0
            if b.close > b.open and qq < 0:
                kk2 = qq
            else:
                kk2 = 0
            do = k1 + kk1 + kkk1 + lastdo
            ko = k2 + kk2 + kkk1 + lastko
            databuf=[rownum+1,b.strtime, b.open, b.high, b.low, b.close, b.position, k1, kk1, kkk1, k2, kk2, do, ko]
        self.postitionTrend.append(databuf)
        self.combineBar(self,b)
        pass

    # 合并K线
    def combineBar(self, bar):
        pass

    #准备好画布，分成1列3行，第一个为原始K线，第二个为合并后的K线，第三个为仓位走势图
    #准备好之后，如果数据不为空，则将已有数据画出
    def pltPrepare(self):

        self.pltUpdate()
        self.logger.info("plot prepared")
        pass

    #更新画布，在on_Bar()中调用，每次数据更新后更新画图；在pltPrepare()中调用，画布准备好之后，把已有数据画出来
    def pltUpdate(self):
        pass

if __name__ == '__main__':
    myStrategy = Mystrategy(
        username='-',
        password='-',
        strategy_id='3ac57fd6-818b-11e7-8296-0019860005e9',
        subscribe_symbols='SHFE.rb1801.bar.60',
        mode=3,
        td_addr='127.0.0.1:8001'
    )
    ret = myStrategy.run()
    print('exit code: ', ret)
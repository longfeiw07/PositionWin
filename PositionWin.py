# -*- coding: utf-8 -*-
import sys
from gmsdk.api import StrategyBase
#from gmsdk.gm import Bar
import logging
import logging.config
import Bar
import PlotPositionWin as pc
import pandas as pd
import numpy as np
#import matplotlib
#matplotlib.use("WXAgg", warn=True)  # 这个要紧跟在 import matplotlib 之后，而且必须安装了 wxpython 2.8 才行。
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from matplotlib.pylab import date2num
import datetime
import time
import MAtest as ma
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
__color_lightsalmon__ = '#ffa07a'
__color_pink__ = '#ffc0cb'
__color_navy__ = '#000080'
__color_gold__ = '#FDDB05'
__color_gray30__ = '0.3'
__color_gray70__ = '0.7'
__color_lightblue__ = 'lightblue'

class Mystrategy(StrategyBase):

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        super(Mystrategy, self).__init__(*args, **kwargs)

        self.positionTrend = pd.DataFrame(columns=['strdatetime','utcdatetime', 'open', 'high', 'low', 'close', 'position', 'volume','do', 'ko','delta']) #保存持仓数据，总共5列：date,time,symbol,longPosition,shortPosition
        self.dailyBar=pd.DataFrame(columns=['strdatetime','utcdatetime','open','high','low','close','position','volume'])        #保存原始的1分钟Bar数据
        self.dailyBarMin=pd.DataFrame(columns=['strdatetime','utcdatetime','open','high','low','close','position','volume'])     #保存多分钟合并的Bar数据，分钟数由K_min确定
        self.combindBar =pd.DataFrame(columns=['strdatetime','utcdatetime','open','high','low','close','position','volume'])      #合并后的数据
        self.MACD=pd.DataFrame(columns=['strdatetime','utcdatetime','close','MACD','DEA','HIST','sema','lema'])
        self.KDJ=pd.DataFrame(columns=['strdatetime','utcdatetime','lowL','highL','RSV','KDJ_K','KDJ_D','KDJ_J'])
        self.K_trend=0 #当前的趋势，1表示上升，-1表示下降，初始为0
        self.marketFlag=0 #上一波行情标志，1为反弹上涨，-1为到顶下跌
        self.marketList = [] #用来保存每一次趋势的内容，包序号，x轴位置，时间，最高价，最低价，现价，类型
                            #{'index','xpos','time','phigh','plow','pnow','type'}
        self.trendList=[] #用来保存每一次趋势判断的情况
        self.trendPeriod=0 #距离上波行情经过了几根K线
        self.marketCount=0 #表示经过了几波行情
        self.tradeZoneHigh=0 #保存交易区间的上端点
        self.tradeZoneLow=0#保存交易区间的下端点，如果tradeZoneHige<=tradeZoneLow，表示当日没有非交易区间限制
        self.buyFlag=0#买卖标识，-1为卖，1为买

        #self.K_min=3 #采用多少分钟的K线，默认为3分钟，在on_bar中会判断并进行合并
        self.K_min=self.config.getint('para', 'K_min') or 3
        self.lastPositionDo= self.config.getfloat('para', 'lastPositionDo') or 0
        self.lastPositionKo= self.config.getfloat('para', 'lastPositionKo') or 0
        self.noticeMail=self.config.get('para','noticeMail')
        self.tradeStartHour=self.config.getint('para','tradeStartHour')
        self.tradeStartMin=self.config.getint('para','tradeStartMin')
        self.tradeEndHour=self.config.getint('para','tradeEndHour')
        self.tradeEndMin=self.config.getint('para','tradeEndMin')
        self.backwardDay=self.config.getint('para','backwardDay')

        self.K_minCounter=0 #用来计算当前是合并周期内的第几根K线，在onBar中做判断使用
        self.last_update_time=datetime.datetime.now() #保存上一次 bar更新的时间，用来帮助判断是否出现空帧

        self.exchange_id,self.sec_id,buf=self.subscribe_symbols.split('.',2)
        #准备好数据，回测模式下不用准备
        if self.mode != 4:self.dataPrepare()
        #self.pltPrepare()

    def on_login(self):
        pass

    def on_error(self, code, msg):
        pass

    def on_backtest_finish(self, indicator):
        self.positionTrend.to_csv("position"+'.csv', encoding='GB18030')
        pass

    def on_bar(self, bar):
        #实时只能取1分钟的K线，所以要先将1分钟线合并成多分钟K线，具体多少分钟由参数K_min定义
        #每次on_bar调用，先用数据保存到dailyBar中，再判断是否达到多分钟合并时间，是则进行合并，并执行一系列操作
        timenow=datetime.datetime.fromtimestamp(bar.utc_time)

        if timenow.hour==self.tradeStartHour and self.last_update_time.hour!=self.tradeStartHour:
            #每日晚上21点开盘时数据清零
            self.dataReset()

        #每日14：58分时，平掉所有持仓
        if timenow.hour==self.tradeEndHour and timenow.minute==self.tradeEndMin:
            self.closeAllPosition()
            #self.dailyBar.to_csv("dailyBar"+timenow.strftime("%Y%m%d")+'.csv',encoding='GB18030')
            #self.dailyBarMin.to_csv("dailyBarMin" + timenow.strftime("%Y%m%d") + '.csv', encoding='GB18030')
            #self.combindBar.to_csv("combindBar"+timenow.strftime("%Y%m%d")+'.csv',encoding='GB18030')
            print timenow.strftime("%Y%m%d")
            print self.tradeZoneHigh
            print self.tradeZoneLow
            #print '-------------------------------'
            #self.pltUpdate()

        minutesDelta=int((timenow-self.last_update_time).seconds)/60
        if 2<=minutesDelta<10:
            self.insertEmptyBar(minutesDelta)
        self.last_update_time=timenow
        #先保存bar数据
        rownum=self.update_dailyBar(bar)

        #barMin = int(bar.strtime[14:15])#取分钟数
        barMin=int(timenow.minute)
        if (barMin+1) % self.K_min==0 and self.K_minCounter>=self.K_min:
            self.update_dailyBarMin(bar)
            #self.pltUpdate('up')
            if self.combineBar() and self.mode!=4:self.pltUpdate()#更新combinedBar
            self.update_Position() #更新positionTrend,postion要使用dailyBarMin来计算，所以要在update_dailyBarMin后调用
            self.updateMACD()
            self.updateKDJ()
            #self.pltUpdate('down')#更新图片
            self.trendJudge()#趋势判断，在趋势判断中会给出buyFlag
            if self.buyFlag==1 :                             #买
                self.buyJudge(bar)
                self.buyFlag=0
            elif self.buyFlag==-1:                          #卖
                self.sellJudge(bar)
                self.buyFlag=0
        else:
            pass
        pass

    #开始运行时，准备好数据，主要是把当天的数据加载到缓存中
    def dataPrepare(self):
        '''
        20170919:增加backwardDay
        1、加载到当天开盘前的数据，合成dailyBarMin和position，计算MACD和KDJ，MACD和KDJ的计算方式采用一次性全部计算。
        2、如果是实盘模式，要清除数据缓存，然后再加载当天从开盘到当前时间的数据，计算判决数据，不触发下单。MACD和KDJ的计算方式采用单个计算
            `1、判断是回测模式还是实盘模式，回测模式下startTime为回测的starttime-backwardDay，endtime为回测模式的starttime
            2、实盘模式下starttime为timenow-backwardDay，endtime为当天的开盘时间
        :return:
        '''
        #先处理时间，判断当前时间是否在当天晚上21点到24点之间，如果是，start time为当天21点，如果不是，start time为前一天21天
        #end time为当前时间
        startTime = datetime.time(self.tradeEndHour, self.tradeStartMin, 0).strftime("%H:%M:%S")
        if self.mode==4:
            d, t = self.start_time.split(' ', 1)
            y, m, d = d.split('-', 2)
            d = datetime.date(int(y), int(m), int(d))
            startDate=(d-datetime.timedelta(days=self.backwardDay)).strftime("%Y-%m-%d")
            endTime=self.start_time
        else:
            startDate=(datetime.date.today()-datetime.timedelta(days=self.backwardDay)).strftime("%Y-%m-%d")
            endTime=datetime.date.today().strftime("%Y-%m-%d")+' '+startTime
        sT=startDate+' '+startTime
        bars = self.get_bars(self.exchange_id+'.'+self.sec_id, 60, sT, endTime)
        #这里数据只用来计算position,macd和kdj
        rownum=0
        for bar in bars:
            rownum = self.update_dailyBar(bar)
            if rownum % self.K_min == 0 and rownum >= self.K_min:
                self.update_dailyBarMin(bar)
                self.update_Position()  # 更新positionTrend
        self.prepareMACD()
        self.prepareKDJ()
        self.dataReset()
        #下面要再做实盘下当天数据的处理
        if self.mode==2:
            pass
        if rownum>0:
            self.last_update_time = datetime.datetime.fromtimestamp(self.dailyBar.ix[rownum-1,'utcdatetime'])
        print("------------------------data prepared-----------------------------")
#        self.dailyBar.to_csv('d:\dailyBar.csv', encoding='GB18030')
#        self.dailyBarMin.to_csv('d:\dailyBarMin.csv', encoding='GB18030')
#        self.positionTrend.to_csv('d:\positionTrend.csv', encoding='GB18030')
        pass

    def dataReset(self):
        '''
        在每个交易开始时（晚上21点），重置缓存数据，包括
        dailyBar，dailyBarMini，combinedBar,
        self.K_trend=0 #当前的趋势，1表示上升，-1表示下降，初始为0
        self.marketFlag=0 #上一波行情标志，1为反弹上涨，-1为到顶下跌
        self.marketList = [] #用来保存每一次趋势的内容，包序号，x轴位置，时间，最高价，最低价，现价，类型
                            #{'index','xpos','time','phigh','plow','pnow','type'}
        self.trendList=[] #用来保存每一次趋势判断的情况
        self.trendPeriod=0 #距离上波行情经过了几根K线
        self.marketCount=0 #表示经过了几波行情
        self.tradeZoneHigh=0 #保存交易区间的上端点
        self.tradeZoneLow=0#保存交易区间的下端点，如果tradeZoneHige<=tradeZoneLow，表示当日没有非交易区间限制
        self.buyFlag=0#买卖标识，-1为卖，1为买
        self.K_minCounter=0 #用来计算当前是合并周期内的第几根K线，在onBar中做判断使用

        positionTrend,MACD，KDJ的数据要保留
        :return:
        '''
        def cleanDf(df):
            row=df.shape[0]
            for i in range(row):
                df.drop(i,inplace=True)
        def cleanList(l):
            n=len(l)
            for i in range(n):
                del l[0]

        cleanDf(self.dailyBar)
        cleanDf(self.dailyBarMin)
        cleanDf(self.combindBar)
        self.K_trend=0
        self.marketFlag=0
        cleanList(self.marketList)
        cleanList(self.trendList)
        self.trendPeriod = 0  # 距离上波行情经过了几根K线
        self.marketCount = 0  # 表示经过了几波行情
        self.tradeZoneHigh = 0  # 保存交易区间的上端点
        self.tradeZoneLow = 0  # 保存交易区间的下端点，如果tradeZoneHige<=tradeZoneLow，表示当日没有非交易区间限制
        self.buyFlag = 0  # 买卖标识，-1为卖，1为买
        self.K_minCounter = 0  # 用来计算当前是合并周期内的第几根K线，在onBar中做判断使用

    def closeAllPosition(self):
        '''
        每日收盘前，平掉所有持仓
        :return:
        '''
        '''
        longP=self.get_position(self.exchange_id,self.sec_id,1)
        if longP and longP.volume>0:
            self.close_long(self.exchange_id,self.sec_id,0,longP.volume)
        shortP=self.get_position(self.exchange_id,self.sec_id,0)
        if shortP and shortP.volume>0:
            self.close_short(self.exchange_id,self.sec_id,0,shortP.volume)
        pass
        '''
        pl=self.get_positions()
        for p in pl:
            if p.side ==1:self.close_long(self.exchange_id,self.sec_id,0,p.volume)
            else: self.close_short(self.exchange_id,self.sec_id,0,p.volume)

    #将dailyBarMin数据更新到缓存positionTrend
    def update_Position(self):
        barrow=self.dailyBarMin.shape[0]
        strdatetime=self.dailyBarMin.ix[barrow-1,'strdatetime']
        utcdatetime=self.dailyBarMin.ix[barrow-1,'utcdatetime']
        open=self.dailyBarMin.ix[barrow-1,'open']
        high=self.dailyBarMin.ix[barrow-1,'high']
        low=self.dailyBarMin.ix[barrow-1,'low']
        close=self.dailyBarMin.ix[barrow-1,'close']
        position=self.dailyBarMin.ix[barrow-1,'position']
        volume=self.dailyBarMin.ix[barrow-1,'volume']

        rownum=self.positionTrend.shape[0] #row是从0开始算
        if rownum<1:
            databuf=[strdatetime,utcdatetime,open,high,low,close,position,volume,self.lastPositionDo,self.lastPositionKo]
        else:
            lastposition=self.positionTrend.ix[rownum-1,'position']
            lastdo=self.positionTrend.ix[rownum-1,'do']
            lastko=self.positionTrend.ix[rownum-1,'ko']
            qq=position-lastposition
            if close > open and qq >= 0:  # 计算K1的值
                k1 = qq
            else:
                k1 = 0
            if close < open and qq < 0:  # 计算KK1的值
                kk1 = qq
            else:
                kk1 = 0
            if close == open:  # 计算KKK1的值
                kkk1 = qq / 2
            else:
                kkk1 = 0
            if close < open and qq >= 0:
                k2 = qq
            else:
                k2 = 0
            if close > open and qq < 0:
                kk2 = qq
            else:
                kk2 = 0
            do = k1 + kk1 + kkk1 + lastdo
            ko = k2 + kk2 + kkk1 + lastko
            databuf=[strdatetime,utcdatetime, open, high, low, close, position, volume, do, ko]
#            print("position updated")
#            print databuf
        self.positionTrend.loc[rownum]=databuf
        pass

    #更新dailyBar
    def update_dailyBar(self,bar):
        rownum=self.dailyBar.shape[0]
        self.dailyBar.loc[rownum] =[bar.strtime,bar.utc_time, bar.open, bar.high, bar.low, bar.close, bar.position,bar.volume]
        self.K_minCounter+=1
#        print("dailyBar updated")
#        print self.dailyBar.loc[rownum]

        return rownum+1
        pass

    #更新dailyBarMin
    def update_dailyBarMin(self,bar):
        '''
        K线合并后，取第一根K线的时间作为合并后的K线时间
        :param bar:
        :return:
        '''
        rownum=self.dailyBar.shape[0]
        if rownum <self.K_min:return
        self.dailyBarMin.loc[self.dailyBarMin.shape[0]] = \
            [self.dailyBar.ix[rownum - self.K_min]['strdatetime'],
             self.dailyBar.ix[rownum - self.K_min]['utcdatetime'],
             self.dailyBar.ix[rownum - self.K_min]['open'],  # 取合并周期内第一条K线的开盘
             max(self.dailyBar.iloc[rownum - self.K_min:rownum]['high']),  # 合并周期内最高价
             min(self.dailyBar.iloc[rownum - self.K_min:rownum]['low']),  # 合并周期内的最低价
             bar.close,  # 最后一条K线的收盘价
             bar.position, # 最后一条K线的仓位值
             sum(self.dailyBar.iloc[rownum -self.K_min:rownum]['volume'])] #v1.2版本加入成交量数据
        self.K_minCounter=0
        #print("dailyBarMin updated")
        #print self.dailyBarMin.loc[rownum/self.K_min-1]
        pass

    # 合并K线，并做趋势判断
    #规则：
    #1.如果本K线上边比上根K线上边高
    #   1.1 如果下边比上根的下边高，则将K线加入趋势，不做合并，趋势判断为上升
    #   1.2 如果下边比上根的下边高，则将K线加入趋势，不做合并，趋势判断为上升
    # 2.如果本K线上边比上根K线的上边低
    #   2.1 如果下边比上根的下边高，则将Kxg并入上根K线，趋势判断为不变
    #   2.2 如果下边比上根的下边低，则将K线加入趋势，不做合并，趋势判断为下降
    def combineBar(self):
        #v如果dailyBarMin是第一根，则直接加入到combindBar中
        rownum=self.dailyBarMin.shape[0]
        if rownum==1:
            #databuf=self.dailyBarMin.iloc[0]
            self.combindBar.loc[0]=self.dailyBarMin.loc[0]
#            print self.dailyBarMin.loc[0]
#            print self.combindBar.loc[0]
            #self.combindBar.append(pd.Series(databuf))
            self.trendPeriod+=1
            return True
        rownum-=1#定位到最后一行
        crow=self.combindBar.shape[0]-1
        lastup=max(self.combindBar.ix[crow]['open'],self.combindBar.ix[crow]['close'])
        lastdown=min(self.combindBar.ix[crow]['open'],self.combindBar.ix[crow]['close'])
        currentup=max(self.dailyBarMin.ix[rownum]['open'],self.dailyBarMin.ix[rownum]['close'])
        currentdown = min(self.dailyBarMin.ix[rownum]['open'], self.dailyBarMin.ix[rownum]['close'])
        if currentup>lastup and currentdown>=lastdown:       #上边高的，趋势判定为上升
            self.combindBar.loc[self.combindBar.shape[0]]=self.dailyBarMin.iloc[-1]
            self.K_trend=1
            self.trendPeriod+=1
            self.trendList.append(self.K_trend)
        elif currentup>lastup and currentdown<lastdown:      #上边高，下边低，加入但趋势保持不变
            self.combindBar.loc[self.combindBar.shape[0]] = self.dailyBarMin.iloc[-1]
            self.trendPeriod+=1
            self.trendList.append(self.K_trend)
        elif currentdown<lastdown: #上边低，且下边低的，趋势判定为下降
            self.combindBar.loc[self.combindBar.shape[0]] = self.dailyBarMin.iloc[-1]
            self.K_trend=-1
            self.trendPeriod+=1
            self.trendList.append(self.K_trend)
        else:#上边低，且下边高的，合并（即不加入combindBar），趋势不变
             return False
        return True
        pass

    #行情判断
    #趋势是每根K线都做判断，行情是trendPeriod大于3才做判断
    #1.前3波行情不做判断
    #2.每次反转判断需要3根K线，每次反转判断使用的K线不能重叠
    #计算非交易区间：前三波行情价格段的重叠区间为非交易区间，行情价格在区间外才做交易，本函数用于计算交易区间
    #前3波K线（再加上起始点）共4个顶点，取两个下跌行情的低值和两个反弹行情的高值，两者区间为非交易区间
    #如果两者没有交集，则当天不设非交易区间
    #如果第一波行情为由上向下的下跌行情，即marketFlag=-1，则起始首根K线做为低点
    #如果第一波行情为由上向上的反弹行情，即marketFlag=1,则起始首根K线做为高点
    def trendJudge(self):
        if len(self.trendList)<2:return
        if self.trendList[-1]==self.trendList[-2]:return #趋势保持不变，没有行情
        if self.trendList[-1]==1 and self.trendList[-2]==-1:#出现反弹行情
            barrow = self.combindBar.shape[0]
            if self.marketCount==0:#第一波行情，起点做高点看
                self.tradeZoneHigh=self.combindBar.ix[0]['high']
                self.tradeZoneLow=self.combindBar.ix[barrow-2]['low']#取倒数第2根，即底点的最低值
                self.marketCount=1
            elif self.marketCount<3:
                self.tradeZoneLow=max(self.tradeZoneLow,self.combindBar.ix[barrow-2]['low'])
                self.trendPeriod=0
                self.marketCount+=1
            else:
                if self.trendPeriod < 3: return #前3波行情不做3根K线共用的限制，不加入trendPeriod的判断
                self.trendPeriod = 0
                self.marketCount += 1
                self.marketFlag = 1
                '''
                #做买操作，判断多仓是否连续三次增仓，或者空仓连续三次减仓
                if (self.positionTrend.ix[prow-1]['do']>self.positionTrend.ix[prow-2]['do'] and
                    self.positionTrend.ix[prow-2]['do']>self.positionTrend.ix[prow-3]['do']) or\
                    (self.positionTrend.ix[prow-1]['ko']<self.positionTrend.ix[prow-2]['ko'] and
                    self.positionTrend.ix[prow-2]['ko']<self.positionTrend.ix[prow-3]['ko']):
                    self.buyFlag=1
              '''
                #1.1版本，改为当前K线下多仓减空仓大于上一K线多仓减空仓
                self.buyFlag = 1
                pass
        elif self.trendList[-1]==-1 and self.trendList[-2]==1:#出现下跌行情
            barrow = self.combindBar.shape[0]
            if self.marketCount==0:#第一波行情，起点做低点看
                self.tradeZoneLow=self.combindBar.ix[0]['low']
                self.tradeZoneHigh=self.combindBar.ix[barrow-2]['high']#取顶点的最高值
                self.marketCount = 1
            elif self.marketCount<3:
                self.tradeZoneHigh=min(self.tradeZoneHigh,self.combindBar.ix[barrow-2]['high'])
                self.marketCount += 1
                self.trendPeriod = 0
            else:
                if self.trendPeriod < 3: return  # 前3波行情不做3根K线共用的限制，不加入trendPeriod的判断
                self.marketFlag = -1
                self.marketCount += 1
                self.trendPeriod = 0
                '''
                #做卖操作，判断多仓是否连续三次减仓，或者空仓连续三次增仓
                if (self.positionTrend.ix[prow-1]['do']<self.positionTrend.ix[prow-2]['do'] and
                    self.positionTrend.ix[prow-2]['do']<self.positionTrend.ix[prow-3]['do']) or\
                    (self.positionTrend.ix[prow-1]['ko']>self.positionTrend.ix[prow-2]['ko'] and
                    self.positionTrend.ix[prow-2]['ko']>self.positionTrend.ix[prow-3]['ko']):
                    self.buyFlag=-1
              '''
                self.buyFlag = -1
                pass
        else:pass
        # 有行情时，保存行情信息
        row=self.dailyBarMin.shape[0]
        bar = self.dailyBarMin.iloc[row - 2]
        marketInfo = {"index": self.marketCount,
                      'xpos': row-2,
                      'time': bar.utcdatetime,
                      'phigh':bar.high,
                      'plow': bar.low,
                      'pnow': bar.low if self.marketFlag==1 else bar.high,
                      'type': self.marketFlag
                      }
        self.marketList.append(marketInfo)
        pass

    def buyJudge(self,bar):
        '''
        买入条件：
        1、收盘价格在交易区间外才能交易
        2、第三根最高价格高于第一根
        3、而且：红绿数值相减连续变大，持续4~5根K线（可设）
        4、持续3根K线的成交量增加
        5、而且：
                1)当第2根的MACD值大于等于第1根MACD值
                2)或第2根的KDJ值大于等于第1根KDJ值
                3)或如果当前第二根最低价格低于前一底部形态第二根最低价，而当前第二根MACD或KDJ值大于或等于前一底部形态第二根。
                4)或如果当前第二根最低价格高于前一底部形态第二根最低价，而当前第二根MACD或KDJ值小于或等于前一底部形态第二根。
        :param bar:
        :return:
        '''
        # 1.1版本，平仓无交易区间限制，开仓才有交易区间限制
        # 上涨趋势中，判断是否持有空仓，有的话平掉空仓
        position = self.get_position(self.exchange_id, self.sec_id, 2)
        if position:
            self.close_short(self.exchange_id, self.sec_id, 0, position.volume)
        # 加入交易区间的限制，在交易区间外才交易，或者无交易区间（high<=low)
        #1.1加入底部形态第3根K线最高价必须高于第1根K线的最高价，同时第3根K线的成交量必须大于第2根
        prow = self.positionTrend.shape[0]
        crow= self.combindBar.shape[0]
        firstHigh=self.combindBar.ix[crow-3]['high']
        thirdHigh=self.combindBar.ix[crow-1]['high']
        secondVolume=self.combindBar.ix[crow-2]['volume']
        thirdVolume=self.combindBar.ix[crow-1]['volume']
        if (self.positionTrend.ix[prow - 1]['do'] - self.positionTrend.ix[prow - 1]['ko']) > \
            (self.positionTrend.ix[prow - 2]['do'] - self.positionTrend.ix[prow - 2]['ko']) and \
            (bar.close > self.tradeZoneHigh or bar.close < self.tradeZoneLow or self.tradeZoneHigh <= self.tradeZoneLow) and \
            (thirdHigh > firstHigh and thirdVolume>secondVolume):
                # 买多
                self.open_long(self.exchange_id, self.sec_id, 0, 1)
        pass

    def sellJudge(self,bar):
        # 1.1版本，平仓无交易区间限制，开仓才有交易区间限制
        # 下跌趋势中，判断是否持有多仓，有的话平掉多仓
        position = self.get_position(self.exchange_id, self.sec_id, 1)
        if position:
            self.close_long(self.exchange_id, self.sec_id, 0, position.volume)
        # 加入交易区间的限制，在交易区间外才交易，或者无交易区间（high<=low)
        #1.1加入,顶部形态第3根K线的最低价必须低于第1根K线的最低价，同时第3根K线的成交量必须大于第2根K线的成交量
        prow = self.positionTrend.shape[0]
        crow = self.combindBar.shape[0]
        firstLow=self.combindBar.ix[crow-3]['low']
        thirdLow=self.combindBar.ix[crow-1]['low']
        secondVolume=self.combindBar.ix[crow-2]['volume']
        thirdVolume=self.combindBar.ix[crow-1]['volume']
        # 1.1版本，改为当前K线下多仓减空仓大于上一K线多仓减空仓
        if (self.positionTrend.ix[prow - 1]['ko'] - self.positionTrend.ix[prow - 1]['do']) > \
            (self.positionTrend.ix[prow - 2]['ko'] - self.positionTrend.ix[prow - 2]['do']) and \
            (bar.close > self.tradeZoneHigh or bar.close < self.tradeZoneLow or self.tradeZoneHigh <= self.tradeZoneLow) and \
            (thirdLow<firstLow and thirdVolume>secondVolume):
            # 多空，平多
            self.open_short(self.exchange_id, self.sec_id, 0, 1)
        pass
    #插入n个空bar，用来填补出来无交易时空帧的情况
    #插入规则：
    #       high、low、position跟上一帧保持一致
    #       open、close为0
    #       时间为上一帧加1分钟
    #如果n>K_min，还要对dailyBarMin进行插空
    #构造一个Bar对象，然后调用update函数
    def insertEmptyBar(self,n):
        i=n
        bar = Bar.Bar()
        while(i>1):
            rownum = self.dailyBar.shape[0]-1
            bar.strtime=' '
            bar.utc_time=self.dailyBar.ix[rownum]['utcdatetime']+60
            bar.open=0
            bar.close=0
            bar.high=self.dailyBar.ix[rownum]['high']
            bar.low=self.dailyBar.ix[rownum]['low']
            bar.position=self.dailyBar.ix[rownum]['position']
            bar.volume=self.dailyBar.ix[rownum]['volume']
            self.update_dailyBar(bar)
            if(datetime.datetime.fromtimestamp(bar.utc_time).minute% self.K_min==0):
                self.update_dailyBarMin(bar)
                pass
            i-=1
        pass

    def prepareMACD(self):
        '''
        在dataPrepare准备完后，一次计算已有数据的MACD，保存到self.MACD中
        self.MACD=pd.DataFrame(columns=['strdatetime','utcdatetime','close','MACD','DEA','HIST','sema','lema'])
        :return:
        '''
        self.MACD['strdatetime']=self.dailyBarMin['strdatetime']
        self.MACD['utcdatetime']=self.dailyBarMin['utcdatetime']
        self.MACD['close']=self.dailyBarMin['close']
        self.MACD['MACD'],self.MACD['DEA'],self.MACD['HIST'],self.MACD['sema'],self.MACD['lema']\
            =ma.calMACD(self.MACD['close'])
        pass

    def updateMACD(self):
        '''
        根据dailyBarMin最后一行的数据，计算出新的MACD，并更新到MACD表中
        :return:
        '''
        brow=self.dailyBarMin.shape[0]
        mrow=self.MACD.shape[0]
        laststrdatetime=self.dailyBarMin.ix[brow-1,'strdatetime']
        lastutcdatetime = self.dailyBarMin.ix[brow - 1, 'utcdatetime']
        lastClose=self.dailyBarMin.ix[brow-1,'close']
        lastdea=self.MACD.ix[mrow-1,'DEA']
        lastsema=self.MACD.ix[mrow-1,'sema']
        lastlema=self.MACD.ix[mrow-1,'lema']
        macd,dea,hist,sema,lema=ma.calNewMACD(lastClose,lastdea,lastsema,lastlema)
        self.MACD.loc[mrow] = [laststrdatetime,lastutcdatetime, lastClose, macd, dea, hist, sema,lema]
        pass

    def prepareKDJ(self):
        '''
        在dataPrepare准备完后，一次计算已有数据的KDJ，保存到self.KDJ中
        self.KDJ=pd.DataFrame(columns=['strdatetime','utcdatetime','lowL','highL','RSV','KDJ_K','KDJ_D','KDJ_J'])
        :return:
        '''
        self.KDJ['strdatetime']=self.dailyBarMin['strdatetime']
        self.KDJ['utcdatetime']=self.dailyBarMin['utcdatetime']
        self.KDJ['lowL'],self.KDJ['highL'],self.KDJ['RSV'],self.KDJ['KDJ_K'],self.KDJ['KDJ_D'],self.KDJ['KDJ_J']\
            =ma.calKDJ(self.dailyBarMin)
        pass

    def updateKDJ(self):
        '''
        根据dailyBarMin最后一行的数据，计算出新的KDJ，并更新到KDJ表中
        :return:
        '''
        ma.calNewKDJ(self.dailyBarMin,self.KDJ)
        pass

    #准备好画布，分成1列3行，第一个为原始K线，第二个为合并后的K线，第三个为仓位走势图
    #准备好之后，如果数据不为空，则将已有数据画出
    def pltPrepare(self):
        if self.mode==4:return
        self.axesSet['up'] = self._Fig.add_axes([0.1, 0.68, 0.8, 0.3], axis_bgcolor='white')
        self.axesSet['mid'] = self._Fig.add_axes([0.1, 0.34, 0.8, 0.25], axis_bgcolor='white')
        self.axesSet['down'] = self._Fig.add_axes([0.1, 0.08, 0.8, 0.15], axis_bgcolor='white')
        self.plotSet['up'] = pc.PlotCandlesticks(axesObject=self.axesSet['up'], pdata=self.dailyBarMin, xlength=150, showX=True, name="daialy Bar")
        self.plotSet['mid'] = pc.PlotCandlesticks(axesObject=self.axesSet['mid'],pdata=self.combindBar,xlength=150,showX=True,name="combined Bar")
        self.plotSet['down'] = pc.PlotPositionLine(axesObject=self.axesSet['down'],pdata=self.positionTrend,xlength=150,showX=False,name="position trend")
        if self.marketCount>=3:
            # 画出交易区间
            self.plotSet['up'].plotTradeZone(self.tradeZoneHigh, self.tradeZoneLow)
            self.plotSet['mid'].plotTradeZone(self.tradeZoneHigh, self.tradeZoneLow)
        if len(self.marketList)>0   :
            #在每个行情点写出价格
            for ml in self.marketList:
                self.plotSet['up'].plotPrice(ml['xpos'],ml['phigh'],ml['plow'],ml['type'])
        #plt.show()
        pass

    #更新画布，在on_Bar()中调用，每次数据更新后更新画图；在pltPrepare()中调用，画布准备好之后，把已有数据画出来
    def pltUpdate(self):
        '''
        更新画布，调用updateCandlesticks(self,bar)，updatePositionLine
        每次更新完dailyBarMin之后，更新上图、下图
        每次更新完combinedBar之后，更新中图
        每次有行情信息，在上图和中图写出行情价格
        :return:
        '''
        # 画布相关参数
        #if self.mode==4:return
        self._figfacecolor = __color_pink__
        self._figedgecolor = __color_navy__
        self._figdpi = 200
        self._figlinewidth = 1.0
        self._xfactor = 0.025  # x size * x factor = x length
        self._yfactor = 0.025  # y size * y factor = y length

        self._xlength = 7
        self._ylength = 4
        # 一个figure，三个Axes
        #        self.pltConfig=plt.figure(1) #创建一个公共画布，用来画走势图和K线图
        self._Fig = plt.figure(figsize=(self._xlength, self._ylength), dpi=self._figdpi,
                               facecolor=self._figfacecolor,
                               edgecolor=self._figedgecolor, linewidth=self._figlinewidth)  # Figure 对象
        self.axesSet = {}
        self.plotSet = {}
        self.axesSet['up'] = self._Fig.add_axes([0.1, 0.68, 0.8, 0.3], axis_bgcolor='white')
        self.axesSet['mid'] = self._Fig.add_axes([0.1, 0.34, 0.8, 0.25], axis_bgcolor='white')
        self.axesSet['down'] = self._Fig.add_axes([0.1, 0.08, 0.8, 0.15], axis_bgcolor='white')
        self.plotSet['up'] = pc.PlotCandlesticks(axesObject=self.axesSet['up'], pdata=self.dailyBarMin, xlength=300,
                                                 showX=True, name="daialy Bar")
        self.plotSet['mid'] = pc.PlotCandlesticks(axesObject=self.axesSet['mid'], pdata=self.combindBar, xlength=300,
                                                  showX=True, name="combined Bar")
        self.plotSet['down'] = pc.PlotPositionLine(axesObject=self.axesSet['down'], pdata=self.positionTrend,
                                                   xlength=300, showX=False, name="position trend")
        if self.marketCount >= 3:
            # 画出交易区间
            self.plotSet['up'].plotTradeZone(self.tradeZoneHigh, self.tradeZoneLow)
            self.plotSet['mid'].plotTradeZone(self.tradeZoneHigh, self.tradeZoneLow)
        if len(self.marketList) > 0:
            # 在每个行情点写出价格
            for ml in self.marketList:
                self.plotSet['up'].plotPrice(ml['xpos'], ml['phigh'], ml['plow'], ml['type'])
        self._Fig.savefig(self.last_update_time.strftime("%Y%m%d")+str(self.marketCount) + ".jpg")
        plt.close('all')

        '''
        if pos =='up':
            bar=self.dailyBarMin.iloc[-1]
            self.plotSet['up'].updateCandlesticks(self.dailyBarMin,bar)
        elif pos == 'mid':
            bar=self.combindBar.iloc[-1]
            self.plotSet['mid'].updateCandlesticks(self.combindBar,bar)
            print "saving pictures"
            self._Fig.savefig("d:/"+str(self.marketCount)+".jpg")
            print "saving pictures done"
        else:
            self.plotSet['down'].updatePositionLine()
        plt.show()
        '''
        pass

if __name__ == '__main__':
    ''''
    myStrategy = Mystrategy(
        username='smartgang@126.com',
        password='39314656a',
        strategy_id='3ac57fd6-818b-11e7-8296-0019860005e9',
        subscribe_symbols='DCE.J.bar.60',
        mode=4,#2为实时行情，3为模拟行情,4为回测
        td_addr=''
    )
    '''
    ini_file = sys.argv[1] if len(sys.argv) > 1 else 'pwconfig.ini'
    logging.config.fileConfig(ini_file)
    myStrategy = Mystrategy(config_file=ini_file)
    ret = myStrategy.run()
    print('exit code: ', ret)
# -*- coding: utf-8 -*-
'''
用于绘制PositionWin策略的图像
图像包括三部分：
上：分钟K线图[0.1,0.6,0.8,0.9]
中：合并后的K线图[0.1,0.3,0.8,0.5]
下：仓量变化图[0.1,0.1,0.8,0.25]
在上和中两图中，增加压力区间线（标出数值）
在上图画出买卖点
在中图画出行情信号

图像初始化时，先将已有数据画出
    上中下共用一套xParameter，在上图中画出('x')
    上中的yParameter相同，各自画出('y1')
    下图独立的yParameter，独立画出('y2')
后续根据每一Bar的内容进行更新：
    判断是否要进行坐标轴大小的调整
        上中图因为每天的波动幅度有限，其实可以把尺寸定死，只更新下图
        每天交易的时间也是固定的，相当于X轴的长度也是固定，可以根据分钟K线定死
    在三幅图中画出新Bar内容
'''
import datetime
import numpy
import pandas as pd
import matplotlib
matplotlib.use("WXAgg", warn=True)  # 这个要紧跟在 import matplotlib 之后，而且必须安装了 wxpython 2.8 才行。
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import time
import Bar
#from gmsdk.gm import Bar
__color_lightsalmon__ = '#ffa07a'
__color_pink__ = '#ffc0cb'
__color_navy__ = '#000080'
__color_gold__ = '#FDDB05'
__color_gray30__ = '0.3'
__color_gray70__ = '0.7'
__color_lightblue__ = 'lightblue'


class PlotCandlesticks():

    def __init__(self,axesObject,pdata,xlength,showX,name):

        self.linecounter=0
        self.stickcounter=0

        self._Axes=axesObject
        self._pdata=pdata
        self._xlength=xlength
        self._isShowX=showX
        self._name=name
        # 1.先准备数据
        self.time = self._pdata['strdatetime']
        self.timelist=[]
        self.high = self._pdata['high']
        self.low = self._pdata['low']
        self.open = self._pdata['open']
        self.close = self._pdata['close']

        self._yhighlim = 0
        self._ylowlim = 0
        self._ysize = 0
        self._xsize = 0
        plt.ion()
        # 取数据长度
        self.length = len(self.high)
        #   转换成序列
        # ==============================================================================================================
        # 一天的交易时长按最长450分钟估计，则x轴的长度为450/k_min
        self._xindex = numpy.arange(self.length)  # X 轴上的 index，一个辅助数据
        self._zipoc = zip(self.open, self.close)  # smart:将open和close一对对打包
        # 把数据中上涨，下跌，持平的数据都分别用trun和false进行标识
        self._up = numpy.array(
            [True if po < pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内上涨的一个序列
        self._down = numpy.array(
            [True if po > pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内下跌的一个序列
        self._side = numpy.array(
            [True if po == pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内走平的一个序列

        self._setupAxes()
        self._setXAxis()
        self._setYAxis()
        self.plotCandlesticks()

    def _compute_size(self):
        '''
           根据绘图数据 pdata 计算出本子图的尺寸，修改数据成员
        '''
        phigh = max([ph for ph in self.high if ph is not None])  # 最高价
        plow = min([pl for pl in self.low if pl is not None])  # 最低价

        yhighlim = int(phigh/10)*10+10 # K线子图 Y 轴最大坐标,5%最大波动,调整为10的倍数
        ylowlim = int(plow/10)*10  # K线子图 Y 轴最小坐标
        self._yhighlim = yhighlim
        self._ylowlim = ylowlim
        self._xsize = self._xlength
        self._ysize = yhighlim - ylowlim

    def _setupAxes(self):

        self._xAxis = self._Axes.get_xaxis()
        self._yAxis = self._Axes.get_yaxis()
        self._Axes.set_axisbelow(True)  # 网格线放在底层
        #   设置两个坐标轴上的网格线
        # ==================================================================================================================================================
        self._xAxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        self._xAxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)
        self._yAxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        self._yAxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)
        self._yAxis.set_label_position('left')
        self._Axes.set_label(self._name)
        self._compute_size()
        pass

    def _setXAxis(self):
        #设置X轴的范围

        timetmp = []
        for t in self.time: timetmp.append(t[11:19])
        self.timelist = [datetime.time(int(hr), int(ms), int(sc)) for hr, ms, sc in
                    [dstr.split(':') for dstr in timetmp]]
        i = 0
        minindex = []
        for min in self.timelist:
            if min.minute % 15 == 0: minindex.append(i)
            i += 1
        xMajorLocator = FixedLocator((numpy.array(minindex)))
        wdindex = numpy.arange(self.length)
        xMinorLocator = FixedLocator(wdindex)

        # 确定 X 轴的 MajorFormatter 和 MinorFormatter
        def x_major_formatter(idx, pos=None):
            if idx<self.length:return self.timelist[int(idx)].strftime('%H:%M:%S')
            else:return pos

        def x_minor_formatter(idx, pos=None):
            if idx<self.length:return self.timelist[int(idx)].strftime('%M:%S')
            else:return pos

        xMajorFormatter = FuncFormatter(x_major_formatter)
        xMinorFormatter = FuncFormatter(x_minor_formatter)
        # 设定 X 轴的 Locator 和 Formatter
        self._Axes.set_xlim(0, self._xsize)
        self._xAxis.set_major_locator(xMajorLocator)
        self._xAxis.set_major_formatter(xMajorFormatter)
        self._xAxis.set_minor_locator(xMinorLocator)
        self._xAxis.set_minor_formatter(xMinorFormatter)

        # 设置 X 轴标签的显示样式。
        for mal in self._Axes.get_xticklabels(minor=False):
            mal.set_fontsize(3)
            mal.set_horizontalalignment('center')
            mal.set_rotation('90')
            if self._isShowX:mal.set_visible(True)
            else: mal.set_visible(False)

        for mil in self._Axes.get_xticklabels(minor=True):
            mil.set_fontsize(3)
            mil.set_horizontalalignment('right')
            mil.set_rotation('90')
            mil.set_visible(False)
        pass

    def _setYAxis(self):
        ylimgap = self._yhighlim - self._ylowlim
        #   主要坐标点
        # ----------------------------------------------------------------------------
        #        majors = [ylowlim]
        #        while majors[-1] < yhighlim: majors.append(majors[-1] * 1.1)
        majors = numpy.arange(self._ylowlim, self._yhighlim, ylimgap / 5)
        minors = numpy.arange(self._ylowlim, self._yhighlim, ylimgap / 10)
        #   辅助坐标点
        # ----------------------------------------------------------------------------
        #        minors = [ylowlim * 1.1 ** 0.5]
        #        while minors[-1] < yhighlim: minors.append(minors[-1] * 1.1)
        majorticks = [loc for loc in majors if loc > self._ylowlim and loc < self._yhighlim]  # 注意，第一项（ylowlim）被排除掉了
        minorticks = [loc for loc in minors if loc > self._ylowlim and loc < self._yhighlim]

        #   设定 Y 轴坐标的范围
        # ==================================================================================================================================================
        self._Axes.set_ylim(self._ylowlim, self._yhighlim)

        #   设定 Y 轴上的坐标
        # ==================================================================================================================================================

        #   主要坐标点
        # ----------------------------------------------------------------------------
        yMajorLocator = FixedLocator(numpy.array(majorticks))

        # 确定 Y 轴的 MajorFormatter
        def y_major_formatter(num, pos=None):
            return str(num)

        yMajorFormatter = FuncFormatter(y_major_formatter)

        # 设定 X 轴的 Locator 和 Formatter
        self._yAxis.set_major_locator(yMajorLocator)
        self._yAxis.set_major_formatter(yMajorFormatter)

        # 设定 Y 轴主要坐标点与辅助坐标点的样式
        fsize = 4
        for mal in self._Axes.get_yticklabels(minor=False):
            mal.set_fontsize(fsize)

        # 辅助坐标点
        # ----------------------------------------------------------------------------
        yMinorLocator = FixedLocator(numpy.array(minorticks))

        # 确定 Y 轴的 MinorFormatter
        def y_minor_formatter(num, pos=None):
            return str(num)

        yMinorFormatter = FuncFormatter(y_minor_formatter)

        # 设定 Y 轴的 Locator 和 Formatter
        self._yAxis.set_minor_locator(yMinorLocator)
        self._yAxis.set_minor_formatter(yMinorFormatter)
        # 设定 Y 轴辅助坐标点的样式
        for mil in self._Axes.get_yticklabels(minor=True):
            mil.set_visible(False)

    def plotCandlesticks(self):
        '''
         绘制 K 线
         '''
        axes = self._Axes
        xindex = self._xindex
        up = self._up
        down = self._down
        side = self._side
        open = self.open
        close = self.close

        #   对开收盘价进行视觉修正
        for idx, poc in enumerate(self._zipoc):
            if poc[0] == poc[1] and None not in poc:
                open[idx] = poc[0] - 0.1  # 稍微偏离一点，使得在图线上不致于完全看不到
                close[idx] = poc[1] + 0.1

        rarray_open = numpy.array(self.open)
        rarray_close = numpy.array(self.close)
        rarray_high = numpy.array(self.high)
        rarray_low = numpy.array(self.low)

        # XXX: 如果 up, down, side 里有一个全部为 False 组成，那么 vlines() 会报错。
        # XXX: 可以使用 alpha 参数调节透明度
        if True in up:
            axes.vlines(xindex[up], rarray_low[up], rarray_high[up], edgecolor='red', linewidth=0.4,
                        label='_nolegend_',
                        alpha=1)
            axes.vlines(xindex[up], rarray_open[up], rarray_close[up], edgecolor='red', linewidth=1.5,
                        label='_nolegend_', alpha=1)

        if True in down:
            axes.vlines(xindex[down], rarray_low[down], rarray_high[down], edgecolor='green', linewidth=0.4,
                        label='_nolegend_', alpha=1)
            axes.vlines(xindex[down], rarray_open[down], rarray_close[down], edgecolor='green', linewidth=1.5,
                        label='_nolegend_', alpha=1)

        if True in side:
            axes.vlines(xindex[side], rarray_low[side], rarray_high[side], edgecolor='0.7', linewidth=0.4,
                        label='_nolegend_', alpha=1)
            axes.vlines(xindex[side], rarray_open[side], rarray_close[side], edgecolor='0.7', linewidth=1.5,
                        label='_nolegend_', alpha=1)

    def plotTradeZone(self,high,low):
        '''
        在high和low的高度画出两条横穿图像的直线，表示非交易区间
        :param high:
        :param low:
        :return:
        '''
        if low>=high:
            self._Axes.text(0, low+(high-low)/2, 'no trade zone', fontsize=4, color='w')
        else:
            self._Axes.hlines(high,0,self._xlength,color=__color_gold__,linewidth=0.4)
            self._Axes.hlines(low,0,self._xlength,color=__color_lightblue__,linewidth=0.4)
            self._Axes.text(0,high,str(high),fontsize=4,color='w')
            self._Axes.text(0,low,str(low),fontsize=4,color='w')
        pass

    def updateCandlesticks(self,pdata,bar):
        '''
        根据Bar更新画图：
            更新蜡烛区的K线
            X轴上显示对应的标签:更新self.timelist
            更新yhighlim和ylowlim
        :param bar:
        :return:
        '''
        #更新x轴坐标
        timestr=bar['strdatetime'][11:19]
        hr,ms,sc=timestr.split(':')
        self.timelist.append(datetime.time(int(hr),int(ms),int(sc)))
        mal=self._Axes.get_xticklabels(minor=False)
        xindex=len(self.timelist)-1
        self.length=xindex
        if int(ms) % 15 == 0 and self._isShowX is True:
            mlen=len(mal)
            mal[mlen].set_fontsize(3)
            mal[mlen].set_horizontalalignment('center')
            mal[mlen].set_rotation('90')
            mal[mlen].set_visible(True)
        ''''
        #更新high,low,open,close,_up,_down,_side,_zipoc
        self._pdata=pdata
        self.length+=1
        self.high = self._pdata['high']
        self.low = self._pdata['low']
        self.open = self._pdata['open']
        self.close = self._pdata['close']
        self._xindex = numpy.arange(self.length)  # X 轴上的 index，一个辅助数据
        self._zipoc = zip(self.open, self.close)  # smart:将open和close一对对打包
        # 把数据中上涨，下跌，持平的数据都分别用trun和false进行标识
        self._up = numpy.array(
            [True if po < pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内上涨的一个序列
        self._down = numpy.array(
            [True if po > pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内下跌的一个序列
        self._side = numpy.array(
            [True if po == pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内走平的一个序列
        self._Axes.cla()
        self.plotCandlesticks()
        plt.show()
        '''
        #更新K线
        open=bar['open']
        close=bar['close']
        high=bar['high']
        low=bar['low']
        if close> open:
            self._Axes.vlines(xindex, low, high, edgecolor='red', linewidth=0.4,
                        label='_nolegend_',
                        alpha=1)
            self._Axes.vlines(xindex, open, close, edgecolor='red', linewidth=1.5,
                        label='_nolegend_', alpha=1)
        if close<open:
            self._Axes.vlines(xindex, low, high, edgecolor='green', linewidth=0.4,
                        label='_nolegend_', alpha=1)
            self._Axes.vlines(xindex, open, close, edgecolor='green', linewidth=1.5,
                        label='_nolegend_', alpha=1)
        if close==open:
            self._Axes.vlines(xindex, low, high, edgecolor='0.7', linewidth=0.4,
                        label='_nolegend_', alpha=1)
            self._Axes.vlines(xindex, open+0.1, close-0.1, edgecolor='0.7', linewidth=1.5,
                        label='_nolegend_', alpha=1)
        self._Axes.hlines(1283,0,self._xlength,color=__color_navy__,linewidth=2)
        #更新ylim
        if high>=self._yhighlim:
            self._yhighlim=high
            self._Axes.set_ylim(self._ylowlim,self._yhighlim)
        if low<=self._ylowlim:
            self._ylowlim=low
            self._Axes.set_ylim(self._ylowlim, self._yhighlim)


    def plotPrice(self,x,ph,pl,t):
        if t==1:self._Axes.text(x,pl,str(pl),fontsize=3,color='g')
        else: self._Axes.text(x,ph,str(ph),fontsize=3,color='r')

class PlotPositionLine():
    def __init__(self, axesObject, pdata, xlength, showX, name):
        self._Axes = axesObject
        self._pdata = pdata
        self._xlength = xlength
        self._isShowX = showX
        self._name = name
        # 1.先准备数据
        self.time = self._pdata['strdatetime']
        self.timelist = []
        self.do = self._pdata['do']
        self.ko = self._pdata['ko']

        self.length = len(self.time)

        self._yhighlim = 0
        self._ylowlim = 0
        self._ysize = 0
        self._xsize = 0
        self._xindex = numpy.arange(self.length)  # X 轴上的 index，一个辅助数据
        plt.ion()
        self._setupAxes()
        self._setupXAxis()
        self._setupYAxis()
        self.plotPositionLine()

    def _setupAxes(self):
        self._xAxis = self._Axes.get_xaxis()
        self._yAxis = self._Axes.get_yaxis()
        self._Axes.set_axisbelow(True)  # 网格线放在底层
        #   设置两个坐标轴上的网格线
        # ==================================================================================================================================================
        self._xAxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        self._xAxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)
        self._yAxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        self._yAxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)
        self._yAxis.set_label_position('left')
        self._Axes.set_label(self._name)

        dhigh = max([ph for ph in self.do if ph is not None])  # 最高价
        dlow = min([dl for dl in self.do if dl is not None])
        khigh = max([kh for kh in self.ko if kh is not None])
        klow = min([pl for pl in self.ko if pl is not None])  # 最低价

        self._yhighlim=  round(max(dhigh,khigh)*1.01,0)
        self._ylowlim = round(min(dlow,klow)+dlow*0.01,0)  # K线子图 Y 轴最小坐标
        self._xsize = self._xlength
        self._ysize = self._yhighlim - self._ylowlim

    def _setupXAxis(self):
        #设置X轴的范围

        timetmp = []
        for t in self.time: timetmp.append(t[11:19])
        self.timelist = [datetime.time(int(hr), int(ms), int(sc)) for hr, ms, sc in
                    [dstr.split(':') for dstr in timetmp]]
        i = 0
        minindex = []
        for min in self.timelist:
            if min.minute % 15 == 0: minindex.append(i)
            i += 1
        xMajorLocator = FixedLocator((numpy.array(minindex)))
        wdindex = numpy.arange(self.length)
        xMinorLocator = FixedLocator(wdindex)

        # 确定 X 轴的 MajorFormatter 和 MinorFormatter
        def x_major_formatter(idx, pos=None):
            if idx<self.length:return self.timelist[int(idx)].strftime('%H:%M:%S')
            else:return pos

        def x_minor_formatter(idx, pos=None):
            if idx<self.length:return self.timelist[int(idx)].strftime('%M:%S')
            else:return pos

        xMajorFormatter = FuncFormatter(x_major_formatter)
        xMinorFormatter = FuncFormatter(x_minor_formatter)
        # 设定 X 轴的 Locator 和 Formatter
        self._Axes.set_xlim(0, self._xsize)
        self._xAxis.set_major_locator(xMajorLocator)
        self._xAxis.set_major_formatter(xMajorFormatter)
        self._xAxis.set_minor_locator(xMinorLocator)
        self._xAxis.set_minor_formatter(xMinorFormatter)

        # 设置 X 轴标签的显示样式。
        for mal in self._Axes.get_xticklabels(minor=False):
            mal.set_fontsize(3)
            mal.set_horizontalalignment('center')
            mal.set_rotation('90')
            if self._isShowX:mal.set_visible(True)
            else: mal.set_visible(False)

        for mil in self._Axes.get_xticklabels(minor=True):
            mil.set_fontsize(3)
            mil.set_horizontalalignment('right')
            mil.set_rotation('90')
            mil.set_visible(False)
        pass

    def _setupYAxis(self):

        ylimgap = self._yhighlim - self._ylowlim

        majors = numpy.arange(self._ylowlim, self._yhighlim, ylimgap / 5)
        minors = numpy.arange(self._ylowlim, self._yhighlim, ylimgap / 10)

        majorticks = [loc for loc in majors if loc > self._ylowlim and loc < self._yhighlim]  # 注意，第一项（ylowlim）被排除掉了
        minorticks = [loc for loc in minors if loc > self._ylowlim and loc < self._yhighlim]

        #   设定 Y 轴坐标的范围
        # ==================================================================================================================================================
        self._Axes.set_ylim(self._ylowlim, self._yhighlim)
        #   主要坐标点
        # ----------------------------------------------------------------------------
        yMajorLocator = FixedLocator(numpy.array(majorticks))
        # 确定 Y 轴的 MajorFormatter
        def y_major_formatter(num, pos=None):
            return str(num)

        yMajorFormatter = FuncFormatter(y_major_formatter)
        # 设定 X 轴的 Locator 和 Formatter
        self._yAxis.set_major_locator(yMajorLocator)
        self._yAxis.set_major_formatter(yMajorFormatter)

        # 设定 Y 轴主要坐标点与辅助坐标点的样式
        fsize = 4
        for mal in self._Axes.get_yticklabels(minor=False):
            mal.set_fontsize(fsize)

        # 辅助坐标点
        # ----------------------------------------------------------------------------
        yMinorLocator = FixedLocator(numpy.array(minorticks))

        # 确定 Y 轴的 MinorFormatter
        def y_minor_formatter(num, pos=None):
            return str(num)

        yMinorFormatter = FuncFormatter(y_minor_formatter)

        # 设定 Y 轴的 Locator 和 Formatter
        self._yAxis.set_minor_locator(yMinorLocator)
        self._yAxis.set_minor_formatter(yMinorFormatter)
        # 设定 Y 轴辅助坐标点的样式
        for mil in self._Axes.get_yticklabels(minor=True):
            mil.set_visible(False)

    def plotPositionLine(self):
        self._Axes.plot(self.do,color='r',linewidth=1)
        self._Axes.plot(self.ko,color='g',linewidth=1)

    def updatePositionLine(self):
        pass

if __name__ == '__main__':
    _figfacecolor = __color_pink__
    _figedgecolor = __color_navy__
    _figdpi = 200
    _figlinewidth = 1.0
    _xfactor = 0.025  # x size * x factor = x length
    _yfactor = 0.025  # y size * y factor = y length

    _xlength = 7
    _ylength = 4
    _Fig = plt.figure(figsize=(_xlength, _ylength), dpi=_figdpi,
                           facecolor=_figfacecolor,
                           edgecolor=_figedgecolor, linewidth=_figlinewidth)  # Figure 对象
    axesSet = {}
    axesSet['up'] = _Fig.add_axes([0.1, 0.65, 0.8, 0.3], axis_bgcolor='black')
    axesSet['mid'] = _Fig.add_axes([0.1, 0.3, 0.8, 0.25], axis_bgcolor='black')
    axesSet['down'] = _Fig.add_axes([0.1, 0.1, 0.8, 0.15], axis_bgcolor='black')
#    plt.ion()
    pdata = pd.read_csv('d:\data_1m.csv', index_col='index')
    myfig1 = PlotCandlesticks(axesObject=axesSet['up'],pdata=pdata,xlength=200,showX=True,name="daialy Bar")
    myfig1.plotTradeZone(1288,1280)

    myfig2 = PlotCandlesticks(axesObject=axesSet['mid'],pdata=pdata,xlength=200,showX=False,name="combinedBar")
    myfig3 = PlotPositionLine(axesObject=axesSet['down'],pdata=pdata,xlength=200,showX=False,name="position trend")
    _Fig.savefig('d:/myfig.jpg')
    print "10 seconds to update"

    print "after updated,wait 10 seconds"
    time.sleep(10)
    print "going on"
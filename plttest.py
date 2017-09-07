# -*- coding: utf-8 -*-
import pandas as pd
import numpy
import math
import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from matplotlib.pylab import date2num, FixedLocator, FuncFormatter, FixedFormatter

__color_lightsalmon__ = '#ffa07a'
__color_pink__ = '#ffc0cb'
__color_navy__ = '#000080'
__color_gold__ = '#FDDB05'
__color_gray30__ = '0.3'
__color_gray70__ = '0.7'
__color_lightblue__ = 'lightblue'

class PlotK:
    '''
    颜色代码：
        red=r
        black=k
        blue=b
        cyan=c
        yellow=y
        white=w
        green=g

    '''

    '''
    ax1=plt.subplot(311)
    ax2=plt.subplot(312)
    ax3=plt.subplot(313)
    ax1.set_title('orient K')
    ax1.set_ylabel('price')
    ax2.set_title('combined K')
    ax2.set_ylabel('price')
    
    ko=df['ko']
    do=df['do']
    ax3.set_title('Position')
    ax3.set_ylabel('position')
    ax3.set_xlim(0,1000)
    
    ax3.plot(ko,color='g',label='short position')
    ax3.plot(do,color='r',label='long position')
    ax3.legend()
    plt.show()
    '''


    def __init__(self, pdata):

        self._pdata=pdata
        self._shrink=1
        self._expbase=1.1

        #1.先准备数据
        self.time=self._pdata['start_time']
        self.high=self._pdata['high']
        self.low=self._pdata['low']
        self.open=self._pdata['open']
        self.close=self._pdata['close']
        self.ko=self._pdata['ko']
        self.do=self._pdata['do']

        #有多个图的时候，用这个来保存
        #self._subplots

        #取数据长度
        self.length=len(self.high)

        #   转换成序列
        # ==============================================================================================================
        self._xindex = numpy.arange(self.length)  # X 轴上的 index，一个辅助数据

        self._zipoc = zip(self.open, self.close)  # smart:将open和close一对对打包
        #把数据中上涨，下跌，持平的数据都分别用trun和false进行标识
        self.up = numpy.array(
            [True if po < pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内上涨的一个序列
        self.down = numpy.array(
            [True if po > pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内下跌的一个序列
        self.side = numpy.array(
            [True if po == pc and po is not None else False for po, pc in self._zipoc])  # 标示出该天股价日内走平的一个序列

        #计算坐标轴大小
        self._Axes = None
        self._AxisX = None
        self._AxisY = None

        self._xsize = 0.0
        self._ysize = 0.0

        self._yhighlim = 0  # Y 轴最大坐标
        self._ylowlim = 0  # Y 轴最小坐标

        self._xparams=self._compute_xparams()
        self._compute_size()
        self._ytickset = self._compute_ytickset()  # 需放在前一句后面
        #   根据计算出的尺寸建立 Figure 对象
        # ===============================================================================================================
        self._xsize, self._ysize = self.get_size()

        self._figfacecolor = __color_pink__
        self._figedgecolor = __color_navy__
        self._figdpi = 200
        self._figlinewidth = 1.0

        self._xsize_left = 12.0  # left blank
        self._xsize_right = 12.0  # right blank
        self._ysize_top = 0.3  # top blank
        self._ysize_bottom = 1.2  # bottom blank
        self._xfactor = 10.0 / 400.0  # x size * x factor = x length
        self._yfactor = 0.1  # y size * y factor = y length
       # self._yfactor=0.6

        self._ysize_gap1 = 0
        self._ysize_gap2 = 0

        self._xlength = self._xsize * self._xfactor
        self._ylength = self._ysize * self._yfactor
        self._Fig = plt.figure(figsize=(self._xlength, self._ylength), dpi=self._figdpi,
                                  facecolor=self._figfacecolor,
                                  edgecolor=self._figedgecolor, linewidth=self._figlinewidth)  # Figure 对象


        rects = self._compute_rect()
        self.build_axes(figobj=self._Fig, rect=rects)
        self.set_xticks()
        self.set_yticks()


    def _compute_size(self):
        '''
        根据绘图数据 pdata 计算出本子图的尺寸，修改数据成员
        '''
        quotes = self._pdata

        popen = self.open[0]  # int 类型

        phigh = max([ph for ph in self.high if ph is not None])  # 最高价
        plow = min([pl for pl in self.low if pl is not None])  # 最低价

#        yhighlim = phigh * 1.2  # K线子图 Y 轴最大坐标
#        ylowlim = plow / 1.2  # K线子图 Y 轴最小坐标
        yhighlim = phigh   # K线子图 Y 轴最大坐标
        ylowlim = plow  # K线子图 Y 轴最小坐标
        self._yhighlim = yhighlim
        self._ylowlim = ylowlim

        # XXX: 价格在 Y 轴上的 “份数”。注意，虽然最高与最低价是以第一个行情为基准修正出来的，但其中包含的倍数因子对结果无影响，即:
        #   log(base, num1) - log(base, num2) ==
        #   log(base, num1/num2) ==
        #   log(base, k*num1/k*num2) ==
        #   log(base, k*num1) - log(base, k*num2)
        # ，这是对数运算的性质。
        #xmargin = self._xparams['xmargin']
        xmargin=1
        self._xsize = (self.length + xmargin * 2) * self._shrink  # int, 所有数据的长度，就是天数
        self._ysize=yhighlim-ylowlim
        #self._ysize = (math.log(yhighlim, self._expbase) - math.log(ylowlim, self._expbase)) * self._shrink  # float


    def get_size(self):
        return (self._xsize, self._ysize)


    def get_ylimits(self):
        return (self._yhighlim, self._ylowlim)

    def get_axes(self):
        return self._Axes

    def build_axes(self, figobj, rect):
        '''
        初始化 self._Axes 对象
        '''
        #   添加 Axes 对象
        # ==================================================================================================================================================
#        sharex = self.get_axes()
#        axes = figobj.add_axes(rect, axis_bgcolor='black', sharex=sharex)
        axes=figobj.add_axes(rect,axis_bgcolor='black')
        axes.set_axisbelow(True)  # 网格线放在底层
        #   axes.set_zorder(1)      # XXX: 不顶用
        #   axes.patch.set_visible(False)   # hide the 'canvas'
        #axes.set_yscale('log', basey=self._expbase)  # 使用对数坐标


        #   改变坐标线的颜色
        # ==================================================================================================================================================
        for child in axes.get_children():
            if isinstance(child, matplotlib.spines.Spine):
                child.set_color(__color_gold__)

        # 得到 X 轴 和 Y 轴 的两个 Axis 对象
        # ==================================================================================================================================================
        xaxis = axes.get_xaxis()
        yaxis = axes.get_yaxis()

        #   设置两个坐标轴上的网格线
        # ==================================================================================================================================================
        xaxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        xaxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)

        yaxis.grid(True, 'major', color='0.3', linestyle='solid', linewidth=0.2)
        yaxis.grid(True, 'minor', color='0.3', linestyle='dotted', linewidth=0.1)

        yaxis.set_label_position('left')

        self._Axes = axes
        self._AxisX = xaxis
        self._AxisY = yaxis

    def set_xticks(self):

        xMajorLocator = self._xparams['xMajorLocator']
        xMinorLocator = self._xparams['xMinorLocator']
        xMajorFormatter = self._xparams['xMajorFormatter']
        xMinorFormatter = self._xparams['xMinorFormatter']

        axes = self._Axes
        xaxis = self._AxisX

        #   设定 X 轴坐标的范围
        # ==================================================================================================================================================
#        xmargin = self._xparams['xmargin']
        xmargin=1
        axes.set_xlim(-xmargin, self.length + xmargin)

        #   先设置 label 位置，再将 X 轴上的坐标设为不可见。因为与 成交量子图 共用 X 轴
        # ==================================================================================================================================================

        # 设定 X 轴的 Locator 和 Formatter
        xaxis.set_major_locator(xMajorLocator)
        xaxis.set_major_formatter(xMajorFormatter)

        xaxis.set_minor_locator(xMinorLocator)
        xaxis.set_minor_formatter(xMinorFormatter)

        #将 X 轴上的坐标设为不可见。
        for mal in axes.get_xticklabels(minor=False):
            mal.set_fontsize(3)
            mal.set_horizontalalignment('center')
            mal.set_rotation('90')

        for mil in axes.get_xticklabels(minor=True):
            mil.set_fontsize(3)
            mil.set_horizontalalignment('right')
            mil.set_rotation('90')
            mil.set_visible(False)


    def _compute_ytickset(self):
        '''
        计算 Y 轴坐标点的位置，包括第二个行情
        '''
        quotes = self._pdata
        expbase = self._expbase

        ytickset = {}

        yhighlim = self._yhighlim
        ylowlim = self._ylowlim
        ylimgap=yhighlim-ylowlim

        #   主要坐标点
        # ----------------------------------------------------------------------------
#        majors = [ylowlim]
#        while majors[-1] < yhighlim: majors.append(majors[-1] * 1.1)
        majors=numpy.arange(ylowlim,yhighlim,ylimgap/10)
        minors=numpy.arange(ylowlim,yhighlim,ylimgap/30)
        #   辅助坐标点
        # ----------------------------------------------------------------------------
#        minors = [ylowlim * 1.1 ** 0.5]
#        while minors[-1] < yhighlim: minors.append(minors[-1] * 1.1)

        ytickset['major'] = [loc for loc in majors if loc > ylowlim and loc < yhighlim]  # 注意，第一项（ylowlim）被排除掉了
        ytickset['minor'] = [loc for loc in minors if loc > ylowlim and loc < yhighlim]

        return ytickset

    def get_ytickset(self):
        return self._ytickset

    def set_yticks(self):
        '''
        设置第一只行情的 Y 轴坐标，包括坐标值在图中间的显示
        '''

        axes = self._Axes
        ylowlim = self._ylowlim
        yhighlim = self._yhighlim
        yaxis = self._AxisY

        majorticks = self._ytickset['major']
        minorticks = self._ytickset['minor']

        #   设定 Y 轴坐标的范围
        # ==================================================================================================================================================
        axes.set_ylim(ylowlim, yhighlim)

        #   设定 Y 轴上的坐标
        # ==================================================================================================================================================

        #   主要坐标点
        # ----------------------------------------------------------------------------

        yMajorLocator = FixedLocator(numpy.array(majorticks))

        # 确定 Y 轴的 MajorFormatter
        def y_major_formatter(num, pos=None):
            return str(round(num, 1))

        yMajorFormatter = FuncFormatter(y_major_formatter)

        # 设定 X 轴的 Locator 和 Formatter
        yaxis.set_major_locator(yMajorLocator)
        yaxis.set_major_formatter(yMajorFormatter)

        # 设定 Y 轴主要坐标点与辅助坐标点的样式
        fsize = 4
        for mal in axes.get_yticklabels(minor=False):
            mal.set_fontsize(fsize)

        # 辅助坐标点
        # ----------------------------------------------------------------------------

        yMinorLocator = FixedLocator(numpy.array(minorticks))

        # 确定 Y 轴的 MinorFormatter
        def y_minor_formatter(num, pos=None):
            return str(round(num, 1))

        yMinorFormatter = FuncFormatter(y_minor_formatter)

        # 设定 Y 轴的 Locator 和 Formatter
        yaxis.set_minor_locator(yMinorLocator)
        yaxis.set_minor_formatter(yMinorFormatter)


        # 设定 Y 轴辅助坐标点的样式
        for mil in axes.get_yticklabels(minor=True):
            mil.set_visible(False)

    def plot_candlestick(self):
        '''
        绘制 K 线
        '''
        axes = self._Axes

        xindex = self._xindex

        up = self.up
        down = self.down
        side = self.side

        #   绘制 K 线部分
        # ==================================================================================================================================================
        '''
        #   对开收盘价进行视觉修正
        for idx, poc in enumerate(self._zipoc):
            if poc[0] == poc[1] and None not in poc:
                variant = int(round((poc[1] + 1000) / 2000.0, 0))
                self.open[idx] = poc[0] - variant  # 稍微偏离一点，使得在图线上不致于完全看不到
                self.close[idx] = poc[1] + variant
        '''
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


    #计算x轴坐标
    #每小时，0，15，30，45分为主要坐标
    #每根K线为次要坐标
    def _compute_xparams(self):

 #       quotes = self._pdata
        #   设定 X 轴上的坐标
        # ==================================================================================================================================================

        timetmp=[]
        for t in self.time:timetmp.append(t[11:19])
        timelist = [datetime.time(int(hr), int(ms), int(sc)) for hr, ms, sc in
                    [dstr.split(':') for dstr in timetmp]]

        ''''
        # 确定 X 轴的 MajorLocator
        mdindex = []  # 每个月第一个交易日在所有日期列表中的 index
        allyears = set([d.year for d in timelist])  # 所有的交易年份

        for yr in sorted(allyears):
            allmonths = set([d.month for d in timelist if d.year == yr])  # 当年所有的交易月份
            for mon in sorted(allmonths):
                monthday = min([dt for dt in timelist if dt.year == yr and dt.month == mon])  # 当月的第一个交易日
                mdindex.append(timelist.index(monthday))
        
        xMajorLocator = FixedLocator(numpy.array(mdindex))
        '''
        i=0
        minindex=[]
        for min in timelist:
            if min.minute%15==0:minindex.append(i)
            i+=1
        xMajorLocator=FixedLocator((numpy.array(minindex)))
        #xMajorLocator = FixedLocator(minindex)

        # 确定 X 轴的 MinorLocator
        '''
        wdindex = {}  # value: 每周第一个交易日在所有日期列表中的 index; key: 当周的序号 week number（当周是第几周）

        for d in datelist:
            isoyear, weekno = d.isocalendar()[0:2]
            dmark = isoyear * 100 + weekno
            if dmark not in wdindex:
                wdindex[dmark] = datelist.index(d)

        wdindex = sorted(wdindex.values())
        '''
        wdindex=numpy.arange(self.length)
        xMinorLocator = FixedLocator(wdindex)


        # 确定 X 轴的 MajorFormatter 和 MinorFormatter
        def x_major_formatter(idx, pos=None):
            return timelist[int(idx)].strftime('%H:%M:%S')

        def x_minor_formatter(idx, pos=None):
            return timelist[int(idx)].strftime('%M:%S')

        xMajorFormatter = FuncFormatter(x_major_formatter)
        xMinorFormatter = FuncFormatter(x_minor_formatter)

        '''
        x_major_formatter=[]
        x_minor_formatter=[]
        for t in timelist:
            x_major_formatter.append(t.strftime('%H:%M:%S') )
            x_minor_formatter.append(t.strftime('%M:%S'))
        xMajorFormatter=FixedFormatter(x_major_formatter)
        xMinorFormatter=FixedFormatter(x_minor_formatter)
        '''

        return {'xMajorLocator': xMajorLocator,
                'xMinorLocator': xMinorLocator,
                'xMajorFormatter': xMajorFormatter,
                'xMinorFormatter': xMinorFormatter,
                'mdindex': minindex,
                'wdindex': wdindex
                }

    def _compute_rect(self):
        '''

        '''
        pdata = self._pdata
        '''
        x_left = self._xsize_left
        x_right = self._xsize_right
        y_top = self._ysize_top
        y_bottom = self._ysize_bottom
        x_all = self._xsize
        y_all = self._ysize

        y_gap1 = self._ysize_gap1  # basic 与 financial 之间的空隙
        y_gap2 = self._ysize_gap2  # toratefs 与 price 之间的空隙

        x_basic, y_basic = self.get_size()

        rect = ((x_left + (x_all - x_left - x_right - x_basic) / 2) / x_all, (y_all - y_top - y_basic) / y_all,
                    x_basic / x_all, y_basic / y_all)  # K线图部分
        '''
        rect=[0.1,0.1,0.8,0.8]

        return rect

if __name__ == '__main__':

    pdata = pd.read_csv('d:\data_1m.csv', index_col='index')

    myfig = PlotK(pdata=pdata)
    myfig.plot_candlestick()
    plt.show()
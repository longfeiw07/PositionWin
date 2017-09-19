# -*- coding: utf-8 -*-
import pandas as pd

d = {'one': pd.Series([1., 2., 3.], index=['a', 'b', 'c']), 'two': pd.Series([1., 2., 3., 4.], index=['a', 'b', 'c', 'd'])}
df = pd.DataFrame(d)
print df
print '============================================='
#访问某一行
#print df.iloc[1]
#print df.iloc[-1]
#print df.ix[-1,'b']#访问具体某个位置
'''
#清阶行
def cleanDF(df):
    row = df.shape[0]
    for i in range(row):
        df.drop(i, inplace=True)

d2 = {'one': pd.Series([1., 2., 3.]), 'two': pd.Series([1., 2., 3., 4.])}
df2 = pd.DataFrame(d2)
print df2
cleanDF(df2)
print df2
print '=============================================='
data=pd.DataFrame([[1,2,3],[4,5,6]])
print data
print data.drop(0)
'''
'''
#增加一行
self.dailyBarMin.loc[self.dailyBarMin.shape[0]] = \
            [self.dailyBar.ix[rownum - self.K_min]['strdatetime'],
             self.dailyBar.ix[rownum - self.K_min]['utcdatetime'],
             self.dailyBar.ix[rownum - self.K_min]['open'],  # 取合并周期内第一条K线的开盘
             max(self.dailyBar.iloc[rownum - self.K_min:rownum]['high']),  # 合并周期内最高价
             min(self.dailyBar.iloc[rownum - self.K_min:rownum]['low']),  # 合并周期内的最低价
             bar.close,  # 最后一条K线的收盘价
             bar.position, # 最后一条K线的仓位值
             sum(self.dailyBar.iloc[rownum -self.K_min:rownum]['volume'])] #v1.2版本加入成交量数据
'''


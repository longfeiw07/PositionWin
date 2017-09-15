# -*- coding: utf-8 -*-
import pandas as pd

d = {'one': pd.Series([1., 2., 3.], index=['a', 'b', 'c']), 'two': pd.Series([1., 2., 3., 4.], index=['a', 'b', 'c', 'd'])}
df = pd.DataFrame(d)
print df
print '============================================='
#访问某一行
#print df.iloc[1]
#print df.iloc[-1]
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



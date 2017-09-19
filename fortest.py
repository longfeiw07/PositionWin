# -*- coding: utf-8 -*-
import time
import datetime  # 导入日期时间模块

'''
时间处理：
# 先处理时间，判断当前时间是否在当天晚上21点到24点之间，如果是，start time为当天21点，如果不是，start time为前一天21天
# end time为当前时间
cTime = time.strftime("%H:%M:%S")
cDate = time.strftime("%Y-%m-%d")
if (cDate+' '+cTime)> (cDate+' 21:00:00'):
    startTime = cDate+" 21:00:00"
    endTime=cDate+' '+cTime
else:
    startTime =str(datetime.date.today()-datetime.timedelta(days=1))+" 21:00:00"
    endTime=cDate+' '+cTime

d1 = datetime.datetime(2017, 8, 5,15,01,0)
d2 = datetime.datetime(2017, 8, 5,15,06,0)
print d1
print d2
print (d2-d1).seconds

d3=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(1502802000))

print 'd3'
print d3

print datetime.datetime.fromtimestamp(1502802000)
print datetime.datetime.fromtimestamp(1502802000-60)
'''
'''
s='DCE.J.bar.60'
a,b,c= s.split('.',2)
print a
print b
print c
'''
start_time="2017-07-04 09:00:00"
d, t = start_time.split(' ', 1)
y, m, d = d.split('-', 2)
d=datetime.date(int(y),int(m),int(d))
print d
# -*- coding: utf-8 -*-
import time
import datetime  # 导入日期时间模块

# 先处理时间，判断当前时间是否在当天晚上21点到24点之间，如果是，start time为当天21点，如果不是，start time为前一天21天
# end time为当前时间
cTime = time.strftime("%H:%M:%S")
cDate = time.strftime("%Y-%m-%d")
print cTime
if (cDate+' '+cTime)> (cDate+' 21:00:00'):
    startTime = cDate+" 21:00:00"
    endTime=cDate+' '+cTime
else:
    startTime =str(datetime.date.today()-datetime.timedelta(days=1))+" 21:00:00"
    endTime=cDate+' '+cTime

print startTime
print endTime


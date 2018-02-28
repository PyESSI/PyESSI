# -*- coding: utf-8 -*-


from utils.dateTime import *

iniDate =  datetime.date(1996,1,1)
endDate = datetime.date(2000,12,31)
dayCount = endDate.toordinal() - iniDate.toordinal() + 1
daily = dailyRange('19960101', '20001231')

dailyfile=open(r'D:\pyESSITest\DCBAM\Forcing\daily.txt','a')
for i in range(dayCount):
    dailyfile.write(daily[i]+'\n')
dailyfile.close()
# -*- coding: utf-8 -*-
"""
Created Dec 2017

@author: Hao Chen

Functions:
    dailyRange:
    monthlyRange:

"""

# load needed python modules
import datetime
from numpy import *


# generate daily time series
# usage: daily = dailyRange('20080101', '20161231')
def dailyRange(start, end, step=1, format="%Y%m%d"):
    strPTime, strFTime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strPTime(end, format) - strPTime(start, format)).days + 1
    return [strFTime(strPTime(start, format) + datetime.timedelta(i), format) for i in range(0, days, step)]


# generate monthly time series
# usage: monthly = monthRange(2008, 2016)
def monthlyRange(startYear, endYear):
    monthly = []
    for year in range(startYear, endYear + 1):
        for month in range(1, 13):
            if month < 10:
                month = '0' + str(month)
            else:
                month = str(month)
            monthly.append(str(year) + month)
    return monthly




# main test
# iniDate =  datetime.date(2008,1,1)
# endDate = datetime.date(2016,12,31)
# dayCount = endDate.toordinal() - iniDate.toordinal() + 1
# daily = dailyRange('20080101', '20161231')
# print(dayCount)
# print(daily)
# monthly = monthlyRange(2008,2016)
# print(monthly)

def CheckLeapYear(year):
    '''
    判断输入年份是否是闰年
    :param year: 需判断年份
    :return: true -- 是闰年；false -- 不是闰年
    '''
    if year < 0:
        raise Exception("year must large than 0!")
    if year % 4 == 0:  # Is it a century?
        if year % 100 == 0:  # If a century, must be evenly divisible by 400.
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def GetDayNum(date):
    '''
    由日期获得在一年内的天数
    :param date: yyyymmdd
    :return:
    '''
    dd = datetime.datetime.strptime(date, "%Y%m%d")
    return dd.timetuple().tm_mday()

# -*- coding: utf-8 -*-

"""
@Class: CSolarRadiation
@Author: Huiran Gao
@Functions:
    计算太阳辐射

Created: 2018-03-01
Revised:
"""

# load needed python modules
import utils.config
import math
from modules.Climate.PET import *
from utils.dateTime import CheckLeapYear, GetDayNum


#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*             太阳辐射类 -- CSolarRadiation	  	*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *                功能：计算太阳辐射               *   |
# | *         Calculate the solar irradiation       *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CSolarRadiation():
    def __init__(self, curForcingFilename, lat, shour=10):
        # curForcingFilename: yyyymmdd
        self.iYear = curForcingFilename[0:4]  # used to determine where a year is a leap year and has 29 days in Feb.
        self.iDn = GetDayNum(curForcingFilename)  # the number of a day in one year,ie. dn=1 for 1 Jan and dn=365 for 31 Dec
        self.dSHour = shour  # solar hour
        self.dLat = lat  # the latitude of the weather station(in degree)
        self.dSd = self.SolarDeclination()  # the solar declination(in radiation)

    def SolarDeclination(self):
        '''
        the solar declination value for a given day in a given year
        :return:
        '''
        bLeap = CheckLeapYear(self.iYear)
        if bLeap:
            if self.iDn > 59:
                # in leap year, 29 Feb is treated as 28 Feb and all other days after 29 Feb will be forward one day
                self.iDn -= 1
        dtemp = 0.4 * math.sin(2 * math.pi * (self.iDn - 82) / 365.)
        dret = math.asin(dtemp)
        # in radiation
        return dret

    def EarthSunDist(self):
        '''
        the distance between earth and sun per astronomical unit(AU)
        :return:
        '''
        bLeap = CheckLeapYear(self.iYear)
        if bLeap:
            if self.iDn > 59:
                # in leap year, 29 Feb is treated as 28 Feb and all other days after 29 Feb will be forward one day
                self.iDn -= 1
        dret = 1 + 0.033 * math.cos(2 * math.pi * self.iDn / 365.)
        return dret

    def SunRiseTime(self):
        '''
        Calculate the time sun is up,the time interval is between sunrise to solar noon
        :return:
        '''
        dret = math.acos(-math.tan(self.dSd) * math.tan(self.dLat / RAD)) / AV
        return dret

    def SunSetTime(self):
        '''
        Calculate the time sun is down,the time interval is between solar noon to sunset
        :return:
        '''
        dret = math.acos(-math.tan(self.dSd) * math.tan(self.dLat / RAD)) / AV
        return dret

    def DayLength(self):
        '''
        The total daylength at latitudes between 66.5 and -66.5
        :return:
        '''
        dret = 2 * math.acos(-math.tan(self.dSd) * math.tan(self.dLat / RAD)) / AV
        return dret

    def SunHeight(self):
        '''
        The height between the sun and a horizontal surface on the earth's surface
        :return:
        '''
        ha = AV * self.dSHour  # the hour angle
        dret = math.sin(self.dSd) * math.sin(self.dLat / RAD) + math.cos(self.dSd) * math.cos(
            self.dLat / RAD) * math.cos(ha)
        return dret

    def ExtraTerrRad(self):
        '''
        Calculate the extraterrestrial radiation in given conditions
        :return:
        '''
        tsr = self.SunRiseTime()
        dist = self.EarthSunDist()
        ha = AV * tsr
        dret = (24 / math.pi) * I0 * dist * (
            ha * math.sin(self.dSd) * math.sin(self.dLat / RAD) + math.cos(self.dSd) * math.cos(
                self.dLat / RAD) * math.sin(ha))
        return dret

    def RealSolarRadMax(self, dscale):
        '''
        the real solar radiation under cloudless skies assumes that 100*(1-dscale)%
        of the solar radiation is absorbed or scattered by atmosphere
        :param dscale:
        :return:
        '''
        Q0 = self.ExtraTerrRad()
        dret = Q0 * dscale
        return dret

    def RealSolarRad(self, slrpercent, a, b, dabsorb):
        '''
        ---
        :param slrpercent: sunlight percentage(日照百分率)
        :param a: the experiential coefficient ie: y = a + b * s
        :param b: the experiential coefficient ie: y = a + b * s
        :param dabsorb:
        :return:
        '''
        # Q0 may be the extraterrestrial radiation or the ideal atmospherical radiation
        # or the clear sky total solar radiation
        Q0 = self.RealSolarRadMax(dabsorb)
        dret = Q0 * (a + b * slrpercent)
        return dret

# -*- coding: utf-8 -*-

"""
@Class: CWaterVaporFAOPM
@Author: Huiran Gao
@Functions:
    计算与水汽相关的变量

Created: 2018-03-01
Revised:
"""

# load needed python modules
from util.fileIO import *
import util.config
import math
from modules.Climate.PET import *


#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*          水汽相关类 -- CWaterVaporFAOPM        	*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *            功能：计算与水汽相关的变量            *   |
# | * Ccalculate variances related with water vapor *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CWaterVaporFAOPM():
    def __init__(self, tav, elev, tmx, tmn):
        self.dTav = tav
        self.dElev = elev
        self.dTmx = tmx
        self.dTmn = tmn
        self.dSvp = self.SatuVapPressure()

    def SatuVapPressure(self):
        '''
        Calculate saturation vapor pressure
        :return:
        '''
        etmx = self.ESatuTemp(self.dTmx)
        etmn = self.ESatuTemp(self.dTmn)
        dsvap = (etmx + etmn) / 2.
        return dsvap

    def ESatuTemp(self, dtmp):
        '''
        ---
        :param dtmp:
        :return:
        '''
        dret = 0.611 * math.exp(17.27 * dtmp / (dtmp + 237.3))
        return dret

    def RelativeHmd(self, avp):
        '''
        ---
        :param avp: actual
        :return:
        '''
        hmd = avp / self.dSvp
        return hmd

    def LatHeatVapor(self):
        '''
        Calculate the latent heat of vaporization (MJ / kg)
        :return:
        '''
        lmt = 2.45
        return lmt

    def AirPressureInSite(self):
        '''
        Calculate the air pressure (kPa)
        :return:
        '''
        ap = 101.3 * pow((293. - 0.0065 * self.dElev) / 293., 5.62)
        return ap

    def AirPressureInPlain(self, dn):
        '''
        Calculate the air pressure (kPa)
        本公式可输出逐日大气压, 公式由汉江的32个气象站拟合得到，高程范围200～1600米!!!???
        :return:
        '''
        ap = 101.3 - 0.0109 * self.dElev + (1.1702 - 0.0005 * self.dElev) * math.cos(2 * math.pi * dn / 365.)
        return ap

    def PsychroConst(self):
        '''
        Calculate psychrometric constant(kPa/C)
        :return:
        '''
        ap = self.AirPressureInSite()
        lmt = self.LatHeatVapor()
        gm = 0.00163 * ap / lmt
        return gm

    def PsychroConst_dn(self, dn):
        '''
        Calculate psychrometric constant(kPa/C)
        :return:
        '''
        ap = self.AirPressureInPlain(dn)
        lmt = self.LatHeatVapor()
        gm = 0.00163 * ap / lmt
        return gm

    def ActVapPressure(self, realhumd):
        '''
        ---
        :param self:
        :param realhumd:
        :return:
        '''
        return realhumd * self.dSvp

    def ActVapPressureByTMxMn(self, realhmd):
        '''
        ---
        :param self:
        :param realhmd:
        :return:
        '''
        dret = 50. / self.ESatuTemp(self.dTmx) + 50. / self.ESatuTemp(self.dTmn)
        dret = realhmd * 100 / dret
        return dret

    def TmpVapCurveSlp(self):
        '''
        the slope of the saturatiion vapor pressure curve
        :param self:
        :return:
        '''
        dlta = 4098 * self.dSvp / (pow((self.dTav + 237.3), 2))
        return dlta


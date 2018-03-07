# -*- coding: utf-8 -*-

"""
@Class: CHortonInfil
@Author: Huiran Gao
@Functions:
    土壤水下渗(霍顿超渗产流理论)

Created: 2018-02-28
Revised:
"""

# load needed python modules
import math

import util.config
from modules.Hydro.SoilPara import *
from util.fileIO import *
from modules.Hydro.Hydro import gSoil_GridLayerPara


# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         土壤水下渗类 -- CHortonInfil			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *         功能：利用Horton下渗曲线法           	*   |
# |	*				土壤水下渗量  					*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CHortonInfil:
    def __init__(self):
        self.m_dERR = 0.
        self.m_dK = 0.
        self.m_dFc = 0.
        self.m_dF0 = 0.

        self.m_dFt = 0  # 土壤水下渗量
        self.m_dPreSoilW = 0  # 初始土壤含水量

    def SetGridPara(self, row, col, dSoilW, dErr, soil):
        '''
        设置参数
        :param dSoilW:
        :param dErr:
        :return:
        '''
        self.currow = row
        self.curcol = col
        self.m_dPreSoilW = dSoilW
        self.m_dERR = dErr
        self.m_Soil = soil

        self.m_dK = gSoil_GridLayerPara["Horton_K"][self.currow][self.curcol]
        self.m_dF0 = gSoil_GridLayerPara["SP_Init_F0"][self.currow][self.curcol]
        self.m_dFc = gSoil_GridLayerPara["SP_Stable_Fc"][self.currow][self.curcol]

        return 0

    def HortonExcessRunoff(self):
        '''
        计算霍顿超渗产流
        :return:
        '''
        dt0 = self.m_dPreSoilW / self.m_dF0
        dtmpsw = self.DTempSoilW(dt0)
        dthet = math.fabs(self.m_dPreSoilW - dtmpsw)
        num = 0

        self.m_dFt = self.m_dF0 - self.m_dK * (dtmpsw - self.m_dFc * dt0)
        dt0 += dthet / self.m_dFt
        dtmpsw = self.DTempSoilW(dt0)
        dthet = math.fabs(self.m_dPreSoilW - dtmpsw)
        num += 1

        while dthet > self.m_dERR:
            if num > 500:
                break
            self.m_dFt = self.m_dF0 - self.m_dK * (dtmpsw - self.m_dFc * dt0)
            dt0 += dthet / self.m_dFt
            dtmpsw = self.DTempSoilW(dt0)
            dthet = math.fabs(self.m_dPreSoilW - dtmpsw)
            num += 1

        return self.m_dFt

    def DTempSoilW(self, dt):
        '''
        求时段dt下的土壤含水量变化
        :param dt:
        :return:
        '''
        dret = self.m_dFc * dt + (1 - math.exp(-1 * self.m_dK * dt)) * (self.m_dF0 - self.m_dFc) / self.m_dK
        return dret

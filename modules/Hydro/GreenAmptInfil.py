# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Functions:
    class: CCanopyStorage


"""


# load needed python modules
from utils.fileIO import *
from modules.SoilPara import *
import utils.config
import math



# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         栅格产流类 -- CGreenAmptInfil			*	|
# |   *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# |   *         功能：利用Green-Ampt Mein-Larson法	*   |
# |	*				计算超渗产流量					*	    |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CGreenAmptInfil:

    # 功能:    -- 设置Green - Ampt法计算参数
    def SetGridPara(self, currow, curcol, timelen, Prerateinf, Precumr, Prerintns, Precuminf, Preexcum, pcp, Cp):
        self.m_row = currow
        self.m_col = curcol
        self.m_timeLen = timelen
        self.m_Pcp = pcp
        self.m_dPreRateinf = Prerateinf
        self.m_dPrecumr = Precumr
        self.m_dPrerintns = Prerintns
        self.m_dPrecuminf = Precuminf
        self.m_dPreexcum = Preexcum

        self.m_dEhc = self.EffHydroConductivity(Cp)

    def GreenAmptExcessRunoff(self):
        self.m_dSoilw = 0.
        self.m_dSurfQ = 0.

        soilTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep +  utils.config.SoilFileName)
        pGridSoilInfo =  SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(soilTemp.data[self.m_row][self.m_col]) + '.sol')
        dthet = pGridSoilInfo.SoilWaterDeficitPercent()
        psidt = 0.
        psidt = dthet * pGridSoilInfo.SP_WFCS

        drateinf = 0.
        drintns = 0.
        dcumr = 0.
        dcuminf = 0.
        dexinc = 0.
        dexcum = 0.

        dt = self.m_timeLen / 60.
        dcumr = self.m_dPrecumr + self.m_Pcp
        drintns = self.m_Pcp / dt

        if self.m_dPreRateinf <= 0.:
            self.m_dPreRateinf    = self.m_dEhc
        if self.m_dPrecumr <= 0.:
            self.m_dPrecumr = 0.
        if self.m_dPrerintns <= 0.:
            self.m_dPrerintns    = drintns
        if self.m_dPrecuminf <= 0.:
            self.m_dPrecuminf    = 0.
        if self.m_dPreexcum <= 0.:
            self.m_dPreexcum = 0.

        if drintns <= self.m_dPreRateinf:
            self.m_dSoilw = self.m_dPrerintns * dt
            dcuminf = self.m_dPrecuminf + self.m_dSoilw
            self.m_dSurfQ = 0.
            if self.m_dPreexcum > 0.:
                dexcum = self.m_dPreexcum
                dexinc = 0.
            else:
                dexcum = 0.
                dexinc = 0.
        else:
            dtmp = 0.
            bExistLoop = False
            while not bExistLoop:
                df = 0.
                df = self.m_dPrecuminf + self.m_dEhc * dt + psidt * math.log((dtmp + psidt) / (self.m_dPrecuminf + psidt));
                if math.fabs(df - dtmp) <= 0.001:
                    dcuminf = df
                    dexcum = dcumr - dcuminf
                    if dexcum <= 0:
                        dexcum = 0.
                        dexinc = dexcum - self.m_dPreexcum
                    if dexinc < 0.:
                        dexinc = 0.
                        self.m_dSurfQ = self.m_dSurfQ + dexinc
                        bExistLoop = True
                else:
                    dtmp = df
            if self.m_dPrecuminf > 0.:
                self.m_dSoilw = dcuminf - self.m_dPrecuminf

        if dcuminf <= 0.00001:
            drateinf = self.m_dEhc
        else:
            drateinf = self.m_dEhc * (psidt / (dcuminf + 0.00001) + 1)
            self.m_dPreRateinf = drateinf
            self.m_dPrecumr = dcumr
            self.m_dPrerintns = drintns
            self.m_dPrecuminf = dcuminf
            self.m_dPreexcum = dexcum


    def EffHydroConductivity(self,Cp):
        soilTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.SoilFileName)
        pGridSoilInfo = SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(soilTemp.data[self.m_row][self.m_col]) + '.sol')

        dehc = 0.
        if Cp == -1.:
            dehc = pGridSoilInfo.SP_Sat_K / 2.
        else:
            dehc = pGridSoilInfo.SP_Sat_K / (1 + math.exp(0.2 * Cp))

        if dehc <= 0.:
            dehc = 0.001
        return dehc




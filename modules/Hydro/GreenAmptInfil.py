# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Class:
    CGreenAmptInfil
        functions:
            SetGridPara(self, currow, curcol, timelen, Prerateinf, Precumr, Prerintns, Precuminf, Preexcum, pcp, Cp)
            GreenAmptExcessRunoff(self)
            EffHydroConductivity(self, Cp=-1.)


"""

# load needed python modules
import math

import util.config
from modules.Hydro.SoilPara import *
from modules.Hydro.Hydro import gSoil_GridLayerPara


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
    def SetGridPara(self, currow, curcol, timelen, Prerateinf, Precumr, Prerintns, Precuminf, Preexcum, pcp, Cp=0.):
        '''
        功能:    -- 设置Green - Ampt法计算参数
        :param currow:
        :param curcol:
        :param timelen:
        :param Prerateinf:
        :param Precumr:
        :param Prerintns:
        :param Precuminf:
        :param Preexcum:
        :param pcp:
        :param Cp:
        :return:
        '''
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


    def GreenAmptExcessRunoff(self, row, col):
        self.m_dSoilw = 0.
        self.m_dSurfQ = 0.
        self.m_row = row
        self.m_col = col

        self.SP_Por = gSoil_GridLayerPara.SP_Por[self.m_row][self.m_col]
        self.SP_Sw = gSoil_GridLayerPara.SP_Sw[self.m_row][self.m_col]
        self.SP_Fc = gSoil_GridLayerPara.SP_Fc[self.m_row][self.m_col]
        self.SP_WFCS = gSoil_GridLayerPara.SP_WFCS[self.m_row][self.m_col]

        dthet = (1.0 - self.SP_Sw / self.SP_Fc) * self.SP_Por
        psidt = 0.
        psidt = dthet * self.SP_WFCS

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
            self.m_dPreRateinf = self.m_dEhc
        if self.m_dPrecumr <= 0.:
            self.m_dPrecumr = 0.
        if self.m_dPrerintns <= 0.:
            self.m_dPrerintns = drintns
        if self.m_dPrecuminf <= 0.:
            self.m_dPrecuminf = 0.
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
            dtmp = self.m_dEhc * dt
            bExistLoop = False

            # do while
            df = 0.
            df = self.m_dPrecuminf + self.m_dEhc * dt + psidt * math.log((dtmp + psidt) / (self.m_dPrecuminf + psidt))
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

            while not bExistLoop:
                df = 0.
                df = self.m_dPrecuminf + self.m_dEhc * dt + psidt * math.log(
                    (dtmp + psidt) / (self.m_dPrecuminf + psidt))
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

        gSoil_GridLayerPara.SP_Por[self.m_row][self.m_col] = self.SP_Por
        gSoil_GridLayerPara.SP_Sw[self.m_row][self.m_col] = self.SP_Sw
        gSoil_GridLayerPara.SP_Fc[self.m_row][self.m_col] = self.SP_Fc
        gSoil_GridLayerPara.SP_WFCS[self.m_row][self.m_col] = self.SP_WFCS

    def EffHydroConductivity(self, Cp=-1.):
        '''
        :param Cp:
        :return:
        '''
        self.SP_Sat_K = gSoil_GridLayerPara.SP_Sat_K[self.m_row][self.m_col]

        dehc = 0.
        if Cp == -1.:
            dehc = self.SP_Sat_K / 2.
        else:
            dehc = self.SP_Sat_K / (1 + math.exp(0.2 * Cp))

        if dehc <= 0.:
            dehc = 0.001
        return dehc

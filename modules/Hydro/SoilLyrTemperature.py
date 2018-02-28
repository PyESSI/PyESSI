# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Functions:
    class: CSoilLyrTemperature


"""


# load needed python modules
import math
import numpy as np


class CSoilLyrTemperature:

    def SetLyrPara(self, soilbd, soilsw, totaldepth, dBCV, albedo, slr, tmax, tmin, tmean, tprev, tmpan):
        self.m_dSoilBD = soilbd
        self.m_dSoilSW = soilsw
        self.m_dSoilLyrDepth = totaldepth
        self.m_dBCV = dBCV
        self.m_dAlbedo = albedo
        self.m_dSlr = slr
        self.m_dTmpMX = tmax
        self.m_dTmpMN = tmin
        self.m_dTmpMean = tmean
        self.m_dTmpPrev = tprev
        self.m_dTmpAn = tmpan

    def GetLyrTmpValue(self):
        dret = 0.
        tlag = 0.8

        f = 0.
        dp = 0.
        f = self.m_dSoilBD / (self.m_dSoilBD + 686. * math.exp(-5.63 * self.m_dSoilBD))
        dp = 1000. + 2500. * f

        ww = 0.
        wc = 0.
        ww = 0.356 - 0.144 * self.m_dSoilBD
        wc = self.m_dSoilSW / (ww * self.m_dSoilLyrDepth)
        b = 0.
        f = 0.
        dd = 0.
        b = math.log(500. / dp)
        f = math.exp(b * pow((1. - wc) / (1. + wc), 2))
        dd = f * dp
        st0 = 0.
        tbare = 0.
        tcov = 0.
        tmp_srf = 0.
        st0 = (self.m_dSlr * (1. - self.m_dAlbedo) - 14.)/ 20.
        tbare = self.m_dTmpMean + 0.5 * (self.m_dTmpMX - self.m_dTmpMN) * st0
        tcov = self.m_dBCV * self.m_dTmpPrev + (1. - self.m_dBCV) * tbare

        if self.m_dBCV > 0.01:
            tmp_srf = np.min([tbare, tcov])
        else:
            tmp_srf = tbare
        df = 0.
        zd = self.m_dSoilLyrDepth
        zd = zd / dd
        df = zd / (zd + math.exp(-.8669 - 2.0775 * zd))
        dret = tlag * self.m_dTmpPrev + (1. - tlag) * (df * (self.m_dTmpAn - tmp_srf) + tmp_srf)
        return dret



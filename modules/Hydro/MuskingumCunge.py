# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Functions:
    class: CMuskingumCunge


"""


# load needed python modules
import utils.config


class CMuskingumCunge:

    # 设置汇流计算参数
    def SetRoutingPara(self, Vflow, dSlp,deltaX, deltaT, riverType, Q11, Q12, Q21,  dq, dB, x, k):
        self.m_dVflow = Vflow
        self.m_dSlp = dSlp
        self.m_iRriverType = riverType
        self.m_deltaT = deltaT
        self.m_deltaX = deltaX
        self.m_Q11 = Q11
        self.m_Q12 = Q12
        self.m_Q21 = Q21
        self.m_dQ = dq
        self.m_dB = dB
        self.m_X = x
        self.m_K = k / 60.

    # 汇流结果
    def RoutingOutQ(self):
        m_Q22 = 0.
        self.CalcMuskRoutingCoeff()
        self.m_Q22 = self.C1 * self.m_Q11 + self.C2 * self.m_Q12 + self.C3 * self.m_Q21 + self.C4 * self.m_dQ
        # ifdef _DCBAM
        if self.m_Q22 < 0:
            print("MuskingumCunge 汇流结果为负")

        return m_Q22

    def CalcMuskRoutingCoeff(self):
        self.C1 = 0.3333
        self.C2 = 0.3333
        self.C3 = 0.3333
        self.m_dKWV = self.KinematicWaveV(self.m_dVflow)
        self.m_dDiffC = self.DiffusiveCoeff()

        denominator = 1.
        denominator = self.m_K * (1 - self.m_X) + 0.5 * self.m_deltaT
        self.C1 = (self.m_X * self.m_K + 0.5 * self.m_deltaT) / denominator
        self.C2 = (0.5 * self.m_deltaT - self.m_X * self.m_K) / denominator
        self.C3 = (self.m_K * (1 - self.m_X) - 0.5 * self.m_deltaT) / denominator
        self.C4 = self.m_deltaT * self.m_deltaX / (denominator)

    # 计算运动波速
    def KinematicWaveV(self,vflow):
        dKWVC = self.GetKWVCoeff(self.m_iRriverType)
        dKWV = vflow * dKWVC
        return dKWV

    # 计算扩散系数
    def DiffusiveCoeff(self):
        dDC = 1.
        if self.m_dSlp == 0.:
            self.m_dSlp = 0.0001
        dDC = (self.m_Q12 + self.m_dQ * self.m_dB) / ( 2. * self.m_dSlp * self.m_dB)
        return dDC

    def GetKWVCoeff(self, rivertype):
        dcoeff = 1.
        if rivertype == utils.config.M_RIVER_SECTION_TRIANGLE:
            dcoeff = 1.33
        elif rivertype == utils.config.M_RIVER_SECTION_RECTANGLE:
            dcoeff = 1.67
        elif rivertype == utils.config.M_RIVER_SECTION_PARABOLA:
            dcoeff = 1.44
        elif rivertype == utils.config.M_RIVER_SECTION_HILLSIDE:
            dcoeff = 3.0
        elif rivertype == utils.config.C_RIVER_SECTION_TRIANGLE:
            dcoeff = 1.25
        elif rivertype == utils.config.C_RIVER_SECTION_RECTANGLE:
            dcoeff = 1.50
        elif rivertype == utils.config.C_RIVER_SECTION_PARABOLA:
            dcoeff = 1.33
        elif rivertype == utils.config.C_RIVER_SECTION_HILLSIDE:
            dcoeff = 2.50
        else:
            dcoeff = 1.5
        return dcoeff










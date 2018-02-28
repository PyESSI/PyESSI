# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Functions:
    class: CMuskingum


"""


# load needed python modules
class CMuskingum:

    def SetRoutingPara(self,  deltaT, Q11, Q12, Q21, x, k):
        self.m_deltaT = deltaT
        self.m_Q11 = Q11
        self.m_Q12 = Q12
        self.m_Q21 = Q21
        self.m_X = x
        self.m_K = k

    # 计算马斯京根系数
    def CalcMuskRoutingCoeff(self):
        denominator = 1.
        denominator = self.m_K * (1 - self.m_X) + 0.5 * self.m_deltaT
        self.C1 = (self.m_X * self.m_K + 0.5 * self.m_deltaT) / denominator
        self.C2 = (0.5 * self.m_deltaT - self.m_X * self.m_K) / denominator
        self.C3 = (self.m_K * (1 - self.m_X) - 0.5 * self.m_deltaT) / denominator

    def RoutingOutQ(self):
        self.m_Q22 = 0.
        self.CalcMuskRoutingCoeff()
        self.m_Q22 = self.C1 * self.m_Q11 + self.C2 * self.m_Q12 + self.C3 * self.m_Q21
        return self.m_Q22


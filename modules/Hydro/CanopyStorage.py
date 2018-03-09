# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Class:
    CCanopyStorage
        functions:
            __init__(self)
            SetGridValue(self, dLai, dpcp, dCd, pcpcoeff)
            CanopyStore(self)
            CrownIC(self)
            PcpInterCCoeff(self)


"""

# load needed python modules
import math


# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	 ***********************************************    |
# |	 *										       *	|
# |	 *         林冠截留类 -- CCanopyStorage        *	    |
# |                                                     |
# |	 ***********************************************    |
# |	 *                                             *	|
# |    *         功能：计算降雨时的林冠截留量		   *    |
# |	 *										       *	|
# |    ***********************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++*/
class CCanopyStorage:
    def __init__(self):
        self.m_dPcpCoeff = 0.046
        self.m_dCd = 0.7
        self.m_dPcp = 0.
        self.m_dLAI = 0.

    def SetGridValue(self, dLai, dpcp, dCd, pcpcoeff):
        '''
        功能：设置栅格上林冠截留参数
        :param dLai:
        :param dpcp:
        :param dCd:
        :param pcpcoeff:
        :return:
        '''
        self.m_dPcpCoeff = pcpcoeff
        self.m_dCd = dCd
        self.m_dPcp = dpcp
        self.m_dLAI = dLai
        if self.m_dLAI <= 0:
            self.m_dLAI = 0.001
        if self.m_dCd <= 0:
            self.m_dCd = 0.001

    # 功能：设置栅格上林冠截留参数-林冠截留量
    def CanopyStore(self):
        dret = 0.
        dCrownIC = self.CrownIC()
        dPcpCoeff = self.PcpInterCCoeff()
        dret = (dCrownIC * (1 - math.exp(-1 * dPcpCoeff * self.m_dPcp / dCrownIC))) * 1.1
        if dret > self.m_dPcp:
            dret = self.m_dPcp
        return dret

    # 功能：林冠截留能力计算
    def CrownIC(self):
        dret = 0.
        dret = 0.935 * 0.498 * self.m_dLAI - 0.00575 * self.m_dLAI * self.m_dLAI
        dret = dret * self.m_dCd
        return dret

    # 功能：降雨截留系数计算
    def PcpInterCCoeff(self):
        return self.m_dPcpCoeff * self.m_dLAI

# -*- coding: utf-8 -*-

"""
@Class: CPETInPM
@Author: Huiran Gao
@Functions:
    潜在蒸散发(彭曼公式)

Created: 2018-03-01
Revised:
"""


# load needed python modules
from utils.fileIO import *
from modules.Climate.WaterVapor import *
from modules.Climate.SolarRadiation import *
from utils.defines import *
import math

#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         潜在蒸散发类 -- CPETInPM			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *         功能：利用彭曼公式计算潜在蒸散发          *   |
# | *    Calculate potential Evaportranspiration    *   |
# | *          with Penman-Monteith method          *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CPETInPM(CPET):
    def __init__(self, tav, elev, curForcingFilename, lat):
        CPET.__init__(self, curForcingFilename, lat)
        self.dTav = tav
        self.dElev = elev
        self.dTavk = self.dTav + 273.15
        self.pwatvap = CWaterVapor(self.dTav, self.dElev)
        self.pslr = CSolarRadiation(curForcingFilename, lat)

    def CombineConst(self):
        '''
        --- By Jensen et al.(1990) to calculate K1*0.622*λ*ρ/P
        :return:
        '''
        cc = 1710 - 6.85 * self.dTav
        return cc

    def AeroDynResistance(self, wspeed):
        '''
        Aerodynamic resistance
        ses alfalfa at a height of 40 cm with a minimum leaf resisitance of 100s/m for the reference crop
        :param wspeed:
        :return:
        '''
        if (wspeed <= 0):
            wspeed = 0.01
        ra = 114. / wspeed
        return ra

    def CanopyResistance(self, co2=330):
        '''
        ---
        :param co2:
        :return:
        '''
        rc = 49 / (1.4 - 0.4 * co2 / 330)
        return rc

    def NetLongWaveRadRHmd(self, slrp, rhmd):
       '''
        ---
       :param slrp: solarlight percentage(日照百分率)
       :param rhmd: relative humidity used to calculate actual vapor pressure
       :return:
       '''
       avp = self.pwatvap.ActVapPressure(rhmd)
       self.dNetLong = -(0.9 * slrp + 0.1) * (0.34 - 0.139 * math.sqrt(avp)) * STEF_BOLTZ * math.pow(self.dTavk, 4)
       return 0

    def NetLongWaveRadAvp(self, slrp, avp):
       '''
       ---
       :param slrp: slrp - ---solarlight percentage(日照百分率)
       :param avp: acturl vapor pressure is already known
       :return:
       '''
       if avp <= 0:
           avp=0.5  # (really avp may change from 0 to 2.5 kpa)
       self.dNetLong = -(0.9 * slrp + 0.1) * (0.34 - 0.139 * math.sqrt(avp)) * STEF_BOLTZ * math.pow(self.dTavk, 4)
       return 0

    def NetLongWaveRadiationRHmd(self, slrg,  rhmd):
        '''
        ---
        :param slrg: real radiation that reaches the ground
        :param rhmd: relative humidity used to calculate actual vapor pressure
        :return:
        '''
        avp = self.pwatvap.ActVapPressure(rhmd)
        self.dNetLong = -(0.9 * slrg / self.pslr.RealSolarRadMax() + 0.1) * (0.34 - 0.139 * math.sqrt(avp)) * STEF_BOLTZ * math.pow(self.dTavk, 4)
        return 0


    def NetLongWaveRadiationAvp(self, slrg, avp):
        '''
        ---
        :param slrg: real radiation that reaches the ground
        :param avp: acturl vapor pressure is already known
        :return:
        '''
        if avp <= 0:
            avp=0.5 # (really avp may change from 0 to 2.5 kpa)
        self.dNetLong = -(0.9 * slrg / self.pslr.RealSolarRadMax() + 0.1)* (0.34 - 0.139 * math.sqrt(avp)) * STEF_BOLTZ * math.pow(self.dTavk, 4)
        return 0


    def NetRadiation(self):
        '''
        As net short wave radiation and net long wave radiation are already got, we can use this function to calculate net radiation
        :return:
        '''
        return self.dNetShort + self.dNetLong

    def PETInPMByRHmd(self, wspeed, rhmd, G):
        '''
        Calculate PET using Penman - Monteith formula
        :param wspeed:
        :param rhmd:
        :param G:
        :return:
        '''
        Hnet = self.NetRadiation()
        dlta = self.pwatvap.TmpVapCurveSlp()
        lhv = self.pwatvap.LatHeatVapor()
        comb = self.CombineConst()
        svp = self.pwatvap.SatuVapPressure()
        avp = self.pwatvap.ActVapPressure(rhmd)
        psy = self.pwatvap.PsychroConst()
        rc = self.CanopyResistance()
        ra = self.AeroDynResistance(wspeed)
        dEnergy = (dlta * (Hnet - G)) / (dlta + psy * (1 + rc / ra)) / lhv
        dAero = (psy * comb * (svp - avp) / ra) / (dlta + psy * (1 + rc / ra)) / lhv
        dPet = dEnergy + dAero
        return dPet

    def PETInPMByRHmd_dn(self, dn, wspeed, rhmd, G):
        '''
        Calculate PET using Penman - Monteith formula
        :param dn:
        :param wspeed:
        :param rhmd:
        :param G:
        :return:
        '''
        Hnet = self.NetRadiation()
        dlta = self.pwatvap.TmpVapCurveSlp()
        lhv = self.pwatvap.LatHeatVapor()
        comb = self.CombineConst()
        svp = self.pwatvap.SatuVapPressure()
        avp = self.pwatvap.ActVapPressure(rhmd)
        psy = self.pwatvap.PsychroConst_dn(dn)  # 改进点，增加dn来模拟日的变化情况
        rc = self.CanopyResistance()
        ra = self.AeroDynResistance(wspeed)
        dEnergy = (dlta * (Hnet - G)) / (dlta + psy * (1 + rc / ra)) / lhv
        dAero = (psy * comb * (svp - avp) / ra) / (dlta + psy * (1 + rc / ra)) / lhv
        dPet = dEnergy + dAero
        return dPet

    def PETByRAVP(self, wspeed, avp, G):
        '''
        ---
        :param wspeed:
        :param avp:
        :param G:
        :return:
        '''
        svp = self.pwatvap.SatuVapPressure()
        rhmd = avp / svp
        return self.PETInPMByRHmd(wspeed, rhmd, G)

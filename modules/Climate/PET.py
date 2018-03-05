# -*- coding: utf-8 -*-

"""
@Class: CPET
@Author: Huiran Gao
@Functions:
    计算潜在蒸散发

Created: 2018-03-01
Revised:
"""

# load needed python modules
import util.config
import math
from modules.Climate.SolarRadiation import *
from util.defines import *


#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         潜在蒸散发类 -- CPET        			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *              功能：计算潜在蒸散发             	*   |
# | *    Calculate potential Evaportranspiration    *   |
# |	*				                    			*   |
# |	*												*	|
# | ***************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CPET:
    def __init__(self, curForcingFilename, lat):
        self.dNetShort = 0
        self.dNetLong = 0

        self.dTav = 0
        self.dTmx = 0
        self.dTmn = 0
        self.dElev = 0
        self.dTmxk = 0
        self.dTmnk = 0
        self.dTavk = 0

        self.dEnergy = 0
        self.dAero = 0

        self.pslr = CSolarRadiation(curForcingFilename, lat)

    def NetShortWaveRadiation(self, albedo, slrg):
        '''
        ---
        :param albedo:
        :param slrg: the real solar radiation reaching the ground
        :return:
        '''
        dNetShort = slrg * (1 - albedo)
        return dNetShort

    def NetShortWaveRad(self, albedo, slrp, a=0.16, bx=0.65, dAbsorb=0.85):
        '''
        ---
        :param albedo:
        :param slrp:
        :param a:
        :param bx:
        :param dAbsorb:
        :return:
        '''
        slrg = self.pslr.RealSolarRad(slrp, a, bx, dAbsorb)
        dNetShort = slrg * (1 - albedo)
        return dNetShort

# -*- coding: utf-8 -*-

"""
@Class: CPETInDeBruin
@Author: Huiran Gao
@Functions:
    潜在蒸散发

Created: 2018-03-01
Revised:
"""

# load needed python modules
from modules.Climate.PETInPM import *
from util.defines import *
import math


#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         潜在蒸散发类 -- CPETInDeBruin			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *                功能：计算潜在蒸散发              *   |
# | *    Calculate potential Evaportranspiration    *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CPETInDeBruin(CPETInPM):
    def __init__(self, tav, elev, curForcingFilename, lat=33):
        CPETInPM.__init__(self, tav, elev, curForcingFilename, lat)
        self.dTav = tav
        self.dElev = elev

    def PETByDeBruin(self, alfa=0.95, beta=1.728, G=0):
        # slope of the saturation vapor pressure-temperature curve
        dlta = self.pwatvap.TmpVapCurveSlp()
        # psychrometric constant
        gma = self.pwatvap.PsychroConst()
        # net radiation
        dNetRad = self.NetRadiation()

        dret = alfa * dlta * (dNetRad - G) / (dlta + gma) + beta
        return dret

# -*- coding: utf-8 -*-

"""
@Class: CPETInPristley
@Author: Huiran Gao
@Functions:
    潜在蒸散发(Pristley)

Created: 2018-03-01
Revised:
"""


# load needed python modules
from utils.fileIO import *
from modules.Climate.PETInPM import *
from modules.Climate.WaterVapor import *
from modules.Climate.SolarRadiation import *
from utils.defines import *
import math

#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*         潜在蒸散发类 -- PETInPristley			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *  功能：利用Pristley-Taylor(PT)方法计算潜在蒸散发  *   |
# | *    Calculate potential Evaportranspiration    *   |
# | *        with Pristley-Taylor(PT) method        *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CPETInPristley(CPETInPM):
    def __init__(self, tav, elev, curForcingFilename, lat=33):
        CPETInPM.__init__(self, tav, elev, curForcingFilename, lat)
        self.dTav = tav
        self.dElev = elev

    def PETByPristley(self, alfa, G):
        dNetRad = self.NetRadiation()            # net radiation
        dlta = self.pwatvap.TmpVapCurveSlp()    # slope of the saturation vapor pressure - temperature curve
        gma = self.pwatvap.PsychroConst()       # psychrometric constant
        lmt = self.pwatvap.LatHeatVapor()       # latent heat of vaporization
        dret = alfa * dlta * (dNetRad - G) / (dlta + gma)
        return dret

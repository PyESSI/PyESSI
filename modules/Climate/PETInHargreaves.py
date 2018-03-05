# -*- coding: utf-8 -*-

"""
@Class: CPETInHargreaves
@Author: Huiran Gao
@Functions:
    潜在蒸散发(FAO-彭曼公式)

Created: 2018-03-05
Revised:
"""

# load needed python modules
from modules.Climate.PETInPM import *
import math


#
# /*++++++++++++++++++++++++++++++++++++++++++++++++++++|
# |														|
# |	*************************************************   |
# |	*												*	|
# |	*        潜在蒸散发类 -- CPETInHargreaves			*	|
# | *												*   |
# |                                                     |
# |	*************************************************   |
# |	*												*	|
# | *      功能：利用Hargreaves公式计算潜在蒸散发       *   |
# | *    Calculate potential Evaportranspiration    *   |
# | *             with Hargreaves method            *   |
# |	*				                    			*   |
# |	*												*	|
# |   *************************************************	|
# |														|
# |++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

class CPETInHargreaves(CPETInPM):
    def __init__(self, tav, elev, tmx, tmn, curForcingFilename, lat=33):
        CPETInPM.__init__(self, tav, elev, curForcingFilename, lat)
        self.dTav = tav
        self.dElev = elev
        self.dTmx = tmx
        self.dTmn = tmn

    def PETByHarg(self):
        dtmpdif = self.dTmx - self.dTmn
        dNetRad = self.NetRadiation()
        dExtRad = self.pslr.ExtraTerrRad()
        if dNetRad == -1:
            dret = 0.
        else:
            if dtmpdif < 0:
                dret = 0.
            else:
                dret = 0.0023 * dExtRad * math.sqrt(self.dTmx - self.dTmn) * (self.dTav + 17.8)
                # dret = 0.0023*dExtRad*math.sqrt(self.dTmx-self.dTmn)*((self.dTmx+self.dTmn)/2.+17.8)
        return dret

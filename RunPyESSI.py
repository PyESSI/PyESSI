# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:
    class: SoilInfo
    GetSoilTypeName(SoilTypeID)


"""

# load needed python modules
import utils.config
import utils.defines
from modules.Hydro.HydroSimulate import *

m_HydroSim = CHydroSimulate()


# 水文模拟循环开始
def runpyESSI():
    if utils.config.RunoffSimuType == utils.defines.STORM_RUNOFF_SIMULATION:
        if utils.config.InfilCurveType == utils.defines.INFILTRATION_HORTON:
            m_HydroSim.StormRunoffSim_Horton()
        elif utils.config.InfilCurveType == utils.defines.INFILTRATION_GREEN_AMPT:
            m_HydroSim.StormRunoffSim_GreenAmpt()
        else:
            m_HydroSim.StormRunoffSim_Horton()
    else:
        m_HydroSim.LongTermRunoffSimulate()


runpyESSI()

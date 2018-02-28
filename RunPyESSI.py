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
from modules.HydroSimulate import *

m_HydroSim = CHydroSimulate()
#水文模拟循环开始
def runpyESSI():
    if utils.config.RunoffSimuType == 1:
        if utils.config.InfilCurveType == 1:
            m_HydroSim.StormRunoffSim_Horton()
        elif utils.config.InfilCurveType == 2:
            m_HydroSim.StormRunoffSim_GreenAmpt()
        else:
            m_HydroSim.StormRunoffSim_Horton()
    else:
        m_HydroSim.LongTermRunoffSimulate()

runpyESSI()









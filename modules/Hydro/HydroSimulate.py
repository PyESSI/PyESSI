# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:
    class: SoilInfo
    GetSoilTypeName(SoilTypeID)


"""

# load needed python modules
import os
import utils.config
import utils.defines
from modules.Hydro.Hydro import *


class CHydroSimulate:
    def __init__(self):
        self.m_iVegOrd = 0
        self.m_iSoilOrd = 0
        self.m_bReadGridData = False
        self.m_bReadClimate = False
        self.m_pOutletQ = None
        self.m_pOutletSurfQ = None
        self.m_pOutletLatQ = None
        self.m_pOutletBaseQ = None
        self.m_pOutletDeepBaseQ = None

        self.m_pNodeSurfQ = None
        self.m_pNodeLatQ = None
        self.m_pNodeBaseQ = None
        self.m_pNodeOutQ = None

        self.m_pRainInterval = None

        self.RoutePara = CMuskCungeRoutePara()
        self.pRouteQ = None
        self.wytype = None

        self.m_pX = None
        self.m_pK = None

        self.m_OutRow = 0
        self.m_OutCol = 0

        if utils.config.RunoffSimuType == utils.defines.LONGTERM_RUNOFF_SIMULATION:
            self.m_bDate = True
        else:
            self.m_bDate = False

        self.m_iNodeNum = 1


    def StormRunoffSim_Horton(self):
        print('StormRunoffSim_Horton')

    def StormRunoffSim_GreenAmpt(self):
        print('StormRunoffSim_GreenAmpt')

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +            长时段降雨～径流过程模拟函数定义 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def LongTermRunoffSimulate(self):
        if utils.config.SurfRouteMethod == utils.defines.ROUTE_MUSK_CONGE:
            if self.ReadInRoutingPara():
                print('LongTermRunoffSimulate')





class RouteFlux:
    def __init__(self):
        self.dInFlux = 0.
        self.dOutFlux = 0.
        self.bCal = False


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                读入全流域栅格汇流参数文件 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +               读入栅格汇流最优次序参数文件 +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def ReadInRoutingPara(self):
        bret = False
        self.m_OutRow = 0
        self.m_OutCol = 0
        strFileName = open(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.DEMFileName.split('.')[0] + '_gud.txt')
        gudLines = strFileName.readlines()
        self.RoutePara.m_iRouteGridNum = len(gudLines)

        for i in range(len(gudLines)):
            self.RoutePara.pInGrid[i] = []
        self.RoutePara.pGridNum = []
        self.RoutePara.pOutGrid = []
        self.RoutePara.pGridRouteOrd = []
        self.RoutePara.pGridSlope = []
        self.RoutePara.pGridRLength = []
        self.pRouteQ = []

        #RouteFlux
        self.pSurfQ.pRoute = RouteFlux([])
        self.pSurfQ.pPreRoute = RouteFlux([])
        self.pLatQ.pRoute = RouteFlux([])
        self.pLatQ.pPreRoute = RouteFlux([])
        self.pBaseQ.pRoute = RouteFlux([])
        self.pBaseQ.pPreRoute = RouteFlux([])

        self.RoutePara.pGridRiverOrd = []
        self.RoutePara.pRow = []
        self.RoutePara.pCol = []








        bret = True

        return bret













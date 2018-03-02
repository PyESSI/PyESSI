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
import sys
import numpy
import utils.config
import utils.defines
from utils.fileIO import *
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
            if not self.ReadInRoutingPara():
                raise Exception('Read In Routing Para!', self.ReadInRoutingPara)

        if not self.ReadInRoutingLayerData():
            raise Exception('Read In Routing Layer Data!', self.ReadInRoutingLayerData)

        if utils.config.RiverRouteMethod == utils.defines.ROUTE_MUSKINGUM_COMBINE_FIRST or utils.config.RiverRouteMethod == utils.defines.ROUTE_MUSKINGUM_ROUTE_FIRST:
            if not self.ReadMuskingCoeff():
                raise Exception("马斯京根法河道参数读取失败，无法模拟", self.ReadMuskingCoeff)
            if self.m_iNodeNum > 1:
                self.MuskRouteInit(self.m_iNodeNum)

        DEMForld = utils.config.workSpace + os.sep + "DEM"
        DEMFile = DEMForld + os.sep + utils.config.DEMFileName
        self.g_DemLayer = readRaster(DEMFile)

        self.m_row = self.g_DemLayer.nRows
        self.m_col = self.g_DemLayer.nCols

             






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
        gutFile = utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.DEMFileName.split('.')[0] + '_gud.txt'
        if os.path.exists(gutFile):
            # 判断是否已读入栅格汇流最优次序参数文件
            if self.RoutePara.pGridNum is not None:
                return True
            strFileName = open(gutFile)
            gudLines = strFileName.readlines()
            num = len(gudLines)
            self.RoutePara = CMuskCungeRoutePara()
            self.RoutePara.m_iRouteGridNum = num
            for i in range(num):
                self.RoutePara.pInGrid[i] = numpy.zeros(8)
            self.RoutePara.pGridNum = numpy.zeros(num)
            self.RoutePara.pOutGrid = numpy.zeros(num)
            self.RoutePara.pGridRouteOrd = numpy.zeros(num)
            self.RoutePara.pGridSlope = numpy.zeros(num)
            self.RoutePara.pGridRLength = numpy.zeros(num)
            self.pRouteQ = numpy.zeros(num)

            #RouteFlux
            self.pSurfQ = CMuskRouteFlux()
            self.pLatQ = CMuskRouteFlux()
            self.pBaseQ = CMuskRouteFlux()
            for i in range(num):
                rtfx = RouteFlux()
                self.pSurfQ.pRoute.append(rtfx)
                self.pSurfQ.pPreRoute.append(rtfx)
                self.pLatQ.pRoute.append(rtfx)
                self.pLatQ.pPreRoute.append(rtfx)
                self.pBaseQ.pRoute.append(rtfx)
                self.pBaseQ.pPreRoute.append(rtfx)

            self.RoutePara.pGridRiverOrd = []
            self.RoutePara.pRow = []
            self.RoutePara.pCol = []


            for i in range(num):
                if i % int(num / 100) == 0:
                    print("▋", end='')
                    sys.stdout.flush()

                strLine = gudLines[i].rstrip(utils.defines.CHAR_SPLIT_ENTER)
                n = 0
                saLine = strLine.split(utils.defines.CHAR_SPLIT_TAB)
                self.RoutePara.pGridNum[i] = int(saLine[n])
                self.RoutePara.pGridRouteOrd[i] = int(saLine[n + 1])
                self.RoutePara.pInGrid[i][0] = int(saLine[n + 2])
                self.RoutePara.pInGrid[i][1] = int(saLine[n + 3])
                self.RoutePara.pInGrid[i][2] = int(saLine[n + 4])
                self.RoutePara.pInGrid[i][3] = int(saLine[n + 5])
                self.RoutePara.pInGrid[i][4] = int(saLine[n + 6])
                self.RoutePara.pInGrid[i][5] = int(saLine[n + 7])
                self.RoutePara.pInGrid[i][6] = int(saLine[n + 8])
                self.RoutePara.pInGrid[i][7] = int(saLine[n + 9])

                self.RoutePara.pOutGrid[i] = int(saLine[n + 10])
                self.RoutePara.pGridSlope[i] = float(saLine[n + 11])
                self.RoutePara.pGridRLength[i] = float(saLine[n + 12])
                self.RoutePara.pGridRiverOrd[i] = int(saLine[n + 13])
                self.RoutePara.pRow[i] = int(saLine[n + 14])
                self.RoutePara.pCol[i] = int(saLine[n + 15])
                self.pSurfQ.pRoute[i].dInFlux = 0.
                self.pSurfQ.pRoute[i].dOutFlux = 0.
                self.pSurfQ.pRoute[i].bCal = False
                self.pSurfQ.pPreRoute[i].dInFlux = 0.
                self.pSurfQ.pPreRoute[i].dOutFlux = 0.
                self.pSurfQ.pPreRoute[i].bCal = True

                self.pLatQ.pRoute[i].dInFlux = 0.
                self.pLatQ.pRoute[i].dOutFlux = 0.
                self.pLatQ.pRoute[i].bCal = False
                self.pLatQ.pPreRoute[i].dInFlux = 0.
                self.pLatQ.pPreRoute[i].dOutFlux = 0.
                self.pLatQ.pPreRoute[i].bCal = True

                self.pBaseQ.pRoute[i].dInFlux = 0.
                self.pBaseQ.pRoute[i].dOutFlux = 0.
                self.pBaseQ.pRoute[i].bCal = False
                self.pBaseQ.pPreRoute[i].dInFlux = 0.
                self.pBaseQ.pPreRoute[i].dOutFlux = 0.
                self.pBaseQ.pPreRoute[i].bCal = True

            bret = True
            self.m_OutRow = self.RoutePara.pRow[num - 1]
            self.m_OutCol = self.RoutePara.pCol[num - 1]
        else:
            raise Exception("Can not find gut txt file", gutFile)

        return bret

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                加载滞时演算汇流图层参数                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def ReadInRoutingLayerData(self):
        DEMForld = utils.config.workSpace + os.sep + "DEM"
        watershedFile = DEMForld + os.sep + utils.config.watershed
        subbasinFile = DEMForld + os.sep + utils.config.subbasin
        streamOrderFile = DEMForld + os.sep + utils.config.streamOrder
        routingTime_GSTFile = DEMForld + os.sep + utils.config.routingTime_GST
        routingTime_GLTFile = DEMForld + os.sep + utils.config.routingTime_GLT
        routingTime_GBTFile = DEMForld + os.sep + utils.config.routingTime_GBT

        if not os.path.exists(watershedFile):
            raise Exception("Can not find watershed file!", watershedFile)
        else:
            self.g_BasinBoundary = readRaster(watershedFile)

        if not os.path.exists(subbasinFile):
            raise Exception("Can not find subbasin file!", subbasinFile)
        else:
            self.g_SubWaterShed = readRaster(subbasinFile)
            self.m_subNum = numpy.max(self.g_SubWaterShed.data)

        if not os.path.exists(streamOrderFile):
            raise Exception("Can not find streamOrder file!", streamOrderFile)
        else:
            self.g_StrahlerRivNet = readRaster(streamOrderFile)
            self.m_MaxStrahlerOrd = numpy.max(self.g_StrahlerRivNet.data)

        if not os.path.exists(routingTime_GSTFile):
            raise Exception("Can not find routingTime_GST file!", routingTime_GSTFile)
        else:
            self.g_RouteSurfQTime = readRaster(routingTime_GSTFile)

        if not os.path.exists(routingTime_GLTFile):
            raise Exception("Can not find routingTime_GLT file!", routingTime_GLTFile)
        else:
            self.g_RouteLatQTime = readRaster(routingTime_GLTFile)

        if not os.path.exists(routingTime_GBTFile):
            raise Exception("Can not find routingTime_GBT file!", routingTime_GBTFile)
        else:
            self.g_RouteBaseQTime = readRaster(routingTime_GBTFile)

        return True


    def ReadMuskingCoeff(self):
        '''
        读取先演后合的马斯京根河道汇流文件
        :return:
        '''
        self.m_MuskCoeffFile = utils.config.workSpace + os.sep + "DEM" + os.sep + utils.config.MuskCoeffFile
        if not os.path.exists(self.m_MuskCoeffFile):
            return False

        MuskCoeffLines = open(self.m_MuskCoeffFile, 'r').readlines()
        self.m_iNodeNum = int(MuskCoeffLines[0].rstrip(utils.defines.CHAR_SPLIT_ENTER))
        if self.m_iNodeNum > 1:
            self.m_pX = []
            self.m_pK = []

            num = len(MuskCoeffLines)
            id = 0
            for i in range(2, num):
                saOut = MuskCoeffLines[i].rstrip(utils.defines.CHAR_SPLIT_ENTER)
                saOut = saOut.split(utils.defines.CHAR_SPLIT_TAB)
                self.m_pX.append(float(saOut[1]))
                self.m_pK.append(float(saOut[2]))
                id += 1

        return True


    def MuskRouteInit(self, nodenum):
        self.pRiverRoute = CMuskRouteFlux()
        if self.pRiverRoute.pRoute:
            self.pRiverRoute.pRoute = []

        if self.pRiverRoute.pPreRoute:
            self.pRiverRoute.pPreRoute = []

        for i in range(nodenum):
            newRouteFlux = RouteFlux()
            self.pRiverRoute.pRoute.append(newRouteFlux)
            self.pRiverRoute.pPreRoute.append(newRouteFlux)

        for i in range(nodenum):
            self.pRiverRoute.pRoute[i].dInFlux = 0.
            self.pRiverRoute.pRoute[i].dOutFlux = 0.
            self.pRiverRoute.pPreRoute[i].dInFlux = 0.
            self.pRiverRoute.pPreRoute[i].dOutFlux = 0.






















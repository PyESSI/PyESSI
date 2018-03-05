# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen
         Huiran Gao

Class:
    CHydroSimulate
        functions:



"""

# load needed python modules
import os
import sys
import numpy
import utils.config
import utils.defines
from utils.fileIO import *
from modules.Hydro.Hydro import *
from utils.dateTime import *
from modules.Hydro.SoilPara import *
from modules.Hydro.VegetationPara import *
from modules.hydro.HortonInfil import *
from modules.hydro.GridWaterBalance import *
from modules.hydro.VegetationPara import *


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

        self.m_row = 0
        self.m_col = 0

        self.HortonInfil = CHortonInfil()
        self.gridwb = CGridWaterBalance()

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
        print('LongTermRunoffSimulate')
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

        # 加载土壤、植被和DEM图层
        self.gridLayerInit()

        self.m_SnowWater = numpy.zeros([self.m_row, self.m_col])

        startDay = utils.config.startTime
        endDay = utils.config.endTime

        iniDate = datetime.date(int(startDay[0:4]), int(startDay[4:6]), int(startDay[6:8]))
        endDate = datetime.date(int(endDay[0:4]), int(endDay[4:6]), int(endDay[6:8]))
        dayCount = endDate.toordinal() - iniDate.toordinal() + 1
        daily = dailyRange('20080101', '20161231')

        totrec = dayCount
        self.m_pOutletQ = numpy.zeros(totrec)
        self.m_pOutletSurfQ = numpy.zeros(totrec)
        self.m_pOutletLatQ = numpy.zeros(totrec)
        self.m_pOutletBaseQ = numpy.zeros(totrec)
        self.m_pOutletDeepBaseQ = numpy.zeros(totrec)

        dthet = None
        dCp = None
        dsnowfactor = None
        aetfactor = 0.
        curorder = 0
        totYear = 0
        dn = None
        dCp = 0.5

        totYear = int(endDay[0:4]) - int(startDay[0:4]) + 1
        if not self.ReadWaterYearType():
            if not self.wytype:
                self.wytype = []
            for i in range(totYear):
                wytypeTemp = WaterYearType()
                wytypeTemp.year = int(startDay[0:4]) + i
                wytypeTemp.wtype = utils.defines.WATER_LOW_YEAR

                self.wytype.append(wytypeTemp)

        ##水文过程循环
        for theDay in daily:
            print('Calculating ' + theDay)
            iMonth = int(theDay[4:6])

            iniDateTemp = datetime.date(int(theDay[0:4]), 1, 1)
            endDateTemp = datetime.date(int(theDay[0:4]), int(theDay[4:6]), int(theDay[6:8]))

            dayCountTemp = iniDateTemp.toordinal() - endDateTemp.toordinal() + 1

            i = int(theDay[0:4])
            j = dayCountTemp

            dn = j

            dintensity = 0.
            dhr = 24.
            dhrIntensity = 0.
            dPE = 0.

            for row in range(self.m_row):
                for col in range(self.m_col):
                    if not self.IfGridBeCalculated(row, col):
                        continue

                    dsnowfactor = 1.
                    curPcp = readRaster(
                        utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'pcpdata' + os.sep + theDay + '.tif')
                    curTmpmean = readRaster(
                        utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmeandata' + os.sep + theDay + '.tif')
                    curPet = readRaster(
                        utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'petdata' + os.sep + theDay + '.tif')

                    if utils.config.tmpmeandata == 1:
                        if curTmpmean.data[row][col] < utils.config.SnowTemperature:
                            self.m_SnowWater[row][col] += curPcp.data[row][col]
                            curPcp.data[row][col] = 0.
                            dsnowfactor = 0.15
                        else:
                            if self.m_SnowWater[row][col] > 0:
                                smelt = self.DDFSnowMelt(curTmpmean.data[row][col], utils.config.SnowTemperature,
                                                         utils.config.DDF, utils.config.DailyMeanPcpTime)
                                if self.m_SnowWater[row][col] < smelt:
                                    smelt = self.m_SnowWater[row][col]
                                    self.m_SnowWater[row][col] = 0.
                                else:
                                    self.m_SnowWater[row][col] -= smelt
                                curPcp.data[row][col] += smelt
                                dsnowfactor = 0.3

                    dhrIntensity = utils.config.DailyMeanPcpTime
                    dintensity = curPcp.data[row][col] / dhrIntensity
                    self.HortonInfil.SetGridPara(row, col, self.pGridSoilInfo_SP_Sw[row][col].SP_Sw, 0.03)

                    self.HortonInfil.HortonExcessRunoff()
                    self.m_drateinf[row][col] = self.HortonInfil.m_dFt

                    dthet = self.g_SoilLayer.data[row][col].SoilWaterDeficitContent()

                    self.gridwb.SetGridPara(row, col, dintensity, self.m_drateinf[row][col], i, j, dhrIntensity, theDay)

                    dalb = self.GetVegAlbedo(iMonth)

                    self.gridwb.CalcPET(dalb, theDay)

                    if not self.g_StrahlerRivNet.data[row][col] == 0:
                        self.m_GridSurfQ[row][col] = curPcp.data[row][col] - self.gridwb.m_dPET
                        if self.m_GridSurfQ[row][col] < 0:
                            self.m_GridSurfQ[row][col] = 0.
                        if self.m_GridSurfQ.pGridValue[row][col] > 1e+10:
                            self.m_GridLateralQ[row][col] = 0.
                        self.m_GridBaseQ[row][col] = 0.
                        self.m_GridTotalQ[row][col] = self.m_GridSurfQ[row][col]
                        self.m_AET[row][col] = self.gridwb.m_dPET
                        self.m_CI[row][col] = 0.
                        self.m_CIDefict[row][col] = 0.
                        self.m_NetPcp[row][col] = self.m_GridSurfQ[row][col]
                        self.m_GridWaterYieldType[row][col] = 0
                        self.m_SoilProfileWater[row][col] = 0.
                        self.m_SoilAvgWater[row][col] = 0.

                    else:
                        self.gridwb.CalcCI()
                        self.m_CI[row][col] = self.gridwb.m_dCrownInterc
                        if self.pGridSoilInfo_SP_Sw[row][col] / self.pGridSoilInfo_SP_Fc[row][col] > 0.8:
                            if curPcp.data[row][col] > 0:
                                aetfactor = 0.6
                            else:
                                aetfactor = 0.9
                        else:
                            if curPcp.data[row][col] > 0:
                                aetfactor = 0.4
                            else:
                                aetfactor = 0.6

                        # //*************对蒸散发处理的特殊代码段 -- 计算实际蒸散发**************//
                        if utils.config.PETMethod == utils.defines.PET_REAL:
                            self.gridwb.m_dAET = curPet.data[row][col] * aetfactor
                            self.m_AET[row][col] = self.gridwb.m_dAET















                            # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # +                                                        +
    # +                度－日因子模型计算日融雪量 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /

    def DDFSnowMelt(self, dtav, dtThresh, ddf, dtlen=24.0):
        dret = 0.
        dret = ddf * (dtav - dtThresh) * dtlen
        return dret

    # // 深层地下水基流计算
    def DeepBaseQSim(self, dn, dmin):
        dret = 0.
        if dmin <= 0:
            return dret
        else:
            dret = (dmin + 3 * dmin) / 2. + (3 * dmin - dmin) / 2 * sin(2 * math.pi * (dn - 82) / 365)
            return dret

    def GetVegAlbedo(self, mon, day=1):
        dret = 0.23
        if mon >= 1 or mon <= 12:
            vegTemp = VegInfo()
            vegTemp.ReadVegFile(GetVegTypeName(int(self.m_iVegOrd)) + '.veg')
            dret = vegTemp.Albedo[mon - 1]
        return dret

    def ReadWaterYearType(self):
        waterYearTypeFile = utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.WaterYearTypeFile
        if os.path.exists(waterYearTypeFile):
            self.wytype = []
            wytypeFile = open(waterYearTypeFile, 'r')
            wytypeFile.close()
            wytypeLines = wytypeFile.readlines()

            for i in range(len(wytypeLines)):
                wyTypeTemp = WaterYearType()
                wyTypeTemp.year = \
                    wytypeLines[i].rstrip(utils.defines.CHAR_SPLIT_ENTER).split(utils.defines.CHAR_SPLIT_TAB)[0]
                wyTypeTemp.wtype = \
                    wytypeLines[i].rstrip(utils.defines.CHAR_SPLIT_ENTER).split(utils.defines.CHAR_SPLIT_TAB)[1]

                self.wytype.append(wyTypeTemp)
            return True

        else:
            return False

    # 加载栅格参数
    def gridLayerInit(self):
        DEMFolder = utils.config.workSpace + os.sep + "DEM"
        DEMFile = DEMFolder + os.sep + utils.config.DEMFileName
        LULCFile = DEMFolder + os.sep + utils.config.LULCFileName
        SoilFile = DEMFolder + os.sep + utils.config.SoilFileName

        self.g_DemLayer = readRaster(DEMFile)
        self.g_VegLayer = readRaster(LULCFile)
        self.g_SoilLayer = readRaster(SoilFile)

        self.m_row = self.g_DemLayer.nRows
        self.m_col = self.g_DemLayer.nCols

        for i in range(self.m_row):
            for j in range(self.m_col):
                if not self.IfGridBeCalculated(i, j):
                    continue
                soilTemp = SoilInfo()
                self.m_iSoilOrd = self.g_SoilLayer.data[i][j]
                soilTemp.ReadSoilFile(GetSoilTypeName(int(self.m_iSoilOrd)) + '.sol')
                self.pGridSoilInfo_SP_Sw[i][j] = soilTemp.SP_Sw

                self.pGridSoilInfo_SP_Wp[i][j] = soilTemp.SP_Wp
                self.pGridSoilInfo_SP_WFCS[i][j] = soilTemp.SP_WFCS
                self.pGridSoilInfo_SP_Sat_K[i][j] = soilTemp.SP_Sat_K
                self.pGridSoilInfo_SP_Stable_Fc[i][j] = soilTemp.SP_Stable_Fc
                self.pGridSoilInfo_SP_Init_F0[i][j] = soilTemp.SP_Init_F0
                self.pGridSoilInfo_Horton_K[i][j] = soilTemp.Horton_K
                self.pGridSoilInfo_SP_Por[i][j] = soilTemp.SP_Por
                self.pGridSoilInfo_rootdepth[i][j] = soilTemp.rootdepth
                self.pGridSoilInfo_SP_Fc[i][j] = soilTemp.SP_Fc
                self.pGridSoilInfo_SP_Sat[i][j] = soilTemp.SP_Sat
                self.pGridSoilInfo_TPercolation[i][j] = (soilTemp.SP_Sat - soilTemp.SP_Fc) / (soilTemp.SP_Sat_K)
                self.pGridSoilInfo_SP_Temp[i][j] = 0.

                vegTemp = VegInfo()
                self.m_iVegOrd = self.g_VegLayer.data[i][j]
                vegTemp.ReadVegFile(GetVegTypeName(int(self.m_iVegOrd)) + '.veg')
                self.pGridVegInfo[i][j] = vegTemp

                # m_GridTotalQ
                # m_GridSurfQ
                # m_GridLateralQ
                # m_GridBaseQ
                # m_GridTempVal
                # m_GridWaterYieldType
                # m_SoilProfileWater
                # m_SoilAvgWater
                # m_SoilAvgWater
                # m_NetPcp

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                判断当前栅格是否需要计算 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +        TRUE - - 需要计算；FALSE - - 不需要计算 +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def IfGridBeCalculated(self, row, col):
        bret = True
        if not self.g_BasinBoundary.data[row][col] == 1:
            bret = False
        else:
            if self.g_VegLayer.data[row][col] == self.g_VegLayer.noDataValue or self.g_DemLayer.data[row][
                col] == self.g_DemLayer.noDataValue or self.g_SoilLayer.data[row][col] == self.g_SoilLayer.noDataValue:
                bret = False
        return bret

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

            # RouteFlux
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

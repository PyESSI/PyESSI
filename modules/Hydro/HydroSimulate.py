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
import numpy
import time
import util.config
import util.defines
from util.fileIO import *
from modules.Hydro.Hydro import *
from util.dateTime import *
from modules.Hydro.SoilPara import *
from modules.Hydro.VegetationPara import *
from modules.Hydro.HortonInfil import *
from modules.Hydro.GridWaterBalance import *
from modules.Hydro.VegetationPara import *
from modules.Hydro.Muskingum import *


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
        self.middaily = []

        self.HortonInfil = CHortonInfil()

        if util.config.RunoffSimuType == util.defines.LONGTERM_RUNOFF_SIMULATION:
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
        print('[LongTermRunoffSimulate]')
        CreateForld(util.config.workSpace + os.sep + "Output")
        if util.config.SurfRouteMethod == util.defines.ROUTE_MUSK_CONGE:
            if not self.ReadInRoutingPara():
                raise Exception('Read In Routing Para!', self.ReadInRoutingPara)

        if not self.ReadInRoutingLayerData():
            raise Exception('Read In Routing Layer Data!', self.ReadInRoutingLayerData)

        if util.config.RiverRouteMethod == util.defines.ROUTE_MUSKINGUM_COMBINE_FIRST or util.config.RiverRouteMethod == util.defines.ROUTE_MUSKINGUM_ROUTE_FIRST:
            if not self.ReadMuskingCoeff():
                raise Exception("马斯京根法河道参数读取失败，无法模拟", self.ReadMuskingCoeff)
            if self.m_iNodeNum > 1:
                self.MuskRouteInit(self.m_iNodeNum)

        # 加载土壤、植被和DEM图层
        SoilTypeTXT = util.config.workSpace + os.sep + 'LookupTable' + os.sep + 'SoilType.txt'
        LulcTypeTXT = util.config.workSpace + os.sep + 'LookupTable' + os.sep + 'LulcType.txt'
        if os.path.exists(SoilTypeTXT):
            soilIdName = []
            soilTypeInfos = open(SoilTypeTXT, 'r').readlines()
            for i in range(len(soilTypeInfos)):
                soilIdName.append((soilTypeInfos[i].split('\n')[0].split('\t')[0].strip(),
                                   soilTypeInfos[i].split('\n')[0].split('\t')[1].strip()))
            self.soilTypeName = dict(soilIdName)
        else:
            raise Exception("Can not find SoilType.txt")
        if os.path.exists(LulcTypeTXT):
            vegIdName = []
            vegTypeInfos = open(LulcTypeTXT, 'r').readlines()
            for i in range(len(vegTypeInfos)):
                vegIdName.append((vegTypeInfos[i].split('\n')[0].split('\t')[0].strip(),
                                  vegTypeInfos[i].split('\n')[0].split('\t')[1].strip()))
            self.vegTypeName = dict(vegIdName)
        else:
            raise Exception("Can not find LulcType.txt")

        self.gridLayerInit()
        self.GridMemFreeAndNew()
        self.GridLayerInit_LongTerm()
        self.GridMemFreeAndNew_LongTerm()

        self.m_SnowWater = numpy.zeros([self.m_row, self.m_col])

        # 设置日期
        startDay = util.config.startTime
        endDay = util.config.endTime

        iniDate = datetime.date(int(startDay[0:4]), int(startDay[4:6]), int(startDay[6:8]))
        endDate = datetime.date(int(endDay[0:4]), int(endDay[4:6]), int(endDay[6:8]))
        dayCount = endDate.toordinal() - iniDate.toordinal() + 1
        daily = dailyRange(startDay, endDay)

        midOutBdate = util.config.strOutBDate
        midOutEdate = util.config.strOutEDate
        self.middaily = dailyRange(midOutBdate, midOutEdate)

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
                self.wytype = None
            wyTypeTemps = []
            for i in range(totYear):
                wytypeTemp = WaterYearType()
                wytypeTemp.year = int(startDay[0:4]) + i
                wytypeTemp.wtype = int(util.defines.WATER_LOW_YEAR)
                wyTypeTemps.append((wytypeTemp.year, wytypeTemp.wtype))
            self.wytype = dict(wyTypeTemps)

        ##水文过程循环
        for theDay in daily:
            print('Calculating %s\t' % theDay, end='')
            s_long = time.clock()
            iMonth = int(theDay[4:6])

            iniDateTemp = datetime.date(int(theDay[0:4]), 1, 1)
            endDateTemp = datetime.date(int(theDay[0:4]), int(theDay[4:6]), int(theDay[6:8]))

            dayCountTemp = endDateTemp.toordinal() - iniDateTemp.toordinal() + 1

            i = int(theDay[0:4])
            j = dayCountTemp

            dn = j

            dintensity = 0.
            dhr = 24.
            dhrIntensity = 0.
            dPE = 0.

            if util.config.pcpdata == 1:
                self.curPcp = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'pcpdata' + os.sep + theDay + '.tif').data
            else:
                self.curPcp = numpy.zeros((self.m_row, self.m_col))

            if util.config.petdata == 1:
                self.curPet = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'petdata' + os.sep + theDay + '.tif').data
            else:
                self.curPet = numpy.zeros((self.m_row, self.m_col))

            if util.config.tmpmeandata == 1:
                self.curTmpmean = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmeandata' + os.sep + theDay + '.tif').data
            else:
                self.curTmpmean = numpy.zeros((self.m_row, self.m_col))

            if util.config.tmpmxdata == 1:
                self.curTmpmx = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmxdata' + os.sep + theDay + '.tif').data
            else:
                self.curTmpmx = numpy.zeros((self.m_row, self.m_col))

            if util.config.tmpmndata == 1:
                self.curTmpmn = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmndata' + os.sep + theDay + '.tif').data
            else:
                self.curTmpmn = numpy.zeros((self.m_row, self.m_col))

            if util.config.wnddata == 1:
                self.curWnd = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'wnddata' + os.sep + theDay + '.tif').data
            else:
                self.curWnd = numpy.zeros((self.m_row, self.m_col))

            if util.config.hmddata == 1:
                self.curHmd = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'hmddata' + os.sep + theDay + '.tif').data
            else:
                self.curHmd = numpy.zeros((self.m_row, self.m_col))
            if util.config.slrdata == 1:
                self.curSlr = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'slrdata' + os.sep + theDay + '.tif').data
            else:
                self.curSlr = numpy.zeros((self.m_row, self.m_col))

            for row in range(self.m_row):
                for col in range(self.m_col):
                    if (row * self.m_row + col + 1) % int(self.m_row * self.m_col / 10) == 0:
                        print("•", end='')
                        sys.stdout.flush()

                    if not self.IfGridBeCalculated(row, col):
                        continue

                    dsnowfactor = 1.

                    if util.config.tmpmeandata == 1:
                        if self.curTmpmean[row][col] < util.config.SnowTemperature:
                            self.m_SnowWater[row][col] += self.curPcp[row][col]
                            self.curPcp[row][col] = 0.

                            dsnowfactor = 0.15
                        else:
                            if self.m_SnowWater[row][col] > 0:
                                smelt = self.DDFSnowMelt(self.curTmpmean[row][col], util.config.SnowTemperature,
                                                         util.config.DDF, util.config.DailyMeanPcpTime)
                                if self.m_SnowWater[row][col] < smelt:
                                    smelt = self.m_SnowWater[row][col]
                                    self.m_SnowWater[row][col] = 0.
                                else:
                                    self.m_SnowWater[row][col] -= smelt
                                self.curPcp[row][col] += smelt
                                dsnowfactor = 0.3

                    dhrIntensity = util.config.DailyMeanPcpTime

                    dintensity = self.curPcp[row][col] / dhrIntensity

                    self.HortonInfil.SetGridPara(row, col, self.pGridSoilInfo_SP_Sw[row][col], 0.03,
                                                 self.g_SoilLayer.data[row][col], self.soilTypeName)

                    self.HortonInfil.HortonExcessRunoff()
                    self.m_drateinf[row][col] = self.HortonInfil.m_dFt

                    pGridSoilInfo = SoilInfo(self.soilTypeName)
                    pGridSoilInfo.ReadSoilFile(self.soilTypeName[str(int(self.g_SoilLayer.data[row][col]))] + '.sol')
                    dthet = pGridSoilInfo.SoilWaterDeficitContent()

                    self.gridwb = CGridWaterBalance(self.g_DemLayer.data[row][col], self.g_SoilLayer.data[row][col],
                                                    self.g_VegLayer.data[row][col],
                                                    self.curPet[row][col], self.curPcp[row][col], self.curTmpmean[row][col],
                                                    self.curTmpmx[row][col], self.curTmpmn[row][col], self.curSlr[row][col],
                                                    self.curHmd[row][col], self.curWnd[row][col], self.soilTypeName, self.vegTypeName)

                    self.gridwb.SetGridPara(dintensity, self.m_drateinf[row][col], i, j, dhrIntensity, theDay)

                    dalb = self.GetVegAlbedo(iMonth)

                    self.gridwb.CalcPET(dalb, theDay)

                    if not self.g_StrahlerRivNet.data[row][col] == 0:
                        self.m_GridSurfQ[row][col] = self.curPcp[row][col] - self.gridwb.m_dPET
                        if self.m_GridSurfQ[row][col] < 0:
                            self.m_GridSurfQ[row][col] = 0.
                        if self.m_GridSurfQ[row][col] > 1e+10:
                            print('hello')
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
                            if self.curPcp[row][col] > 0:
                                aetfactor = 0.6
                            else:
                                aetfactor = 0.9
                        else:
                            if self.curPcp[row][col] > 0:
                                aetfactor = 0.4
                            else:
                                aetfactor = 0.6

                        # //*************对蒸散发处理的特殊代码段 -- 计算实际蒸散发**************//
                        if util.config.PETMethod == util.defines.PET_REAL:

                            self.gridwb.m_dAET = self.curPet[row][col] * aetfactor
                            self.m_AET[row][col] = self.gridwb.m_dAET
                        else:
                            self.gridwb.CalcAET(dalb, theDay)
                            if self.gridwb.m_dAET > self.curPet[row][col]:
                                self.m_AET[row][col] = self.curPet[row][col] * math.exp(
                                    -1 * self.curPet[row][col] / self.gridwb.m_dAET)
                            if self.gridwb.m_dAET < 0:
                                self.m_AET[row][col] = self.curPet[row][col] * 0.1

                        # // ** ** ** ** ** ** ** ** ** ** ** 对蒸散发处理的特殊代码段 ** ** ** ** ** ** ** ** ** ** **
                        self.gridwb.CalcNetRain()
                        self.m_CIDefict[row][col] = self.gridwb.m_dCIDeficit
                        self.m_NetPcp[row][col] = self.gridwb.m_dNetRain
                        self.m_GridWaterYieldType[row][col] = self.gridwb.CalcRunoffElement()
                        self.m_SoilProfileWater[row][col] = self.pGridSoilInfo_SP_Sw[row][col]

                        self.m_SoilAvgWater[row][col] = pGridSoilInfo.SoilAvgWater()
                        self.m_GridTotalQ[row][col] = self.gridwb.m_dTotalQ
                        self.m_GridSurfQ[row][col] = self.gridwb.m_dSurfQ
                        self.m_GridLateralQ[row][col] = self.gridwb.m_dLateralQ
                        self.m_GridBaseQ[row][col] = self.gridwb.m_dBaseQ

                        if self.m_GridSurfQ[row][col] > 1e+10:
                            print("hello2")


            if self.m_iNodeNum == 1 or util.config.RiverRouteMethod == util.defines.ROUTE_PURE_LAG:
                self.m_pOutletSurfQ = self.PureLagGridRouting(self.m_GridSurfQ, self.m_pOutletSurfQ, dhr, util.defines.RUNOFF_ELEMENT_SURFQ,
                                        curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])
                self.m_pOutletLatQ = self.PureLagGridRouting(self.m_GridLateralQ, self.m_pOutletLatQ, dhr, util.defines.RUNOFF_ELEMENT_LATERALQ,
                                        curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])
                self.m_pOutletBaseQ = self.PureLagGridRouting(self.m_GridBaseQ, self.m_pOutletBaseQ, dhr, util.defines.RUNOFF_ELEMENT_BASEQ,
                                        curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])
                self.m_pOutletDeepBaseQ[curorder] = self.DeepBaseQSim(dn, util.config.DeepBaseQ)
                self.m_pOutletQ[curorder] = self.m_pOutletSurfQ[curorder] * util.config.SurfQLinearFactor + \
                                            self.m_pOutletLatQ[curorder] + self.m_pOutletBaseQ[curorder] + \
                                            self.m_pOutletDeepBaseQ[curorder]
            else:
                self.m_pNodeSurfQ = self.PureLagGridRouting_Node(self.m_GridSurfQ, self.m_pNodeSurfQ, dhr,
                                             util.defines.RUNOFF_ELEMENT_SURFQ,
                                             curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])
                self.m_pNodeLatQ = self.PureLagGridRouting_Node(self.m_GridLateralQ, self.m_pNodeLatQ, dhr,
                                             util.defines.RUNOFF_ELEMENT_LATERALQ,
                                             curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])
                self.m_pNodeBaseQ = self.PureLagGridRouting_Node(self.m_GridBaseQ, self.m_pNodeBaseQ, dhr,
                                             util.defines.RUNOFF_ELEMENT_BASEQ,
                                             curorder, totrec, dsnowfactor, self.wytype[int(theDay[0:4])])

                dSurf = 0.
                dLat = 0.
                dBase = 0.

                for i in range(self.m_subNum):
                    dSurf += self.m_pNodeSurfQ[curorder][i] * util.config.SurfQLinearFactor
                    dLat += self.m_pNodeLatQ[curorder][i]
                    dBase += self.m_pNodeBaseQ[curorder][i]
                self.m_pOutletSurfQ[curorder] = dSurf
                self.m_pOutletLatQ[curorder] = dLat
                self.m_pOutletBaseQ[curorder] = dBase
                self.m_pOutletDeepBaseQ[curorder] = self.DeepBaseQSim(dn, util.config.DeepBaseQ)

                if util.config.RiverRouteMethod == util.defines.ROUTE_MUSKINGUM_COMBINE_FIRST:
                    for i in range(self.m_subNum):
                        self.m_pNodeOutQ[curorder][i] = self.m_pNodeSurfQ[curorder][i] * util.config.SurfQLinearFactor + \
                                                        self.m_pNodeLatQ[curorder][i] + self.m_pNodeBaseQ[curorder][i]
                        self.pRiverRoute.pRoute, self.pRiverRoute.pPreRoute = self.MuskingumRiverRouting(24, self.m_pNodeOutQ, self.pRiverRoute.pRoute,
                                               self.pRiverRoute.pPreRoute, self.m_pX, self.m_pK, self.m_subNum,
                                               curorder)
                    self.m_pOutletQ[curorder] = self.pRiverRoute.pRoute[self.m_subNum - 1].dOutFlux + \
                                                self.m_pOutletDeepBaseQ[curorder]
                elif util.config.RiverRouteMethod == ROUTE_MUSKINGUM_ROUTE_FIRST:
                    print('TODO')
                else:
                    self.m_pOutletQ[curorder] = self.m_pOutletSurfQ[curorder] + self.m_pOutletLatQ[curorder] + \
                                                self.m_pOutletBaseQ[curorder] + self.m_pOutletDeepBaseQ[curorder]

            curorder += 1
            self.MidGridResultOut(theDay, self.curPcp, self.curPet, self.curWnd, self.curHmd, self.curSlr, self.curTmpmean, self.curTmpmn, self.curTmpmx)

            self.RiverOutletQ_Hao(theDay, curorder - 1)

            e_long = time.clock()
            print("\ttime: %.3f" % (e_long - s_long))

        if util.config.RiverRouteMethod == util.defines.ROUTE_MUSKINGUM_COMBINE_FIRST or util.config.RiverRouteMethod == util.defines.ROUTE_MUSKINGUM_ROUTE_FIRST:
            if self.m_pX:
                self.m_pX = None
            if self.m_pK:
                self.m_pK = None
        if self.wytype:
            self.wytype = None


    def MidGridResultOut(self, curDay, curPcp, curPet, curWnd, curHmd, curSlr, curTmpmean, curTmpmn, curTmpmx):
        if curDay in self.middaily:
            if util.config.iPcp == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Pcp'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curPcp, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iPET == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'PET'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curPet, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iWnd == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Wnd'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curWnd, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iHmd == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Hmd'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curHmd, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSlr == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Slr'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curSlr, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMean == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMean'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmean, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMin == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMin'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmn, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMax == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMax'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmx, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)



            if util.config.iAET == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'AET'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_AET, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iCI == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'CI'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_CI, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSnowWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Snow'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_SnowWater, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iAI == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'AI'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_AI, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iRouteOut == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'GridRoute'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_GridRoutingQ, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSurfQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'SurfQ'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_GridSurfQ, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iLatQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'WYType'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_GridLateralQ, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iBaseQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'LatQ'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_GridBaseQ, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iWaterYieldType == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'BaseQ'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_GridWaterYieldType, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iInfilRate == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'InfilRate'+ curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_drateinf, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iProfileSoilWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'SoilProfileWater' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_SoilProfileWater, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iAvgSoilWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'oilAvgWater' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_SoilAvgWater, self.g_DemLayer.geoTransform, self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)



    def RiverOutletQ_Hao(self, curDay, curOrder):
        outQ = open(util.config.workSpace + os.sep + 'Output' + os.sep + 'outQ.txt','a')
        outQ.write("%s\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\n" % (curDay, self.m_pOutletQ[curOrder], self.m_pOutletSurfQ[curOrder], self.m_pOutletLatQ[curOrder], self.m_pOutletBaseQ[curOrder], self.m_pOutletDeepBaseQ[curOrder]))

        outQ.close()


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                    河道Muskingum汇流 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                        先合后演 +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def MuskingumRiverRouting(self, dTLen, pNodeQ, pRoute, pPreRoute, pX, pK, NodeNum, curOrder):
        for i in range(NodeNum):
            QOut = 0.
            if i == 0:
                QOut = pNodeQ[curOrder][i]
            else:
                QOut = pNodeQ[curOrder][i] + (pRoute)[i - 1].dOutFlux
            pRoute[i].dInFlux = QOut
            pRoute[i].dOutFlux = self.RiverRoutingOut(dTLen, pPreRoute[i].dInFlux, pRoute[i].dInFlux,
                                                      pPreRoute[i].dOutFlux, pX[i], pK[i])
            pRoute[i].bCal = True
        for i in range(NodeNum):
            pPreRoute[i].dInFlux = pRoute[i].dInFlux
            pPreRoute[i].dOutFlux = pRoute[i].dOutFlux
            pRoute[i].bCal = False
        return pRoute, pPreRoute

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                    河道Muskingum汇流2 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +          单栅格运动波汇流处理, 计算栅格出流 +
    # +            河道和坡面的运动波汇流分别计算 +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /

    def RiverRoutingOut(self, deltaT, dInFlux1, dInFlux2, dOutFlux1, x, k):
        dOutFlux2 = 0.
        self.Muskingum = CMuskingum()
        self.Muskingum.SetRoutingPara(deltaT, dInFlux1, dInFlux2, dOutFlux1, x, k)
        dOutFlux2 = self.Muskingum.RoutingOutQ()

        return dOutFlux2

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                滞时演算法计算汇流(子流域) +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PureLagGridRouting_Node(self, GridQ, pRoute, dTlen, QType, curorder, totorder, snowfactor, WaterYrType):
        LagOrder = 0
        LagTime = 0
        dGridOut = 0.
        subID = 0
        dSurfQLoss = 0.
        if WaterYrType == util.defines.WATER_HIGH_YEAR:
            dSurfQLoss = util.config.HighWaterSurfQLoss
        elif WaterYrType == util.defines.WATER_MID_YEAR:
            dSurfQLoss = util.config.MidWaterSurfQLoss
        elif WaterYrType == util.defines.WATER_LOW_YEAR:
            dSurfQLoss = util.config.LowWaterSurfQLoss
        else:
            dSurfQLoss = util.config.LowWaterSurfQLoss

        for i in range(self.m_row):
            for j in range(self.m_col):
                if self.g_BasinBoundary.data[i][j] == 1.:
                    subID = int(self.g_SubWaterShed.data[i][j] - 1)
                    if QType == util.defines.RUNOFF_ELEMENT_SURFQ:
                        LagTime = int(self.g_RouteSurfQTime[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < int(totorder):
                            if self.g_RouteSurfQTime.data[i][j] <= 0:
                                self.g_RouteSurfQTime.data[i][j] = 0.1
                                dGridOut = snowfactor * GridQ[i][j] / (
                                dSurfQLoss * math.pow(self.g_RouteSurfQTime.data[i][j], 1))
                                pRoute[LagOrder][subID] += dGridOut
                    elif QType == util.defines.RUNOFF_ELEMENT_LATERALQ:
                        LagTime = int(self.g_RouteLatQTime[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < int(totorder):
                            if self.g_RouteLatQTime.data[i][j] <= 0:
                                self.g_RouteLatQTime.data[i][j] = 0.1
                                dGridOut = snowfactor * GridQ[i][j] / (
                                util.config.LatQLoss * math.pow(self.g_RouteLatQTime.data[i][j], 1))
                                pRoute[LagOrder][subID] += dGridOut
                    elif QType == util.defines.RUNOFF_ELEMENT_BASEQ:
                        LagTime = int(self.g_RouteBaseQTime[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < int(totorder):
                            if self.g_RouteBaseQTime.data[i][j] <= 0:
                                self.g_RouteBaseQTime.data[i][j] = 0.1
                                dGridOut = snowfactor * GridQ[i][j] / (
                                util.config.LatQLoss * math.pow(self.g_RouteBaseQTime.data[i][j], 1))
                                pRoute[LagOrder][subID] += dGridOut
                    else:
                        return False
        return pRoute

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                滞时演算法计算汇流(全流域) +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def PureLagGridRouting(self, GridQ, pRoute, dTlen, QType, curorder, totorder, snowfactor, WaterYrType):
        LagOrder = 0
        LagTime = 0
        dGridOut = 0.
        dSurfQLoss = 0.
        if WaterYrType == util.defines.WATER_HIGH_YEAR:
            dSurfQLoss = util.config.HighWaterSurfQLoss
        elif WaterYrType == util.defines.WATER_MID_YEAR:
            dSurfQLoss = util.config.MidWaterSurfQLoss
        elif WaterYrType == util.defines.WATER_LOW_YEAR:
            dSurfQLoss = util.config.LowWaterSurfQLoss
        else:
            dSurfQLoss = util.config.LowWaterSurfQLoss

        for i in range(self.m_row):
            for j in range(self.m_col):
                if self.IfGridBeCalculated(i, j):
                    if QType == util.defines.RUNOFF_ELEMENT_SURFQ:
                        LagTime = int(self.g_RouteSurfQTime.data[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < int(totorder):
                            dGridOut = snowfactor * GridQ[i][j] / (
                                dSurfQLoss * math.pow(self.g_RouteSurfQTime.data[i][j], 1))
                            pRoute[int(LagOrder)] += dGridOut
                    elif QType == util.defines.RUNOFF_ELEMENT_LATERALQ:
                        LagTime =  int(self.g_RouteLatQTime.data[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < totorder:
                            dGridOut = snowfactor * GridQ[i][j] / (
                                util.config.LatQLoss * math.pow(self.g_RouteLatQTime.data[i][j], 1))
                            pRoute[LagOrder] += dGridOut
                    elif QType == util.defines.RUNOFF_ELEMENT_BASEQ:
                        LagTime =  int(self.g_RouteBaseQTime.data[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < totorder:
                            dGridOut = snowfactor * GridQ[i][j] / (
                                util.config.BaseQLoss * math.pow(self.g_RouteBaseQTime.data[i][j], 1))
                            pRoute[LagOrder] += dGridOut

                    else:
                        return False

        return pRoute


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                度－日因子模型计算日融雪量 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /

    def DDFSnowMelt(self, dtav, dtThresh, ddf, dtlen=24.0):
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
            vegTemp = VegInfo(self.vegTypeName)
            vegTemp.ReadVegFile(self.vegTypeName[str(int(self.m_iVegOrd))] + '.veg')
            dret = vegTemp.Albedo[mon - 1]
        return dret

    def ReadWaterYearType(self):
        waterYearTypeFile = util.config.workSpace + os.sep + 'DEM' + os.sep + util.config.WaterYearTypeFile
        if os.path.exists(waterYearTypeFile):
            self.wytype = None
            wytypeFile = open(waterYearTypeFile, 'r')
            wytypeLines = wytypeFile.readlines()
            wytypeFile.close()

            wyTypeTemps = []
            for i in range(len(wytypeLines)):
                wyTypeTemp = WaterYearType()

                wyTypeTemp.year = int(wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[0])
                wyTypeTemp.wtype = int(wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[1])
                wyTypeTemps.append((wyTypeTemp.year, wyTypeTemp.wtype))
            self.wytype = dict(wyTypeTemps)

            return True

        else:
            return False

    def gridLayerInit(self):
        '''
        加载栅格参数
        :return:
        '''
        print("Loading grid parameters...")
        s = time.clock()

        DEMFolder = util.config.workSpace + os.sep + "DEM"
        DEMFile = DEMFolder + os.sep + util.config.DEMFileName
        LULCFile = DEMFolder + os.sep + util.config.LULCFileName
        SoilFile = DEMFolder + os.sep + util.config.SoilFileName

        self.g_DemLayer = readRaster(DEMFile)
        self.g_VegLayer = readRaster(LULCFile)
        self.g_SoilLayer = readRaster(SoilFile)

        self.m_row = self.g_DemLayer.nRows
        self.m_col = self.g_DemLayer.nCols

        self.pGridSoilInfo_SP_Sw = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Wp = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_WFCS = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Sat_K = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Stable_Fc = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Init_F0 = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_Horton_K = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Por = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_rootdepth = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Fc = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Sat = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_TPercolation = numpy.empty((self.m_row, self.m_col))
        self.pGridSoilInfo_SP_Temp = numpy.zeros((self.m_row, self.m_col))

        pGridVegInfoTemp = []
        vegTemp = None
        for i in range(self.m_row):
            for j in range(self.m_col):
                pGridVegInfoTemp.append(vegTemp)

        self.pGridVegInfo = numpy.array(pGridVegInfoTemp).reshape(self.m_row, self.m_col)

        self.m_GridTotalQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridSurfQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridLateralQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridBaseQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridTempVal = numpy.empty((self.m_row, self.m_col))
        self.m_GridWaterYieldType = numpy.empty((self.m_row, self.m_col))
        self.m_SoilProfileWater = numpy.empty((self.m_row, self.m_col))
        self.m_SoilAvgWater = numpy.empty((self.m_row, self.m_col))
        self.m_GridRoutingQ = numpy.empty((self.m_row, self.m_col))
        self.m_NetPcp = numpy.empty((self.m_row, self.m_col))

        for i in range(self.m_row):
            for j in range(self.m_col):
                if (i * self.m_row + j + 1) % int(self.m_row * self.m_col / 10) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                if not self.IfGridBeCalculated(i, j):
                    continue
                if self.GetSoilTypeOrder(int(self.g_SoilLayer.data[i][j])):
                    soilTemp = SoilInfo(self.soilTypeName)
                    self.m_iSoilOrd = int(self.g_SoilLayer.data[i][j])
                    soilTemp.ReadSoilFile(self.soilTypeName[str(int(self.m_iSoilOrd))] + '.sol')
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

                    vegTemp = VegInfo(self.vegTypeName)
                    self.m_iVegOrd = self.g_VegLayer.data[i][j]
                    vegTemp.ReadVegFile(self.vegTypeName[str(int(self.m_iVegOrd))] + '.veg')
                    self.pGridVegInfo[i][j] = vegTemp

        e = time.clock()
        print('\nFinished Load grid parameters：%.3f' % (e - s))


    def GridLayerInit_Horton(self):
        self.m_AET = numpy.empty((self.m_row, self.m_col))
        self.m_drateinf = numpy.empty((self.m_row, self.m_col))

    def GridLayerInit_GreenAmpt(self):
        self.GridLayerInit_Horton()
        self.m_drintns = numpy.empty((self.m_row, self.m_col))
        self.m_dcumr = numpy.empty((self.m_row, self.m_col))
        self.m_dcuminf = numpy.empty((self.m_row, self.m_col))
        self.m_dexcum = numpy.empty((self.m_row, self.m_col))

    def GridLayerInit_LongTerm(self):
        self.m_drateinf = numpy.empty((self.m_row, self.m_col))
        self.m_AET = numpy.empty((self.m_row, self.m_col))
        self.m_CI = numpy.empty((self.m_row, self.m_col))
        self.m_SnowWater = numpy.empty((self.m_row, self.m_col))
        self.m_CIDefict = numpy.empty((self.m_row, self.m_col))
        self.m_AI = numpy.empty((self.m_row, self.m_col))
        self.m_NetPcp = numpy.empty((self.m_row, self.m_col))

    def GridMemFreeAndNew(self):
        self.m_GridTotalQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridSurfQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridLateralQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridBaseQ = numpy.empty((self.m_row, self.m_col))
        self.m_GridRoutingQ = numpy.empty((self.m_row, self.m_col))

        self.m_NetPcp = numpy.empty((self.m_row, self.m_col))
        self.m_GridWaterYieldType = numpy.empty((self.m_row, self.m_col))
        self.m_SoilProfileWater = numpy.empty((self.m_row, self.m_col))
        self.m_SoilAvgWater = numpy.empty((self.m_row, self.m_col))

    def GridMemFreeAndNew_Horton(self):
        self.m_AET = numpy.empty((self.m_row, self.m_col))
        self.m_drateinf = numpy.zeros((self.m_row, self.m_col))

    def GridMemFreeAndNew_LongTerm(self):
        self.m_drateinf = numpy.zeros((self.m_row, self.m_col))
        self.m_drintns = numpy.zeros((self.m_row, self.m_col))
        self.m_dcumr = numpy.zeros((self.m_row, self.m_col))
        self.m_dcuminf = numpy.zeros((self.m_row, self.m_col))
        self.m_dexcum = numpy.zeros((self.m_row, self.m_col))
        self.m_AI = numpy.zeros((self.m_row, self.m_col))
        self.m_CI = numpy.zeros((self.m_row, self.m_col))
        self.m_SnowWater = numpy.zeros((self.m_row, self.m_col))
        self.m_CIDefict = numpy.empty((self.m_row, self.m_col))
        self.m_AET = numpy.empty((self.m_row, self.m_col))
        self.m_NetPcp = numpy.empty((self.m_row, self.m_col))

    def GridMemFreeAndNew_GreenAmpt(self):
        self.m_AI = numpy.empty((self.m_row, self.m_col))
        self.m_CI = numpy.empty((self.m_row, self.m_col))
        self.m_CIDefict = numpy.empty((self.m_row, self.m_col))
        self.m_AET = numpy.empty((self.m_row, self.m_col))

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
    # +  取得当前栅格指定的土壤类型在土壤数据结构指针中的位置 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def GetSoilTypeOrder(self, sid):
        bret = False
        soilname = self.soilTypeName[str(sid)]
        self.m_iSoilOrd = sid
        if soilname:
            bret = True

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
        gutFile = util.config.workSpace + os.sep + 'DEM' + os.sep + util.config.DEMFileName.split('.')[0] + '_gud.txt'
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
                if i % int((num + 1) / 10) == 0:
                    print("▋", end='')
                    sys.stdout.flush()

                strLine = gudLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER)
                n = 0
                saLine = strLine.split(util.defines.CHAR_SPLIT_TAB)
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
            strFileName.close()
        else:
            raise Exception("Can not find gut txt file", gutFile)

        return bret

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                加载滞时演算汇流图层参数                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def ReadInRoutingLayerData(self):
        DEMForld = util.config.workSpace + os.sep + "DEM"
        watershedFile = DEMForld + os.sep + util.config.watershed
        subbasinFile = DEMForld + os.sep + util.config.subbasin
        streamOrderFile = DEMForld + os.sep + util.config.streamOrder
        routingTime_GSTFile = DEMForld + os.sep + util.config.routingTime_GST
        routingTime_GLTFile = DEMForld + os.sep + util.config.routingTime_GLT
        routingTime_GBTFile = DEMForld + os.sep + util.config.routingTime_GBT

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
        self.m_MuskCoeffFile = util.config.workSpace + os.sep + "DEM" + os.sep + util.config.MuskCoeffFile
        if not os.path.exists(self.m_MuskCoeffFile):
            return False

        MuskCoeffLines = open(self.m_MuskCoeffFile, 'r').readlines()
        self.m_iNodeNum = int(MuskCoeffLines[0].rstrip(util.defines.CHAR_SPLIT_ENTER))
        if self.m_iNodeNum > 1:
            self.m_pX = []
            self.m_pK = []

            num = len(MuskCoeffLines)
            id = 0
            for i in range(2, num):
                saOut = MuskCoeffLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER)
                saOut = saOut.split(util.defines.CHAR_SPLIT_TAB)
                self.m_pX.append(float(saOut[1]))
                self.m_pK.append(float(saOut[2]))
                id += 1

        return True

    def MuskRouteInit(self, nodenum):
        self.pRiverRoute = CMuskRouteFlux()


        for i in range(nodenum):
            newRouteFlux = RouteFlux()
            self.pRiverRoute.pRoute.append(newRouteFlux)
            self.pRiverRoute.pPreRoute.append(newRouteFlux)

        for i in range(nodenum):
            self.pRiverRoute.pRoute[i].dInFlux = 0.
            self.pRiverRoute.pRoute[i].dOutFlux = 0.
            self.pRiverRoute.pPreRoute[i].dInFlux = 0.
            self.pRiverRoute.pPreRoute[i].dOutFlux = 0.

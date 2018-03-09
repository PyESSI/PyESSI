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

        self.soilTypeName = None
        self.vegTypeName = None
        self.solFile = {}
        self.vegFile = {}

        self.HortonInfil = CHortonInfil()
        self.gridwb = CGridWaterBalance()

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

        ### 加载土壤、植被和DEM图层 ###
        # 加载土壤、植被查找表
        self.LoadLookupTable()
        # 加载.sol和.veg信息
        self.LoadSolVegFile()

        # 栅格初始化
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

        ##模拟径流结果输出
        self.outQ = open(util.config.workSpace + os.sep + 'Output' + os.sep + 'outQ.txt', 'a')
        self.outQ.write("Date\tTotalQ\tSurfQ\tLatQ\tBaseQ\tDeepBaseQ\n")
        self.outQ.close()

        ##水文过程循环


        for theDay in daily:
            print('Calculating %s\t' % theDay, end='')
            s_long = time.clock()
            iMonth = int(theDay[4:6])

            iniDateTemp = datetime.date(int(theDay[0:4]), 1, 1)
            endDateTemp = datetime.date(int(theDay[0:4]), int(theDay[4:6]), int(theDay[6:8]))

            dayCountTemp = endDateTemp.toordinal() - iniDateTemp.toordinal() + 1

            # 初始化数值
            i = int(theDay[0:4])
            j = dayCountTemp

            dn = j
            dintensity = 0.
            dhr = 24.
            dhrIntensity = 0.
            dPE = 0.

            # 加载逐日驱动数据
            self.LoadForcingData(theDay)

            for row in range(self.m_row):
                for col in range(self.m_col):
                    if (row * self.m_row + col + 1) % int(self.m_row * self.m_col / 10) == 0:
                        print("•", end='')
                        sys.stdout.flush()

                    if not self.IfGridBeCalculated(row, col):
                        continue

                    dsnowfactor = 1.

                    if util.config.tmpmeandata == 1:
                        if gClimate_GridLayer.Tav[row][col] < util.config.SnowTemperature:
                            self.m_SnowWater[row][col] += gClimate_GridLayer.Pcp[row][col]
                            gClimate_GridLayer.Pcp[row][col] = 0.

                            dsnowfactor = 0.15
                        else:
                            if self.m_SnowWater[row][col] > 0:
                                smelt = self.DDFSnowMelt(gClimate_GridLayer.Tav[row][col],
                                                         util.config.SnowTemperature,
                                                         util.config.DDF, util.config.DailyMeanPcpTime)
                                if self.m_SnowWater[row][col] < smelt:
                                    smelt = self.m_SnowWater[row][col]
                                    self.m_SnowWater[row][col] = 0.
                                else:
                                    self.m_SnowWater[row][col] -= smelt
                                gClimate_GridLayer.Pcp[row][col] += smelt
                                dsnowfactor = 0.3

                    dhrIntensity = util.config.DailyMeanPcpTime

                    dintensity = gClimate_GridLayer.Pcp[row][col] / dhrIntensity
                    self.HortonInfil.SetGridPara(row, col, 0.03)
                    self.HortonInfil.HortonExcessRunoff()
                    gOut_GridLayer.drateinf[row][col] = self.HortonInfil.m_dFt

                    self.gridwb.SetGridPara(row, col, dintensity, i, j, dhrIntensity, theDay)
                    dalb = self.GetVegAlbedo(iMonth)
                    self.gridwb.CalcPET(dalb, theDay)

                    if not self.g_StrahlerRivNet.data[row][col] == 0:
                        gOut_GridLayer.SurfQ[row][col] = gClimate_GridLayer.Pcp[row][col] - self.gridwb.m_dPET
                        if gOut_GridLayer.SurfQ[row][col] < 0:
                            gOut_GridLayer.SurfQ[row][col] = 0.
                        if gOut_GridLayer.SurfQ[row][col] > 1e+10:
                            print('hello')
                        gOut_GridLayer.LateralQ[row][col] = 0.
                        gOut_GridLayer.BaseQ[row][col] = 0.
                        gOut_GridLayer.TotalQ[row][col] = gOut_GridLayer.SurfQ[row][col]
                        gOut_GridLayer.AET[row][col] = self.gridwb.m_dPET
                        gOut_GridLayer.CI[row][col] = 0.
                        gOut_GridLayer.CIDefict[row][col] = 0.
                        gOut_GridLayer.NetPcp[row][col] = gOut_GridLayer.SurfQ[row][col]
                        gOut_GridLayer.WaterYieldType[row][col] = 0
                        gOut_GridLayer.SoilProfileWater[row][col] = 0.
                        gOut_GridLayer.SoilAvgWater[row][col] = 0.

                    else:
                        self.gridwb.CalcCI()
                        gOut_GridLayer.CI[row][col] = self.gridwb.m_dCrownInterc
                        if gSoil_GridLayerPara.SP_Sw[row][col] / gSoil_GridLayerPara.SP_Fc[row][col] > 0.8:
                            if gClimate_GridLayer.Pcp[row][col] > 0:
                                aetfactor = 0.6
                            else:
                                aetfactor = 0.9
                        else:
                            if gClimate_GridLayer.Pcp[row][col] > 0:
                                aetfactor = 0.4
                            else:
                                aetfactor = 0.6

                        # //*************对蒸散发处理的特殊代码段 -- 计算实际蒸散发**************//
                        if util.config.PETMethod == util.defines.PET_REAL:

                            self.gridwb.m_dAET = gClimate_GridLayer.Pet[row][col] * aetfactor
                            gOut_GridLayer.AET[row][col] = self.gridwb.m_dAET
                        else:
                            self.gridwb.CalcAET(theDay, dalb)
                            if self.gridwb.m_dAET > gClimate_GridLayer.Pet[row][col]:
                                gOut_GridLayer.AET[row][col] = gClimate_GridLayer.Pet[row][col] * math.exp(
                                    -1 * gClimate_GridLayer.Pet[row][col] / self.gridwb.m_dAET)
                            if self.gridwb.m_dAET < 0:
                                gOut_GridLayer.AET[row][col] = gClimate_GridLayer.Pet[row][col] * 0.1

                        # // ** ** ** ** ** ** ** ** ** ** ** 对蒸散发处理的特殊代码段 ** ** ** ** ** ** ** ** ** ** **
                        self.gridwb.CalcNetRain()
                        gOut_GridLayer.CIDefict[row][col] = self.gridwb.m_dCIDeficit
                        gOut_GridLayer.NetPcp[row][col] = self.gridwb.m_dNetRain
                        gOut_GridLayer.WaterYieldType[row][col] = self.gridwb.CalcRunoffElement(row, col)
                        gOut_GridLayer.SoilProfileWater[row][col] = gSoil_GridLayerPara.SP_Sw[row][col]

                        gOut_GridLayer.SoilAvgWater[row][col] = gSoil_GridLayerPara.SP_Sw[row][col] / \
                                                        gSoil_GridLayerPara.rootdepth[row][col] * 100
                        gOut_GridLayer.TotalQ[row][col] = self.gridwb.m_dTotalQ
                        gOut_GridLayer.SurfQ[row][col] = self.gridwb.m_dSurfQ
                        gOut_GridLayer.LateralQ[row][col] = self.gridwb.m_dLateralQ
                        gOut_GridLayer.BaseQ[row][col] = self.gridwb.m_dBaseQ

                        if gOut_GridLayer.SurfQ[row][col] > 1e+10:
                            print("hello2")

            if self.m_iNodeNum == 1 or util.config.RiverRouteMethod == util.defines.ROUTE_PURE_LAG:
                self.m_pOutletSurfQ = self.PureLagGridRouting(gOut_GridLayer.SurfQ, self.m_pOutletSurfQ, dhr,
                                                              util.defines.RUNOFF_ELEMENT_SURFQ,
                                                              curorder, totrec, dsnowfactor,
                                                              self.wytype[int(theDay[0:4])])
                self.m_pOutletLatQ = self.PureLagGridRouting(gOut_GridLayer.LateralQ, self.m_pOutletLatQ, dhr,
                                                             util.defines.RUNOFF_ELEMENT_LATERALQ,
                                                             curorder, totrec, dsnowfactor,
                                                             self.wytype[int(theDay[0:4])])
                self.m_pOutletBaseQ = self.PureLagGridRouting(gOut_GridLayer.BaseQ, self.m_pOutletBaseQ, dhr,
                                                              util.defines.RUNOFF_ELEMENT_BASEQ,
                                                              curorder, totrec, dsnowfactor,
                                                              self.wytype[int(theDay[0:4])])
                self.m_pOutletDeepBaseQ[curorder] = self.DeepBaseQSim(dn, util.config.DeepBaseQ)
                self.m_pOutletQ[curorder] = self.m_pOutletSurfQ[curorder] * util.config.SurfQLinearFactor + \
                                            self.m_pOutletLatQ[curorder] + self.m_pOutletBaseQ[curorder] + \
                                            self.m_pOutletDeepBaseQ[curorder]
            else:
                self.m_pNodeSurfQ = self.PureLagGridRouting_Node(gOut_GridLayer.SurfQ, self.m_pNodeSurfQ, dhr,
                                                                 util.defines.RUNOFF_ELEMENT_SURFQ,
                                                                 curorder, totrec, dsnowfactor,
                                                                 self.wytype[int(theDay[0:4])])
                self.m_pNodeLatQ = self.PureLagGridRouting_Node(gOut_GridLayer.LateralQ, self.m_pNodeLatQ, dhr,
                                                                util.defines.RUNOFF_ELEMENT_LATERALQ,
                                                                curorder, totrec, dsnowfactor,
                                                                self.wytype[int(theDay[0:4])])
                self.m_pNodeBaseQ = self.PureLagGridRouting_Node(gOut_GridLayer.BaseQ, self.m_pNodeBaseQ, dhr,
                                                                 util.defines.RUNOFF_ELEMENT_BASEQ,
                                                                 curorder, totrec, dsnowfactor,
                                                                 self.wytype[int(theDay[0:4])])

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
                        self.pRiverRoute.pRoute, self.pRiverRoute.pPreRoute = self.MuskingumRiverRouting(24,
                                                                                                         self.m_pNodeOutQ,
                                                                                                         self.pRiverRoute.pRoute,
                                                                                                         self.pRiverRoute.pPreRoute,
                                                                                                         self.m_pX,
                                                                                                         self.m_pK,
                                                                                                         self.m_subNum,
                                                                                                         curorder)
                    self.m_pOutletQ[curorder] = self.pRiverRoute.pRoute[self.m_subNum - 1].dOutFlux + \
                                                self.m_pOutletDeepBaseQ[curorder]

                elif util.config.RiverRouteMethod == ROUTE_MUSKINGUM_ROUTE_FIRST:
                    print('TODO')

                else:
                    self.m_pOutletQ[curorder] = self.m_pOutletSurfQ[curorder] + self.m_pOutletLatQ[curorder] + \
                                                self.m_pOutletBaseQ[curorder] + self.m_pOutletDeepBaseQ[curorder]

            curorder += 1
            self.MidGridResultOut(theDay,
                                  gClimate_GridLayer.Pcp, gClimate_GridLayer.Pet,
                                  gClimate_GridLayer.Wnd, gClimate_GridLayer.Hmd,
                                  gClimate_GridLayer.Slr, gClimate_GridLayer.Tav,
                                  gClimate_GridLayer.Tmn, gClimate_GridLayer.Tmx)

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
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Pcp' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curPcp, self.g_DemLayer.geoTransform, self.g_DemLayer.srs,
                            self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iPET == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'PET' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curPet, self.g_DemLayer.geoTransform, self.g_DemLayer.srs,
                            self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iWnd == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Wnd' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curWnd, self.g_DemLayer.geoTransform, self.g_DemLayer.srs,
                            self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iHmd == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Hmd' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curHmd, self.g_DemLayer.geoTransform, self.g_DemLayer.srs,
                            self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSlr == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Slr' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curSlr, self.g_DemLayer.geoTransform, self.g_DemLayer.srs,
                            self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMean == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMean' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmean, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMin == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMin' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmn, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iTempMax == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'TempMax' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, curTmpmx, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)

            if util.config.iAET == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'AET' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.AET, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iCI == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'CI' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.CI, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSnowWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'Snow' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, self.m_SnowWater, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iAI == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'AI' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.AI, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iRouteOut == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'GridRoute' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.RoutingQ, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iSurfQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'SurfQ' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.SurfQ, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iLatQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'LatQ' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.LateralQ, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iBaseQ == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'BaseQ' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.BaseQ, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iWaterYieldType == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'WYType' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.WaterYieldType, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iInfilRate == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'InfilRate' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.m_drateinf, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iProfileSoilWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'SoilProfileWater' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.SoilProfileWater, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)
            if util.config.iAvgSoilWater == 1:
                filename = util.config.workSpace + os.sep + 'Output' + os.sep + 'SoilAvgWater' + curDay + '.tif'
                writeRaster(filename, self.m_row, self.m_col, gOut_GridLayer.SoilAvgWater, self.g_DemLayer.geoTransform,
                            self.g_DemLayer.srs, self.g_DemLayer.noDataValue, gdal.GDT_Float32)




    def RiverOutletQ_Hao(self, curDay, curOrder):
        self.outQ = open(util.config.workSpace + os.sep + 'Output' + os.sep + 'outQ.txt', 'a')
        self.outQ.write("%s\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\n" % (
        curDay, self.m_pOutletQ[curOrder], self.m_pOutletSurfQ[curOrder], self.m_pOutletLatQ[curOrder],
        self.m_pOutletBaseQ[curOrder], self.m_pOutletDeepBaseQ[curOrder]))
        self.outQ.close()

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
                        LagTime = int(self.g_RouteLatQTime.data[i][j] / dTlen)
                        LagOrder = int(curorder + LagTime)
                        if LagOrder < totorder:
                            dGridOut = snowfactor * GridQ[i][j] / (
                                util.config.LatQLoss * math.pow(self.g_RouteLatQTime.data[i][j], 1))
                            pRoute[LagOrder] += dGridOut
                    elif QType == util.defines.RUNOFF_ELEMENT_BASEQ:
                        LagTime = int(self.g_RouteBaseQTime.data[i][j] / dTlen)
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
            vegTemp = VegInfo(self.vegTypeName, self.vegFile)
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

                wyTypeTemp.year = int(
                    wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[0])
                wyTypeTemp.wtype = int(
                    wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[1])
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

        gBase_GridLayer.DEM = self.g_DemLayer.data
        gBase_GridLayer.Soil = self.g_SoilLayer.data
        gBase_GridLayer.Veg = self.g_VegLayer.data

        self.m_row = self.g_DemLayer.nRows
        self.m_col = self.g_DemLayer.nCols

        gSoil_GridLayerPara.SP_Sw = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Wp = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_WFCS = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Sat_K = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Stable_Fc = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Init_F0 = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.Horton_K = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Por = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.rootdepth = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Fc = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Sat = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.TPercolation = numpy.zeros((self.m_row, self.m_col))
        gSoil_GridLayerPara.SP_Temp = numpy.zeros((self.m_row, self.m_col))

        pGridVegInfoTemp = []
        vegTemp = None
        for i in range(self.m_row):
            for j in range(self.m_col):
                pGridVegInfoTemp.append(vegTemp)
        self.pGridVegInfo = numpy.array(pGridVegInfoTemp).reshape(self.m_row, self.m_col)

        gOut_GridLayer.TotalQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SurfQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.LateralQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.BaseQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.TempVal = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.WaterYieldType = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SoilProfileWater = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SoilAvgWater = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.RoutingQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.NetPcp = numpy.zeros((self.m_row, self.m_col))

        for i in range(self.m_row):
            for j in range(self.m_col):
                if (i * self.m_row + j + 1) % int(self.m_row * self.m_col / 10) == 0:
                    print("▋", end='')
                    sys.stdout.flush()
                if not self.IfGridBeCalculated(i, j):
                    continue
                if self.GetSoilTypeOrder(int(self.g_SoilLayer.data[i][j])):
                    soilTemp = SoilInfo(self.soilTypeName, self.solFile)
                    self.m_iSoilOrd = int(self.g_SoilLayer.data[i][j])
                    soilTemp.ReadSoilFile(self.soilTypeName[str(int(self.m_iSoilOrd))] + '.sol')
                    gSoil_GridLayerPara.SP_Sw[i][j] = soilTemp.SP_Sw
                    gSoil_GridLayerPara.SP_Wp[i][j] = soilTemp.SP_Wp
                    gSoil_GridLayerPara.SP_WFCS[i][j] = soilTemp.SP_WFCS
                    gSoil_GridLayerPara.SP_Sat_K[i][j] = soilTemp.SP_Sat_K
                    gSoil_GridLayerPara.SP_Stable_Fc[i][j] = soilTemp.SP_Stable_Fc
                    gSoil_GridLayerPara.SP_Init_F0[i][j] = soilTemp.SP_Init_F0
                    gSoil_GridLayerPara.Horton_K[i][j] = soilTemp.Horton_K
                    gSoil_GridLayerPara.SP_Por[i][j] = soilTemp.SP_Por
                    gSoil_GridLayerPara.rootdepth[i][j] = soilTemp.rootdepth
                    gSoil_GridLayerPara.SP_Fc[i][j] = soilTemp.SP_Fc
                    gSoil_GridLayerPara.SP_Sat[i][j] = soilTemp.SP_Sat
                    gSoil_GridLayerPara.TPercolation[i][j] = (soilTemp.SP_Sat - soilTemp.SP_Fc) / (soilTemp.SP_Sat_K)
                    gSoil_GridLayerPara.SP_Temp[i][j] = 0.

                    vegTemp = VegInfo(self.vegTypeName, self.vegFile)
                    self.m_iVegOrd = self.g_VegLayer.data[i][j]
                    vegTemp.ReadVegFile(self.vegTypeName[str(int(self.m_iVegOrd))] + '.veg')
                    self.pGridVegInfo[i][j] = vegTemp

        gVeg_GridLayerPara.Veg = self.pGridVegInfo

        e = time.clock()
        print('\nFinished Load grid parameters：%.3f' % (e - s))

    def GridLayerInit_Horton(self):
        gOut_GridLayer.AET = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.drateinf = numpy.zeros((self.m_row, self.m_col))

    def GridLayerInit_GreenAmpt(self):
        self.GridLayerInit_Horton()
        gOut_GridLayer.drintns = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dcumr = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dcuminf = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dexcum = numpy.zeros((self.m_row, self.m_col))

    def GridLayerInit_LongTerm(self):
        gOut_GridLayer.drateinf = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.AET = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SnowWater = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CIDefict = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.AI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.NetPcp = numpy.zeros((self.m_row, self.m_col))

    def GridMemFreeAndNew(self):
        gOut_GridLayer.TotalQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SurfQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.LateralQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.BaseQ = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.RoutingQ = numpy.zeros((self.m_row, self.m_col))

        gOut_GridLayer.NetPcp = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.WaterYieldType = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SoilProfileWater = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SoilAvgWater = numpy.zeros((self.m_row, self.m_col))

    def GridMemFreeAndNew_Horton(self):
        gOut_GridLayer.AET = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.drateinf = numpy.zeros((self.m_row, self.m_col))

    def GridMemFreeAndNew_LongTerm(self):
        gOut_GridLayer.drateinf = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.drintns = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dcumr = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dcuminf = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.dexcum = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.AI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.SnowWater = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CIDefict = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.AET = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.NetPcp = numpy.zeros((self.m_row, self.m_col))

    def GridMemFreeAndNew_GreenAmpt(self):
        gOut_GridLayer.AI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CI = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.CIDefict = numpy.zeros((self.m_row, self.m_col))
        gOut_GridLayer.AET = numpy.zeros((self.m_row, self.m_col))

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

    def LoadLookupTable(self):
        '''
        Load Soil and Veg Lookup Table
        :return:
        '''
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

    def LoadSolVegFile(self):
        '''
        加载.sol和.veg信息
        :return:
        '''
        solFileList, solFileName = getFileList(util.config.workSpace + os.sep + "Soil", ".sol")
        vegFileList, vegFileName = getFileList(util.config.workSpace + os.sep + "Vegetation", ".veg")
        for s in range(len(solFileList)):
            solFileInfo = open(solFileList[s], 'r').readlines()
            self.solFile[solFileName[s] + ".sol"] = solFileInfo
        for v in range(len(vegFileList)):
            vegFileInfo = open(vegFileList[v], 'r').readlines()
            self.vegFile[vegFileName[v] + ".veg"] = vegFileInfo

    def LoadForcingData(self, theDay):
        '''
        加载逐日驱动数据
        :return:
        '''
        if self.m_row == 0 or self.m_col == 0:
            raise Exception("row or col can not be zero!", self.m_row, self.m_col)

        if util.config.pcpdata == 1:
            curPcp = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'pcpdata' + os.sep + theDay + '.tif').data
        else:
            curPcp = numpy.zeros((self.m_row, self.m_col))

        if util.config.petdata == 1:
            curPet = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'petdata' + os.sep + theDay + '.tif').data
        else:
            curPet = numpy.zeros((self.m_row, self.m_col))

        if util.config.tmpmeandata == 1:
            curTmpmean = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmeandata' + os.sep + theDay + '.tif').data
        else:
            curTmpmean = numpy.zeros((self.m_row, self.m_col))

        if util.config.tmpmxdata == 1:
            curTmpmx = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmxdata' + os.sep + theDay + '.tif').data
        else:
            curTmpmx = numpy.zeros((self.m_row, self.m_col))

        if util.config.tmpmndata == 1:
            curTmpmn = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmndata' + os.sep + theDay + '.tif').data
        else:
            curTmpmn = numpy.zeros((self.m_row, self.m_col))

        if util.config.wnddata == 1:
            curWnd = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'wnddata' + os.sep + theDay + '.tif').data
        else:
            curWnd = numpy.zeros((self.m_row, self.m_col))

        if util.config.hmddata == 1:
            curHmd = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'hmddata' + os.sep + theDay + '.tif').data
        else:
            curHmd = numpy.zeros((self.m_row, self.m_col))
        if util.config.slrdata == 1:
            curSlr = readRaster(
                util.config.workSpace + os.sep + 'Forcing' + os.sep + 'slrdata' + os.sep + theDay + '.tif').data
        else:
            curSlr = numpy.zeros((self.m_row, self.m_col))

        # 将驱动数据加入全局变量，逐时间步长更新
        gClimate_GridLayer.Pcp = curPcp
        gClimate_GridLayer.Pet = curPet
        gClimate_GridLayer.Tav = curTmpmean
        gClimate_GridLayer.Tmx = curTmpmx
        gClimate_GridLayer.Tmn = curTmpmn
        gClimate_GridLayer.Wnd = curWnd
        gClimate_GridLayer.Hmd = curHmd
        gClimate_GridLayer.Slr = curSlr
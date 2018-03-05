# load needed python modules
import numpy
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
        print('LongTermRunoffSimulate')
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
        self.gridLayerInit()
        self.GridMemFreeAndNew()
        self.GridLayerInit_LongTerm()
        self.GridMemFreeAndNew_LongTerm()

        self.m_SnowWater = numpy.zeros([self.m_row, self.m_col])

        startDay = util.config.startTime
        endDay = util.config.endTime

        iniDate = datetime.date(int(startDay[0:4]), int(startDay[4:6]), int(startDay[6:8]))
        endDate = datetime.date(int(endDay[0:4]), int(endDay[4:6]), int(endDay[6:8]))
        dayCount = endDate.toordinal() - iniDate.toordinal() + 1
        daily = dailyRange(startDay, endDay)

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
                wytypeTemp.wtype = util.defines.WATER_LOW_YEAR

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

            if util.config.pcpdata == 1:
                curPcp = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'pcpdata' + os.sep + theDay + '.tif').data
            else:
                curPcp = numpy.zeros((self.m_row,self.m_col))

            if util.config.petdata == 1:
                curPet = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'petdata' + os.sep + theDay + '.tif').data
            else:
                curPet = numpy.zeros((self.m_row,self.m_col))

            if util.config.tmpmeandata == 1:
                curTmpmean = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmeandata' + os.sep + theDay + '.tif').data
            else:
                curTmpmean = numpy.zeros((self.m_row,self.m_col))

            if util.config.tmpmxdata == 1:
                curTmpmx = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmxdata' + os.sep + theDay + '.tif').data
            else:
                curTmpmx = numpy.zeros((self.m_row,self.m_col))

            if util.config.tmpmndata == 1:
                curTmpmn = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmndata' + os.sep + theDay + '.tif').data
            else:
                curTmpmn = numpy.zeros((self.m_row,self.m_col))

            if util.config.wnddata == 1:
                curWnd = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'wnddata' + os.sep + theDay + '.tif').data
            else:
                curWnd = numpy.zeros((self.m_row,self.m_col))

            if util.config.hmddata == 1:
                curHmd = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'hmddata' + os.sep + theDay + '.tif').data
            else:
                curHmd = numpy.zeros((self.m_row,self.m_col))
            if util.config.slrdata == 1:
                curSlr = readRaster(
                    util.config.workSpace + os.sep + 'Forcing' + os.sep + 'slrdata' + os.sep + theDay + '.tif').data
            else:
                curSlr = numpy.zeros((self.m_row,self.m_col))


            for row in range(self.m_row):
                for col in range(self.m_col):
                    if (row*self.m_row + col)%int(self.m_row*self.m_col/100) == 0:
                        print("%f%%-" % ((row*self.m_row + col)/int(self.m_row*self.m_col/100)), end='')
                        sys.stdout.flush()
                    if not self.IfGridBeCalculated(row, col):
                        continue

                    dsnowfactor = 1.
                    if util.config.tmpmeandata == 1:
                        if curTmpmean.data[row][col] < util.config.SnowTemperature:
                            self.m_SnowWater[row][col] += curPcp[row][col]
                            curPcp[row][col] = 0.
                            dsnowfactor = 0.15
                        else:
                            if self.m_SnowWater[row][col] > 0:
                                smelt = self.DDFSnowMelt(curTmpmean.data[row][col], util.config.SnowTemperature,
                                                         util.config.DDF, util.config.DailyMeanPcpTime)
                                if self.m_SnowWater[row][col] < smelt:
                                    smelt = self.m_SnowWater[row][col]
                                    self.m_SnowWater[row][col] = 0.
                                else:
                                    self.m_SnowWater[row][col] -= smelt
                                curPcp[row][col] += smelt
                                dsnowfactor = 0.3

                    dhrIntensity = util.config.DailyMeanPcpTime
                    dintensity = curPcp[row][col] / dhrIntensity
                    self.HortonInfil.SetGridPara(row, col, self.pGridSoilInfo_SP_Sw[row][col], 0.03)

                    self.HortonInfil.HortonExcessRunoff()
                    self.m_drateinf[row][col] = self.HortonInfil.m_dFt

                    pGridSoilInfo = SoilInfo()
                    pGridSoilInfo.ReadSoilFile(GetSoilTypeName(int(self.g_SoilLayer.data[row][col])) + '.sol')
                    dthet = pGridSoilInfo.SoilWaterDeficitContent()

                    self.gridwb = CGridWaterBalance(self.g_DemLayer.data[row][col], self.g_SoilLayer.data[row][col], self.g_VegLayer.data[row][col],
                                                    curPet[row][col], curPcp[row][col], curTmpmean[row][col], curTmpmx[row][col], curTmpmn[row][col], curSlr[row][col], curHmd[row][col], curWnd[row][col])

                    self.gridwb.SetGridPara(dintensity, self.m_drateinf[row][col], i, j, dhrIntensity, theDay)

                    dalb = self.GetVegAlbedo(iMonth)

                    self.gridwb.CalcPET(dalb, theDay)

                    if not self.g_StrahlerRivNet.data[row][col] == 0:
                        self.m_GridSurfQ[row][col] = curPcp[row][col] - self.gridwb.m_dPET
                        if self.m_GridSurfQ[row][col] < 0:
                            self.m_GridSurfQ[row][col] = 0.
                        if self.m_GridSurfQ[row][col] > 1e+10:
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
                            if curPcp[row][col] > 0:
                                aetfactor = 0.6
                            else:
                                aetfactor = 0.9
                        else:
                            if curPcp[row][col] > 0:
                                aetfactor = 0.4
                            else:
                                aetfactor = 0.6


                        # //*************对蒸散发处理的特殊代码段 -- 计算实际蒸散发**************//
                        if util.config.PETMethod == util.defines.PET_REAL:
                            self.gridwb.m_dAET = curPet[row][col] * aetfactor
                            self.m_AET[row][col] = self.gridwb.m_dAET
                        else:
                            self.gridwb.CalcAET(dalb,theDay)
                            if self.gridwb.m_dAET > curPet[row][col]:
                                self.m_AET[row][col] = curPet[row][col] * math.exp(-1 * curPet[row][col] / self.gridwb.m_dAET)
                            if self.gridwb.m_dAET < 0:
                                self.m_AET[row][col] = curPet[row][col] * 0.1

                        #// ** ** ** ** ** ** ** ** ** ** ** 对蒸散发处理的特殊代码段 ** ** ** ** ** ** ** ** ** ** **
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
        waterYearTypeFile = util.config.workSpace + os.sep + 'DEM' + os.sep + util.config.WaterYearTypeFile
        if os.path.exists(waterYearTypeFile):
            self.wytype = []
            wytypeFile = open(waterYearTypeFile, 'r')
            wytypeLines = wytypeFile.readlines()
            wytypeFile.close()

            for i in range(len(wytypeLines)):
                wyTypeTemp = WaterYearType()
                wyTypeTemp.year = wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[0]
                wyTypeTemp.wtype = wytypeLines[i].rstrip(util.defines.CHAR_SPLIT_ENTER).split(util.defines.CHAR_SPLIT_TAB)[1]

                self.wytype.append(wyTypeTemp)
            return True

        else:
            return False

    # 加载栅格参数
    def gridLayerInit(self):
        DEMFolder = util.config.workSpace + os.sep + "DEM"
        DEMFile = DEMFolder + os.sep + util.config.DEMFileName
        LULCFile = DEMFolder + os.sep + util.config.LULCFileName
        SoilFile = DEMFolder + os.sep + util.config.SoilFileName

        self.g_DemLayer = readRaster(DEMFile)
        self.g_VegLayer = readRaster(LULCFile)
        self.g_SoilLayer = readRaster(SoilFile)

        self.m_row = self.g_DemLayer.nRows
        self.m_col = self.g_DemLayer.nCols

        self.pGridSoilInfo_SP_Sw = numpy.empty((self.m_row,self.m_col))

        self.pGridSoilInfo_SP_Wp = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_WFCS = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Sat_K = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Stable_Fc = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Init_F0 = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_Horton_K = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Por = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_rootdepth = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Fc = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Sat = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_TPercolation = numpy.empty((self.m_row,self.m_col))
        self.pGridSoilInfo_SP_Temp = numpy.zeros((self.m_row,self.m_col))

        pGridVegInfoTemp = []
        vegTemp = None
        for i in range(self.m_row):
            for j in range(self.m_col):
                pGridVegInfoTemp.append(vegTemp)

        self.pGridVegInfo = numpy.array(pGridVegInfoTemp).reshape(self.m_row,self.m_col)

        self.m_GridTotalQ = numpy.empty((self.m_row,self.m_col))
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
                if not self.IfGridBeCalculated(i, j):
                    continue
                if self.GetSoilTypeOrder(int(self.g_SoilLayer.data[i][j])):
                    soilTemp = SoilInfo()
                    self.m_iSoilOrd = int(self.g_SoilLayer.data[i][j])
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
        print('栅格参数加载完毕')


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
        self.m_GridTotalQ = numpy.empty((self.m_row,self.m_col))
        self.m_GridSurfQ = numpy.empty((self.m_row,self.m_col))
        self.m_GridLateralQ = numpy.empty((self.m_row,self.m_col))
        self.m_GridBaseQ = numpy.empty((self.m_row,self.m_col))
        self.m_GridRoutingQ = numpy.empty((self.m_row,self.m_col))

        self.m_NetPcp = numpy.empty((self.m_row,self.m_col))
        self.m_GridWaterYieldType = numpy.empty((self.m_row,self.m_col))
        self.m_SoilProfileWater = numpy.empty((self.m_row,self.m_col))
        self.m_SoilAvgWater = numpy.empty((self.m_row,self.m_col))

    def GridMemFreeAndNew_Horton(self):
        self.m_AET  = numpy.empty((self.m_row,self.m_col))
        self.m_drateinf  = numpy.zeros((self.m_row,self.m_col))

    def GridMemFreeAndNew_LongTerm(self):
        self.m_drateinf = numpy.zeros((self.m_row,self.m_col))
        self.m_drintns = numpy.zeros((self.m_row,self.m_col))
        self.m_dcumr = numpy.zeros((self.m_row,self.m_col))
        self.m_dcuminf = numpy.zeros((self.m_row,self.m_col))
        self.m_dexcum = numpy.zeros((self.m_row,self.m_col))
        self.m_AI = numpy.zeros((self.m_row,self.m_col))
        self.m_CI = numpy.zeros((self.m_row,self.m_col))
        self.m_SnowWater = numpy.zeros((self.m_row,self.m_col))
        self.m_CIDefict = numpy.empty((self.m_row,self.m_col))
        self.m_AET = numpy.empty((self.m_row,self.m_col))
        self.m_NetPcp = numpy.empty((self.m_row,self.m_col))

    def GridMemFreeAndNew_GreenAmpt(self):
        self.m_AI = numpy.empty((self.m_row,self.m_col))
        self.m_CI = numpy.empty((self.m_row,self.m_col))
        self.m_CIDefict = numpy.empty((self.m_row,self.m_col))
        self.m_AET = numpy.empty((self.m_row,self.m_col))





































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
    def GetSoilTypeOrder(self,sid):
        bret = False
        soilname = GetSoilTypeName(int(sid))
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
                if i % int(num / 100) == 0:
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



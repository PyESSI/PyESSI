# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Class:


"""

# load needed python modules
from utils.fileIO import *
import utils.config
import utils.defines
from modules.Hydro.SoilPara import *
from modules.Hydro.VegetationPara import *
from modules.Hydro.CanopyStorage import *


# /*+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +														+
# +	 ***********************************************    +
# +	 *										       *	+
# +	 *     栅格水量平衡类 -- CGridWaterBalance       *	    +
# +  *											   *    +
# +
# +	 ***********************************************    +
# +	 *											   *	+
# +    *   功能：模拟栅格产水过程，包括以下子过程：  *    +
# +	 *   子过程1：林冠截留   -- CalcCI();		   *	+
# +	 *   子过程2：潜在蒸散量 -- CalcPET();		   *	+
# +	 *   子过程3：实际蒸散量 -- CalcAET();		   *	+
# +	 *   子过程4：干旱指数   -- CalcAI();		   *	+
# +	 *										       *	+
# +    ***********************************************	+
# +														+
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
class CGridWaterBalance:
    def __init__(self):
        self.m_dCrownInterc = 0.
        self.m_dGridLAI = 0.
        self.m_dRIntensity = 0.

    # /*+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +														+
    # +				功能：设置栅格计算参数					+
    # +														+
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
    def SetGridPara(self, currow, curcol, rint, dFp, year, dn, hr, curForcingFilename):
        '''
        :param curcol:
        :param rint:
        :param dFp:
        :param year:
        :param dn:
        :param hr:
        :return:
        '''
        self.m_row = currow
        self.m_col = curcol
        self.m_dRIntensity = rint
        self.m_nYear = year
        self.m_nDn = dn
        self.m_dFp = dFp
        self.m_dHr = hr

        curPcp = readRaster(utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'pcpdata' + os.sep + curForcingFilename)
        self.m_dPcp = curPcp.data[self.m_row][self.m_col]

        curHeight = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.DEMFileName)
        self.m_dHeight = curHeight.data[self.m_row][self.m_col]

        soilTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.SoilFileName)
        pGridSoilInfo = SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(soilTemp.data[self.m_row][self.m_col]) + '.sol')
        self.m_dFc = pGridSoilInfo.SP_Stable_Fc

        if utils.config.RunoffSimuType==utils.defines.STORM_RUNOFF_SIMULATION:
            return

        if utils.config.petdata == 0:
            curTav = readRaster(utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmeandata' + os.sep + curForcingFilename)
            self.m_dTav = curTav.data[self.m_row][self.m_col]

        self.m_nMon = int(curForcingFilename[4:6])
        self.m_dGridLAI = self.DailyLai()
        self.m_dGridCovDeg = self.DailyCoverDeg()

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                    功能：计算冠层截留 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcCI(self):
        m_CanopyStore = CCanopyStorage()
        m_CanopyStore.SetGridValue(self.m_dGridLAI, self.m_dPcp, self.m_dGridCovDeg, 0.046)
        self.m_dCrownInterc = m_CanopyStore.CanopyStore()

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格潜在蒸散量 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /

    #chen 未完成
    def CalcPET(self,dalbedo,curForcingFilename):
        self.m_dPET = 0.

        if utils.config.PETMethod == utils.defines.PET_REAL:
            curPet = readRaster(utils.config.workSpace + os.sep + 'Forcing' + os.sep + 'petdata' + os.sep + curForcingFilename)
            self.m_dPET = curPet.data[self.m_row][self.m_col]

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格实际蒸散量 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +        由于Kojima法会出现比较大的空间不连续性，所以 +
    # +        目前只有互补相关理论法可以用。                    +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    # chen 未完成
    def CalcAET(self, dalbedo, curForcingFilename):
        self.m_dAET = 0.
        if self.m_dPET == 0:
            return

        if utils.config.AETMethod == utils.defines.AET_BY_CROP_COEFFICIENTS:
            self.m_dAET = self.CompleAET(dalbedo)
        elif utils.config.AETMethod == utils.defines.AET_BY_COMPRELATIONSHIP:
            self.m_dAET = self.CompleAET(dalbedo)
        elif utils.config.AETMethod == utils.defines.AET_BY_COMPRELA_AND_KOJIMA:
            self.m_dAET = self.CompleAET(dalbedo)
        else:
            return

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        功能：互补相关理论法计算实际蒸散发 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    #chen 未完成
    def CompleAET(self,dalbedo):
        print('chen 未完成')

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        功能：计算干旱指数 - - AridIndex = (PET / pcp) +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcAI(self):
        m_dAI = 0.

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +            功能：计算到达栅格的净雨量 +
    # +        (降雨中扣除冠层截留, 填洼暂时忽略) +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcNetRain(self):
        self.m_dNetRain = self.m_dPcp
        if self.m_dPcp < self.m_dCrownInterc:
            self.m_dCIDeficit = self.m_dCrownInterc - self.m_dPcp
            self.m_dNetRain = 0.
        else:
            self.m_dCIDeficit = 0.
            self.m_dNetRain = self.m_dPcp - self.m_dCrownInterc

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格总径流 +
    # +        (原理见博士论文：栅格水量平衡关系计算产流)        +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        总径流 ＝ 地表径流 ＋ 壤中流 ＋ 地下径流 +
    # +            1、计算地表径流 +
    # +            2、计算壤中流 +
    # +            3、计算地下径流 +
    # +            4、计算土壤含水量变化 +
    # +                                                        +
    # +        返回值：栅格产流类型；                            +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        调用本函数前的主要输入参数：                    +
    # +            m_dNetRain - - 栅格净雨；                    +
    # +            m_dAET - - 实际蒸散量；                +
    # +            m_dRIntensity - - 雨强；                        +
    # +            m_dFc - - 土壤稳定下渗率；            +
    # +            m_dFp - - 时段土壤下渗率；            +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcRunoffElement(self):
        iret = 0
        dthet = 0.
        dPE = 0.
        dIFc = 0.
        dIFp = 0.
        dPerco = 0.
        dRecharge = 0.
        dBaseQ = 0.
        dLatQ = 0.

        soilTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.SoilFileName)
        pGridSoilInfo = SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(soilTemp.data[self.m_row][self.m_col]) + '.sol')
        dthet = pGridSoilInfo.SoilWaterDeficitContent()
        dPE = self.m_dNetRain - self.m_dAET

        dIFc = self.m_dRIntensity - self.m_dFc
        dIFp = self.m_dRIntensity - self.m_dFp

        self.m_dTotalQ =0.
        self.m_dSurfQ = 0.
        self.m_dLateralQ = 0.
        self.m_dBaseQ = 0.
        self.dBaseQ = 0.
        self.dLatQ = 0.

        if dthet < 0.:
            if dPE < 0.:
                if dIFc < 0.: # 方案1：不产流
                    iret = 1
                else: # 方案2：超渗产流
                    m_dSurfQ = dIFc * self.m_dHr
                    iret = 2
            else:
                if dIFc < 0.: # 方案3：蓄满产流
                    self.m_dBaseQ = self.m_dFc * self.m_dHr
                    self.m_dSurfQ = dPE - self.m_dBaseQ
                    if self.m_dSurfQ < 0:
                        self.m_dSurfQ = dPE * utils.config.SurfQOutFactor
                        self.m_dBaseQ = dPE * (1 - utils.config.SurfQOutFactor)
                    iret = 3
                else:   #方案4：超渗产流＋蓄满产流
                    self.m_dSurfQ = dIFc * self.m_dHr
                    self.m_dBaseQ = self.m_dFc * self.m_dHr
                    if self.m_dSurfQ + self.m_dBaseQ > dPE:
                        self.m_dBaseQ = dPE - self.m_dSurfQ
                        if self.m_dBaseQ < 0:
                            self.m_dSurfQ = dPE * utils.config.SurfQOutFactor
                            self.m_dBaseQ = dPE * (1 - utils.config.SurfQOutFactor)

                    else:
                        self.m_dLateralQ = dPE - self.m_dSurfQ - self.m_dBaseQ

                    iret = 4
        else:
            if dPE < dthet:
                if dIFp <0.:  #方案5：不产流
                    iret = 5
                else:    #方案6：超渗产流
                    self.m_dSurfQ = dIFp * self.m_dHr
                    iret = 6
            else:
                if dIFp <0.:    #方案7：蓄满产流
                    self.m_dBaseQ = self.m_dFp * self.m_dHr
                    self.m_dSurfQ = dPE - dthet - self.m_dBaseQ
                    if self.m_dSurfQ < 0:
                        self.m_dSurfQ = (dPE - dthet) * utils.config.SurfQOutFactor
                        self.m_dBaseQ = (dPE - dthet) * (1 - utils.config.SurfQOutFactor)
                    iret = 7
                else:    #方案8：超渗产流＋蓄满产流
                    self.m_dTotalQ = dPE - dthet
                    self.m_dSurfQ = dIFp * self.m_dHr
                    self.m_dBaseQ = self.m_dFp * self.m_dHr
                    if self.m_dSurfQ > self.m_dTotalQ:
                        self.m_dBaseQ = 0.
                        self.m_dSurfQ = self.m_dTotalQ
                        self.m_dLateralQ = 0.
                    elif self.m_dSurfQ + self.m_dBaseQ > self.m_dTotalQ:
                        self.m_dBaseQ = self.m_dTotalQ - self.m_dSurfQ
                        if self.m_dBaseQ < 0:
                            self.m_dSurfQ = (dPE - dthet) * utils.config.SurfQOutFactor
                            self.m_dBaseQ = (dPE - dthet) * (1 - utils.config.SurfQOutFactor)

                            self.m_dLateralQ = 0.
                    else:
                        self.m_dLateralQ = self.m_dTotalQ - self.m_dSurfQ - self.m_dBaseQ
                    iret = 8

        pGridSoilInfo.SP_Sw += (dPE - self.m_dBaseQ - self.m_dSurfQ - self.m_dLateralQ)
        if pGridSoilInfo.SP_Sw > pGridSoilInfo.SP_Wp:
            if iret == 3 or iret == 4 or iret == 7 or iret == 8:
                dPerco = self.SWPercolation(pGridSoilInfo.SP_Sw, pGridSoilInfo.SP_Fc, self.m_dHr,  pGridSoilInfo.TPercolation)
                if dPerco > 0:
                    pGridSoilInfo.SP_Sw -= dPerco
                    self.m_dBaseQ += dPerco

                    dLatQ = dPerco * utils.config.LatQOutFactor
                    self.m_dLateralQ += dLatQ
                    pGridSoilInfo.SP_Sw -= dLatQ

            if pGridSoilInfo.SP_Sw > pGridSoilInfo.SP_Wp:
                dRecharge = self.SWRecharge(pGridSoilInfo.SP_Sw,self.m_dHr,self.m_dFp,pGridSoilInfo.SP_Init_F0)
                if dRecharge > pGridSoilInfo.SP_Sw -pGridSoilInfo.SP_Wp:
                    dRecharge = pGridSoilInfo.SP_Sw - pGridSoilInfo.SP_Wp
                self.dBaseQ = dRecharge * (1 - math.exp(-1 * (dRecharge / pGridSoilInfo.SP_Sw)))
                if self.dBaseQ < 0:
                    self.dBaseQ = 0.
                self.m_dBaseQ += self.dBaseQ
                pGridSoilInfo.SP_Sw -= self.dBaseQ
        else:
            pGridSoilInfo.SP_Sw = pGridSoilInfo.SP_Wp * 1.05

        if self.m_dBaseQ < 0:
            print("计算的地下径流分量为负"+ "GridWaterBalance")
        if self.m_dSurfQ < 0:
            print("计算的地表径流分量为负" + "GridWaterBalance")
        if self.m_dLateralQ < 0:
            print("计算的壤中径流分量为负" + "GridWaterBalance")

        return iret


    def SWPercolation(self, sw, fc, dt, dtPerco):
        '''
        功能：计算超过土壤田间持水量的土壤水下渗
        :param sw:
        :param fc:
        :param dt:
        :param dtPerco:
        :return:
        '''
        dret = 0.
        swexcess = 0.
        if sw > fc:
            swexcess = sw - fc
        else:
            swexcess = 0.
        dret = swexcess * (1 - math.exp(-1 * (dt / dtPerco)))
        return dret

    def SWRecharge(self, sw, dt, dInfilRate, dInitInfRate):
        '''
        功能：计算无降雨时正常的时段土壤退水量
        :param sw:
        :param dt:
        :param dInfilRate:
        :param dInitInfRate:
        :return:
        '''
        dret = 0.
        if dInfilRate < dInitInfRate:
            dret = dInfilRate * dt
        return dret


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                                +
    # +                            栅格公用变量推算 +
    # +                                                                +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    #
    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        功能：计算逐日LAI值 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyLai(self):
        dLai = 0.5
        vegTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.LULCFileName)
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(vegTemp.data[self.m_row][self.m_col]) + '.veg')
        if utils.config.DLAICalcMethod == utils.defines.DAILY_LAI_CAL_SINE:
            dmax = pGridVegInfo.LAIMX
            dmin = pGridVegInfo.LAIMN
            doffset = pGridVegInfo.doffset
            dLai = (dmax + dmin) / 2. - (dmax - dmin) * math.sin(2 * math.pi * (self.m_nDn - doffset) / 365.) / 2.
        elif utils.config.DLAICalcMethod == utils.defines.DAILY_LAI_CAL_LINEAR:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]

        elif utils.config.DLAICalcMethod == utils.defines.DAILY_LAI_BY_MONTH:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]

        else:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]

        return dLai


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格逐日Albedo +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyAlbedo(self):
        vegTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.LULCFileName)
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(vegTemp.data[self.m_row][self.m_col]) + '.veg')
        dAlb = 0.23
        dAlb = pGridVegInfo.Albedo[self.m_nMon - 1]
        return dAlb


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格逐日盖度 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyCoverDeg(self):
        vegTemp = readRaster(utils.config.workSpace + os.sep + 'DEM' + os.sep + utils.config.LULCFileName)
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(vegTemp.data[self.m_row][self.m_col]) + '.veg')
        dCovD = 0.
        dCovD = pGridVegInfo.CoverDeg[self.m_nMon - 1]
        return dCovD
























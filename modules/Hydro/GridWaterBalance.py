# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Class:
    CGridWaterBalance
     functions:
        SetGridPara(self, currow, curcol, rint, dFp, year, dn, hr, curForcingFilename)
        CalcCI(self)
        CalcPET(self,dalbedo,curForcingFilename)
        CalcAET(self, dalbedo, curForcingFilename)
        CompleAET(self,dalbedo =0.23)
        CalcAI(self)
        CalcNetRain(self)
        CalcRunoffElement(self)
        SWPercolation(self, sw, fc, dt, dtPerco)
        SWRecharge(self, sw, dt, dInfilRate, dInitInfRate)
        DailyLai(self)
        DailyAlbedo(self)
        DailyCoverDeg(self)


"""

# load needed python modules
from util.fileIO import *
import util.config
import util.defines
from modules.Hydro.SoilPara import *
from modules.Hydro.VegetationPara import *
from modules.Hydro.CanopyStorage import *
from modules.Climate.PETInPristley import *


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
    def __init__(self, elev, soil, veg, pet, pcp, tav, tmx, tmn, slr, hmd, wnd):
        '''
        Set variance values
        :param elev: DEM
        :param soil: Soil type
        :param veg: LUCC type
        :param pet:
        :param pcp:
        :param tav:
        :param tmx:
        :param tmn:
        :param slr:
        :param hmd:
        :param wnd:
        '''
        self.m_dCrownInterc = 0.
        self.m_dGridLAI = 0.
        self.m_dRIntensity = 0.

        # 当前栅格值
        self.m_dHeight = elev
        self.m_Soil = soil
        self.m_Veg = veg

        self.m_dPET = pet
        self.m_dPcp = pcp
        self.m_dTav = tav
        self.m_dTmx = tmx
        self.m_dTmn = tmn
        self.m_slr = slr
        self.m_hmd = hmd
        self.m_wnd = wnd

    # /*+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +														+
    # +				功能：设置栅格计算参数					    +
    # +														+
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++*/
    def SetGridPara(self, rint, dFp, year, dn, hr, curForcingFilename):
        '''
        :param curcol:
        :param rint:
        :param dFp:
        :param year:
        :param dn:
        :param hr:
        :return:
        '''
        self.m_dRIntensity = rint
        self.m_nYear = year
        self.m_nDn = dn
        self.m_dFp = dFp
        self.m_dHr = hr


        pGridSoilInfo = SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(int(self.m_Soil)) + '.sol')
        self.m_dFc = pGridSoilInfo.SP_Stable_Fc

        if util.config.RunoffSimuType == util.defines.STORM_RUNOFF_SIMULATION:
            return

        self.m_nMon = int(curForcingFilename[4:6])
        self.m_dGridLAI = self.DailyLai()
        self.m_dGridCovDeg = self.DailyCoverDeg()

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                    功能：计算冠层截留                    +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcCI(self):
        m_CanopyStore = CCanopyStorage()
        m_CanopyStore.SetGridValue(self.m_dGridLAI, self.m_dPcp, self.m_dGridCovDeg, 0.046)
        self.m_dCrownInterc = m_CanopyStore.CanopyStore()

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格潜在蒸散量                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcPET(self, dalbedo, curForcingFilename):
        tmpmxPath = util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmxdata'
        tmpmnPath = util.config.workSpace + os.sep + 'Forcing' + os.sep + 'tmpmndata'
        slrPath = util.config.workSpace + os.sep + 'Forcing' + os.sep + 'slrdata'
        hmdPath = util.config.workSpace + os.sep + 'Forcing' + os.sep + 'hmddata'
        wndPath = util.config.workSpace + os.sep + 'Forcing' + os.sep + 'wnddata'

        ## 判断选择的方法 ##
        if util.config.PETMethod == util.defines.PET_REAL:
            pass
        if not os.path.exists(tmpmxPath + os.sep + curForcingFilename) or not os.path.exists(
                                tmpmnPath + os.sep + curForcingFilename):
            return 0
        dRLong = 0
        dRShort = 0

        if util.config.PETMethod == util.defines.PET_PRISTLEY_TAYLOR:
            if not os.path.exists(slrPath + os.sep + curForcingFilename) or not os.path.exists(
                                    hmdPath + os.sep + curForcingFilename):
                return 0
            prist = CPETInPristley(self.m_dTav, self.m_dHeight, curForcingFilename)
            dRLong = prist.NetLongWaveRadiationRHmd(self.m_slr, self.m_hmd)
            dRShort = prist.NetShortWaveRadiation(dalbedo, self.m_slr)
            self.m_dPET = prist.PETByPristley(1.26, 0)

        elif util.config.PETMethod == util.defines.PET_HARGREAVES:
            if not os.path.exists(slrPath + os.sep + curForcingFilename) or not os.path.exists(
                                    hmdPath + os.sep + curForcingFilename):
                return 0
                # har = CPETInHargreaves() TODO

        elif util.config.PETMethod == util.defines.PET_FAO_PENMAN_MONTEITH:
            if not os.path.exists(slrPath + os.sep + curForcingFilename) or not os.path.exists(
                                    hmdPath + os.sep + curForcingFilename) or not os.path.exists(
                                wndPath + os.sep + curForcingFilename):
                return 0
                # faopm = CPETInFAOPM() TODO

        elif util.config.PETMethod == util.defines.PET_DEBRUIN:
            if not os.path.exists(slrPath + os.sep + curForcingFilename) or not os.path.exists(
                                    hmdPath + os.sep + curForcingFilename):
                return 0
                # debruin = CPETInDeBruin() TODO

        else:
            if not os.path.exists(slrPath + os.sep + curForcingFilename) or not os.path.exists(
                                    hmdPath + os.sep + curForcingFilename):
                return 0
            pm = CPETInPM(self.m_dTav, self.m_dHeight, curForcingFilename)
            dRLong = pm.NetLongWaveRadiationRHmd(self.m_slr, self.m_hmd)
            dRShort = pm.NetShortWaveRadiation(dalbedo, self.m_slr)
            self.m_dPET = pm.PETInPMByRHmd(self.m_wnd, self.m_hmd, 0)

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格实际蒸散量                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +        由于Kojima法会出现比较大的空间不连续性，所以       +
    # +        目前只有互补相关理论法可以用。                    +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    # chen TODO
    def CalcAET(self, dalbedo, curForcingFilename):
        self.m_dAET = 0.
        if self.m_dPET == 0:
            return

        if util.config.AETMethod == util.defines.AET_BY_CROP_COEFFICIENTS:
            self.m_dAET = self.CompleAET(dalbedo)
        elif util.config.AETMethod == util.defines.AET_BY_COMPRELATIONSHIP:
            self.m_dAET = self.CompleAET(dalbedo)
        elif util.config.AETMethod == util.defines.AET_BY_COMPRELA_AND_KOJIMA:
            self.m_dAET = self.CompleAET(dalbedo)
        else:
            return

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        功能：互补相关理论法计算实际蒸散发                  +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    # chen TODO
    def CompleAET(self, dalbedo=0.23):
        print('chen TODO')

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        功能：计算干旱指数 - - AridIndex = (PET / pcp)    +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcAI(self):
        m_dAI = 0.

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +            功能：计算到达栅格的净雨量                     +
    # +        (降雨中扣除冠层截留, 填洼暂时忽略)                  +
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
    # +        (原理见博士论文：栅格水量平衡关系计算产流)           +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        总径流 ＝ 地表径流 ＋ 壤中流 ＋ 地下径流            +
    # +            1、计算地表径流                               +
    # +            2、计算壤中流                                +
    # +            3、计算地下径流                               +
    # +            4、计算土壤含水量变化                          +
    # +                                                        +
    # +        返回值：栅格产流类型；                            +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +        调用本函数前的主要输入参数：                        +
    # +            m_dNetRain - - 栅格净雨；                    +
    # +            m_dAET - - 实际蒸散量；                      +
    # +            m_dRIntensity - - 雨强；                     +
    # +            m_dFc - - 土壤稳定下渗率；                    +
    # +            m_dFp - - 时段土壤下渗率；                    +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcRunoffElement(self):
        pGridSoilInfo = SoilInfo()
        pGridSoilInfo.ReadSoilFile(GetSoilTypeName(int(self.m_Soil)) + '.sol')
        dthet = pGridSoilInfo.SoilWaterDeficitContent()
        dPE = self.m_dNetRain - self.m_dAET

        dIFc = self.m_dRIntensity - self.m_dFc
        dIFp = self.m_dRIntensity - self.m_dFp

        self.m_dTotalQ = 0.
        self.m_dSurfQ = 0.
        self.m_dLateralQ = 0.
        self.m_dBaseQ = 0.
        self.dBaseQ = 0.
        self.dLatQ = 0.

        if dthet < 0.:
            if dPE < 0.:
                if dIFc < 0.:  # 方案1：不产流
                    iret = 1
                else:  # 方案2：超渗产流
                    m_dSurfQ = dIFc * self.m_dHr
                    iret = 2
            else:
                if dIFc < 0.:  # 方案3：蓄满产流
                    self.m_dBaseQ = self.m_dFc * self.m_dHr
                    self.m_dSurfQ = dPE - self.m_dBaseQ
                    if self.m_dSurfQ < 0:
                        self.m_dSurfQ = dPE * util.config.SurfQOutFactor
                        self.m_dBaseQ = dPE * (1 - util.config.SurfQOutFactor)
                    iret = 3
                else:  # 方案4：超渗产流＋蓄满产流
                    self.m_dSurfQ = dIFc * self.m_dHr
                    self.m_dBaseQ = self.m_dFc * self.m_dHr
                    if self.m_dSurfQ + self.m_dBaseQ > dPE:
                        self.m_dBaseQ = dPE - self.m_dSurfQ
                        if self.m_dBaseQ < 0:
                            self.m_dSurfQ = dPE * util.config.SurfQOutFactor
                            self.m_dBaseQ = dPE * (1 - util.config.SurfQOutFactor)

                    else:
                        self.m_dLateralQ = dPE - self.m_dSurfQ - self.m_dBaseQ

                    iret = 4
        else:
            if dPE < dthet:
                if dIFp < 0.:  # 方案5：不产流
                    iret = 5
                else:  # 方案6：超渗产流
                    self.m_dSurfQ = dIFp * self.m_dHr
                    iret = 6
            else:
                if dIFp < 0.:  # 方案7：蓄满产流
                    self.m_dBaseQ = self.m_dFp * self.m_dHr
                    self.m_dSurfQ = dPE - dthet - self.m_dBaseQ
                    if self.m_dSurfQ < 0:
                        self.m_dSurfQ = (dPE - dthet) * util.config.SurfQOutFactor
                        self.m_dBaseQ = (dPE - dthet) * (1 - util.config.SurfQOutFactor)
                    iret = 7
                else:  # 方案8：超渗产流＋蓄满产流
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
                            self.m_dSurfQ = (dPE - dthet) * util.config.SurfQOutFactor
                            self.m_dBaseQ = (dPE - dthet) * (1 - util.config.SurfQOutFactor)

                            self.m_dLateralQ = 0.
                    else:
                        self.m_dLateralQ = self.m_dTotalQ - self.m_dSurfQ - self.m_dBaseQ
                    iret = 8

        pGridSoilInfo.SP_Sw += (dPE - self.m_dBaseQ - self.m_dSurfQ - self.m_dLateralQ)
        if pGridSoilInfo.SP_Sw > pGridSoilInfo.SP_Wp:
            if iret == 3 or iret == 4 or iret == 7 or iret == 8:
                dPerco = self.SWPercolation(pGridSoilInfo.SP_Sw, pGridSoilInfo.SP_Fc, self.m_dHr,
                                            pGridSoilInfo.TPercolation)
                if dPerco > 0:
                    pGridSoilInfo.SP_Sw -= dPerco
                    self.m_dBaseQ += dPerco

                    dLatQ = dPerco * util.config.LatQOutFactor
                    self.m_dLateralQ += dLatQ
                    pGridSoilInfo.SP_Sw -= dLatQ

            if pGridSoilInfo.SP_Sw > pGridSoilInfo.SP_Wp:
                dRecharge = self.SWRecharge(pGridSoilInfo.SP_Sw, self.m_dHr, self.m_dFp, pGridSoilInfo.SP_Init_F0)
                if dRecharge > pGridSoilInfo.SP_Sw - pGridSoilInfo.SP_Wp:
                    dRecharge = pGridSoilInfo.SP_Sw - pGridSoilInfo.SP_Wp
                self.dBaseQ = dRecharge * (1 - math.exp(-1 * (dRecharge / pGridSoilInfo.SP_Sw)))
                if self.dBaseQ < 0:
                    self.dBaseQ = 0.
                self.m_dBaseQ += self.dBaseQ
                pGridSoilInfo.SP_Sw -= self.dBaseQ
        else:
            pGridSoilInfo.SP_Sw = pGridSoilInfo.SP_Wp * 1.05

        if self.m_dBaseQ < 0:
            print("计算的地下径流分量为负" + "GridWaterBalance")
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
    # +                            栅格公用变量推算                      +
    # +                                                                +
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    #
    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                    功能：计算逐日LAI值                   +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyLai(self):
        dLai = 0.5
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(int(self.m_Veg)) + '.veg')

        if util.config.DLAICalcMethod == util.defines.DAILY_LAI_CAL_SINE:
            dmax = pGridVegInfo.LAIMX
            dmin = pGridVegInfo.LAIMN
            doffset = pGridVegInfo.doffset
            dLai = (dmax + dmin) / 2. - (dmax - dmin) * math.sin(2 * math.pi * (self.m_nDn - doffset) / 365.) / 2.
        elif util.config.DLAICalcMethod == util.defines.DAILY_LAI_CAL_LINEAR:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]
        elif util.config.DLAICalcMethod == util.defines.DAILY_LAI_BY_MONTH:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]
        else:
            dLai = pGridVegInfo.LAI[self.m_nMon - 1]

        return dLai

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格逐日Albedo                  +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyAlbedo(self):
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(int(self.m_Veg)) + '.veg')
        dAlb = 0.23
        dAlb = pGridVegInfo.Albedo[self.m_nMon - 1]

        return dAlb

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：计算栅格逐日盖度                     +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def DailyCoverDeg(self):
        pGridVegInfo = VegInfo()
        pGridVegInfo.ReadVegFile(GetVegTypeName(int(self.m_Veg)) + '.veg')
        dCovD = 0.
        dCovD = pGridVegInfo.CoverDeg[self.m_nMon - 1]

        return dCovD

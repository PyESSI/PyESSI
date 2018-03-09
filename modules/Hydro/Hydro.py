# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen

Class:
    CMuskCungeRoutePara
        functions:
            __init__(self)
    CMuskRouteFlux
        functions:
            __init__(self)
Functions:
    HillSideQVelocity(dUnitQ, slp, manning_n)
    ChannelQVelocity(dUnitQ, slp, manning_n)


"""


# load needed python modules
import math



class CMuskCungeRoutePara:
    def __init__(self):
        self.pGridNum = None
        self.pInGrid = None
        self.pOutGrid = None
        self.pGridRouteOrd = None
        self.pGridSlope = None
        self.pGridRLength = None
        self.pGridRiverOrd = None
        self.pRow = None
        self.pCol = None
        self.m_iRouteGridNum = 0


class CMuskRouteFlux:
    def __init__(self):
        self.pRoute = []
        self.pPreRoute = []


class RouteFlux:
    def __init__(self):
        self.dInFlux = 0.
        self.dOutFlux = 0.
        self.bCal = False


def HillSideQVelocity(dUnitQ, slp, manning_n):
    '''
    计算坡面流速
    :param dUnitQ:
    :param slp:
    :param manning_n:
    :return:
    '''
    dVflow = math.pow(dUnitQ, 0.4) * math.pow(slp, 0.3) / math.pow(manning_n, 0.6)
    return dVflow


def ChannelQVelocity(dUnitQ, slp, manning_n):
    '''
    计算河道流速
    :param dUnitQ:
    :param slp:
    :param manning_n:
    :return:
    '''
    dVflow = 0.489 * math.pow(dUnitQ, 0.25) * math.pow(slp, 0.375) / math.pow(manning_n, 0.75)
    return dVflow

class WaterYearType:
    def __init__(self):
        self.year = None
        self.wtype = None


# 全局变量
class gBase_GridLayer:
    def __init__(self):
        self.DEM = None
        self.Soil = None
        self.Veg = None


class gSoil_GridLayerPara:
    def __init__(self):
        self.SP_Sw = None
        self.SP_Wp = None
        self.SP_WFCS = None
        self.SP_Sat_K = None
        self.SP_Stable_Fc = None
        self.SP_Init_F0 = None
        self.Horton_K = None
        self.rootdepth = None
        self.SP_Fc = None
        self.SP_Sat = None
        self.TPercolation = None
        self.SP_Temp = None
        self.SP_Por = None
    
    
class gVeg_GridLayerPara:
    def __init__(self):
        self.Veg = None


class gClimate_GridLayer:
    def __init__(self):
        self.Pcp = None
        self.Pet = None
        self.Tav = None
        self.Tmx = None
        self.Tmn = None
        self.Wnd = None
        self.Hmd = None
        self.Slr = None


class gOut_GridLayer:
    def __init__(self):
        self.TotalQ = None
        self.SurfQ = None
        self.LateralQ = None
        self.BaseQ = None
        self.TempVal = None
        self.WaterYieldType = None
        self.SoilProfileWater = None
        self.SoilAvgWater = None
        self.RoutingQ = None
        self.NetPcp = None
        self.drateinf = None
        self.drintns = None
        self.dcumr = None
        self.dcuminf = None
        self.dexcum = None
        self.AI = None
        self.CI = None
        self.SnowWater = None
        self.CIDefict = None
        self.AET = None
        self.NetPcp = None
        

gBase_GridLayer = gBase_GridLayer()
gSoil_GridLayerPara = gSoil_GridLayerPara()
gVeg_GridLayerPara = gVeg_GridLayerPara()
gClimate_GridLayer = gClimate_GridLayer()
gOut_GridLayer = gOut_GridLayer()
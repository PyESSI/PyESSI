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
    dVflow = pow(dUnitQ, 0.4) * pow(slp, 0.3) / pow(manning_n, 0.6)
    return dVflow


def ChannelQVelocity(dUnitQ, slp, manning_n):
    '''
    计算河道流速
    :param dUnitQ:
    :param slp:
    :param manning_n:
    :return:
    '''
    dVflow = 0.489 * pow(dUnitQ, 0.25) * pow(slp, 0.375) / pow(manning_n, 0.75)
    return dVflow

class WaterYearType:
    def __init__(self):
        self.year = None
        self.wtype = None

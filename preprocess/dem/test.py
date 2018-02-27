# -*- coding: utf-8 -*-

from preprocess.dem.RunoffParam import *
from utils.config import *

if __name__ == "__main__":
    r = RunoffParam()
    # r.workDir = tauDir
    r.workDir = workSpace
    r.flowDir = flowDir
    r.streamOrd = streamOrder
    r.watershed = watershed
    r.dem = DEMFileName
    r.SetInfo()

    r.outX = 154
    r.outY = 579

    r.routingCode = routingCode
    r.RoutingGridCode()

    r.routingOdr = routingOdr
    r.routingSequ = routingSequ
    r.RoutingOptimalOrder()
    # r.RoutingOptimalSequ()

    # r.gridUD = gridUD
    # r.RoutingUDNode()

    r.subbasinsNum = 1
    r.gridFlowLength = gridFlowLength
    r.RouteLength()

    r.gridMeanSlp = gridMeanSlp
    r.RouteMeanSlp()

    r.routingTime = routingTime
    r.dKV = 2000
    r.RouteTime()

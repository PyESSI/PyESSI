# -*- coding: utf-8 -*-

from preprocess.dem.RunoffParam import *
from utils.config import *

if __name__ == "__main__":
    r = RunoffParam()
    r.workDir = tauDir
    r.flowDir = flowDir
    r.streamOrd = streamOrder
    r.dem = DEMFileName
    r.SetInfo()

    r.outX = 230
    r.outY = 72

    r.watershedMask = mask_to_ext
    # r.WatershedBound()

    r.routingCode = routingCode
    # r.RoutingGridCode()

    r.routingOdr = routingOdr
    r.routingSequ = routingSequ
    # r.RoutingOptimalOrder()
    # r.RoutingOptimalSequ()

    r.gridUD = gridUD
    # r.RoutingUDNode()

    r.subbasinsNum = 1
    r.gridFlowLength = gridFlowLength
    # r.RouteLength()

    r.gridMeanSlp = gridMeanSlp
    # r.RouteMeanSlp()

    r.routingTime = routingTime
    r.dKV = 0.5
    r.RouteTime()

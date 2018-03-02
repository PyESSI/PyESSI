# -*- coding: utf-8 -*-

from preprocess.dem.RunoffParam import *
from utils.config import *

if __name__ == "__main__":
    r = RunoffParam()
    r.workDir = workSpace + os.sep + "test"
    r.flowDir = flowDir
    r.streamOrd = streamOrder
    r.dem = DEMFileName
    r.outlet = modifiedOutlet
    r.SetInfo()

    # Get outlet cell X Y
    coord = GetCellXYByPoint(r.workDir + os.sep + r.flowDir, r.workDir + os.sep + r.outlet)
    r.outX = coord[0]
    r.outY = coord[1]

    r.routingCode = routingCode
    r.RoutingGridCode()

    r.routingOdr = routingOdr
    r.routingSequ = routingSequ
    r.RoutingOptimalOrder()
    r.RoutingOptimalSequ()

    r.gridUD = gridUD
    r.RoutingUDNode()

    r.subbasinsNum = 1
    r.gridFlowLength = gridFlowLength
    r.RouteLength()

    r.gridMeanSlp = gridMeanSlp
    r.RouteMeanSlp()

    r.routingTime = routingTime_GST
    r.dKV = GSKv
    r.RouteTime()

    r.routingTime = routingTime_GLT
    r.dKV = GLKv
    r.RouteTime()

    r.routingTime = routingTime_GBT
    r.dKV = GBKv
    r.RouteTime()

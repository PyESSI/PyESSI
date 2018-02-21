# -*- coding: utf-8 -*-

"""
Created 2018-02-13

@author: Huiran Gao

"""

from preprocess.dem.DEMStreamNet import *
from utils.config import *
from utils.utils import GetRasterStat


if __name__ == "__main__":
    d = DEMRiverNet()
    d.workDir = tauDir
    # d.workDir = workSpace
    d.dem = DEMFileName
    d.np = np
    d.defaultNodata = defaultNodata

    # Step 1 Remove Pits
    print("Fill DEM...")
    d.filledDem = filledDem
    d.Fill()

    # Step 2 Flow Directions
    print("Calculating D8 and Dinf flow direction...")
    d.slope = slope
    d.slopeDinf = slopeDinf
    d.flowDir = flowDir
    d.flowDirDinf = flowDirDinf
    d.FlowDirD8()
    d.FlowDirDinf()

    # Step 3 Contributing area
    print("D8 flow accumulation...")
    d.acc = acc
    d.FlowAccD8()

    # Step 4 Grid net
    print("Generating stream grid net...")
    d.flowPath = flowPath
    d.tLenFlowPath = tLenFlowPath
    d.streamOrder = streamOrder
    d.GridNet()

    # Step 5 Stream skeleton
    print("Generating stream skeleton...")
    d.streamSkeleton = streamSkeleton
    d.StreamSkeleton()

    # Step 6 Stream delineation
    print("Stream delineation initially...")
    d.outlet = outlet
    d.FlowAccD8()
    d.modifiedOutlet = modifiedOutlet
    d.streamRaster = streamRaster
    if threshold != 0:
        d.StreamRaster()
    else:
        accD8 = d.workDir + os.sep + d.acc
        maxAccum, minAccum, meanAccum, STDAccum = GetRasterStat(accD8)
        d.threshold = meanAccum
        print(d.threshold)
        d.StreamRaster()

    d.MoveOutlet()

    # d.threshold = threshold
    # if d.threshold == 0:
    #     print("Drop analysis to select optimal threshold...")
    #     minthresh = 10
    #     maxthresh = 500
    #     numthresh = 10
    #     logspace = 'true'
    #     drpfile = 'drp.txt'
    #     d.DropAnalysis(drpfile, minthresh ,maxthresh, numthresh, logspace)
    #     drpf = open(drpfile, "r")
    #     tempContents = drpf.read()
    #     beg, thres = tempContents.rsplit(' ', 1)
    #     d.threshold = float(thres)
    #     print("Optimal threshold: %f" % float(thres))
    #     drpf.close()

    # Step 7 Stream Network
    print("Generating stream net...")
    d.chNetwork = chNetwork
    d.chCoord = chCoord
    d.streamNet = streamNet
    d.subbasin = subbasin
    d.StreamNet()











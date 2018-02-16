# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:


"""

#pyESSI Project Setup
#[ProjectSetup]
workSpace = r'D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM'
tauDir = r'D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM\TauDEM_test'
startTime = 19960101
endTime = 20001231

#pyESSI GridIO File
#[GridIO]
# DEMFileName = 'YLXDem240.tif'
DEMFileName = 'dem.tif'
LULCFileName = 'YLXLulc240.tif'
SoilFileName = 'YLXSoil240.tif'

#PyESSI Model Running Parameters
#[RunPara]
PETMethod = 4
AETMethod = 2
InterpMethod = 1
AIMethod = 1
DLAICalcMethod = 3
RunoffSimuType = 2
SurfRouteMethod = 1
LatRouteMethod = 1
BaseRouteMethod = 1
RiverRouteMethod = 1
InfilCurveType = 1

#PyESSI Model Input Parameters
#[InputPara]
GSKv = 4000.00
GLKv = 1500.00
GBKv = 1200.00
GRKv = 0.00
LowWaterSurfQLoss = 22.50
MidWaterSurfQLoss = 24.00
HighWaterSurfQLoss = 48.00
LatQLoss = 15.00
BaseQLoss = 13.50
RiverQLoss = 0.00
RiverProType = 2
RiverProWidth = 20.00
HillProType = 4
HillProWidth = 240.00
SMCTimeWeight = -0.40
SMCGridRTravelTime = 2.80
LMCTimeWeight = 0.10
LMCGridRTravelTime = 10.00
BMCTimeWeight = -0.60
BMCGridRTravelTime = 4.00
SurfQLinearFactor = 1.00
SurfQOutFactor = 0.90
LatQOutFactor = 0.50
DailyMeanPcpTime = 2.00
SnowTemperature = 1.00
DDF = 0.40
DeepBaseQ = 10.00

#PyESSI Model MidGridOut Parameters
#[MidGridOut]
strOutBDate = 19960101
strOutEDate = 20001231
iPcp = 0
iTempMax = 0
iTempMin = 0
iTempMean = 0
iSlr = 0
iHmd = 0
iWnd = 0
iPET = 0
iAET = 0
iCI = 0
iSnowWater = 0
iAI = 0
iRouteOut = 0
iSurfQ = 0
iLatQ = 0
iBaseQ = 0
iInfilRate = 0
iWaterYieldType = 0
iProfileSoilWater = 0
iAvgSoilWater = 0


#[PREPROCESS PARAMETERS]
isTauDEMD8 = True
CPP_PROGRAM_DIR = None
MPIEXEC_DIR = None
D8AccThreshold = 1000
threshold = 0   # threshold for stream extraction from D8-flow accumulation weighted Peuker-Douglas stream sources
                # if threshold is 0, then Drop Analysis is used to select the optimal value.
np = 4
D8DownMethod = "Surface"
dorm_hr = -1.
T_base = 0.
imperviousPercInUrbanCell = 0.3
default_reach_depth = 5.
defaultLanduse = 33
defaultNodata = -9999.

## Conventional Spatial Raster Data File Names
filledDem = "tauDemFilled.tif"
flowDir = "tauD8FlowDir.tif"
slope = "tauSlope.tif"
acc = "tauD8Acc.tif"
streamRaster = "tauStreamRaster.tif"
outlet = "outlet.shp"

flowDirDinf = "flowDirDinfTau.tif"
# dirCodeDinf = "dirCodeDinfTau.tif"
# weightDinf = "weightDinfTau.tif"
slopeDinf = "slopeDinfTau.tif"
cellLat = "cellLatOrg.tif"
daylMin = "dayLenMinOrg.tif"
dormhr = "dormhrOrg.tif"

modifiedOutlet = "outletM.shp"
streamSkeleton = "streamSkeleton.tif"
flowPath = "flowPath.tif"
tLenFlowPath = "tlenFlowPath.tif"
streamOrder = "tauStreamOrder.tif"
chNetwork = "chNetwork.txt"
chCoord = "chCoord.txt"
streamNet = "streamNet.shp"
subbasin = "tauSubbasin.tif"
mask_to_ext = "mask.tif"
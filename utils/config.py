# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Functions:


"""

#pyESSI Project Setup
#[ProjectSetup]
workSpace = r'D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM'
mpiexeDir = r'"D:\Program Files\Microsoft MPI\Bin"'
startTime = 19960101
endTime = 20001231

#pyESSI GridIO File
#[GridIO]
DEMFileName = 'YLXDem240.tif'
# DEMFileName = 'dem.tif'
LULCFileName = 'YLXLulc240.tif'
SoilFileName = 'YLXSoil240.tif'
outlet = "outlet.shp"

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
demName = DEMFileName.split(".")[0]
filledDem = demName + "_fip.tif"                # Fill pits
flowDir = demName + "_fld.tif"                  # Flow direction with D8
flowDirDinf = demName + "_fdd.tif"              # Flow direction with Dinf
slope = demName + "_slp.tif"                    # Slope
slopeDinf = demName + "_spd.tif"                # Slope with Dinf
acc = demName + "_acu.tif"                      # Accumulation
streamRaster = demName + "_snk.tif"             # Stream network
watershed = demName + "_wby.tif"                # Watershed boundary
modifiedOutlet = "outletM.shp"                  # Nodified outlet shp
streamSkeleton = demName + "_stk.tif"           # Stream skeleton
flowPath = demName + "_mln.tif"                 # Maximum flow length
tLenFlowPath = demName + "_tln.tif"             # Totle length of flow
streamOrder = demName + "_sor.tif"              # Strahler order
chNetwork = "chNetwork.txt"                     # Network txt
chCoord = "chCoord.txt"                         # Coord txt
streamNet = demName + "streamNet.shp"           # Stream net shp
subbasin = demName + "_sws.tif"                 # Sub watershed
routingCode = demName + "_rtc.tif"              # Routing code
routingSequ = demName + "_ros.tif"              # Routing Optional Sequence
routingOdr = demName + "_ror.tif"               # Routing Optional Rank
gridUD = demName + "_gud.txt"                   # Grid upslope and downslope
gridFlowLength = demName + "_grl.tif"           # Grid river length
gridMeanSlp = demName + "_grs.tif"              # Grid river slope
routingTime_GST = demName + "_gst.tif"          # Grid surface runoff route Time
routingTime_GLT = demName + "_glt.tif"          # Grid lateral route time
routingTime_GBT = demName + "_gbt.tif"          # Grid base route Time
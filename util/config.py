# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen
         Huiran Gao

Functions:


"""

#pyESSI Project Setup
#[ProjectSetup]
workSpace = r'D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM'
# workSpace = r'D:\pyESSITest\DCBAM'
mpiexeDir = r'"C:\Program Files\Microsoft MPI\Bin"'
exeDir = None
startTime = '19960101'  # 模拟起始日期
endTime = '20001231'  # 模拟结束日期

# pyESSI GridIO File
# [GridIO]
DEMFileName = 'YLXDem240.tif'  # 原始DEM文件名
# DEMFileName = 'dem.tif'
LULCFileName = 'YLXLulc240.tif'  # LULC文件名
SoilFileName = 'YLXSoil240.tif'  # Soil文件名
outlet = "outlet.shp"  # 出水口shpfile

# PyESSI Model Running Parameters
# [RunPara]
PETMethod = 4  # 潜在蒸散发计算方法
AETMethod = 2  # 实际蒸散发计算方法
InterpMethod = 1  # 空间插值离散方法
AIMethod = 1  # 干旱指数计算方法
DLAICalcMethod = 3  # 逐日LAI计算方法
RunoffSimuType = 2  # 降雨径流过程计算类型
SurfRouteMethod = 1  # 地表径流汇流演算方法
LatRouteMethod = 1  # 壤中径流汇流演算方法
BaseRouteMethod = 1  # 地下径流汇流演算方法
RiverRouteMethod = 1  # 河道汇流演算方法
InfilCurveType = 1  # 下渗曲线类型

# PyESSI Model Input Parameters
# [InputPara]
GSKv = 4000.00  # 地表径流滞时演算速度系数
GLKv = 1500.00  # 壤中径流滞时演算速度系数
GBKv = 1200.00  # 地下径流滞时演算速度系数
GRKv = 0.00  # 河道径流滞时演算速度系数
LowWaterSurfQLoss = 22.50  # 枯水期地表径流损失系数
MidWaterSurfQLoss = 24.00  # 平水期地表径流损失系数
HighWaterSurfQLoss = 48.00  # 丰水期地表径流损失系数
LatQLoss = 15.00  # 壤中径流传输损失系数
BaseQLoss = 13.50  # 地下径流传输损失系数
RiverQLoss = 0.00  # 河道径流传输损失系数
RiverProType = 2  # 栅格河道断面类型
RiverProWidth = 20.00  # 栅格河道断面宽度
HillProType = 4  # 坡面河道断面类型
HillProWidth = 240.00  # 坡面河道断面宽度
SMCTimeWeight = -0.40  # 地表汇流时间差分权重
SMCGridRTravelTime = 2.80  # 地表汇流传播时间
LMCTimeWeight = 0.10  # 壤中汇流时间差分权重
LMCGridRTravelTime = 10.00  # 壤中汇流传播时间
BMCTimeWeight = -0.60  # 地下汇流时间差分权重
BMCGridRTravelTime = 4.00  # 地下汇流传播时间
SurfQLinearFactor = 1.00  # 地表径流线性调节因子
SurfQOutFactor = 0.90  # 地表径流出流系数
LatQOutFactor = 0.50  # 壤中径流出流系数
DailyMeanPcpTime = 2.00  # 日平均降雨时间长度
SnowTemperature = 1.00  # 降雪临界温度
DDF = 0.40  # 度－日系数
DeepBaseQ = 10.00  # 深层地下基流调节量

# PyESSI Forcing Parameters
# [Forcing]
pcpdata = 1  # 降雨量数据
slrdata = 0  # 太阳辐射数据
hmddata = 0  # 相对湿度数据
tmpmxdata = 0  # 最高气温数据
tmpmndata = 0  # 最低气温数据
tmpmeandata = 0  # 平均气温数据
wnddata = 0  # 风速数据
petdata = 1  # 潜在蒸散发数据

# PyESSI Model MidGridOut Parameters
# [MidGridOut]
strOutBDate = '19960101'  # 中间结果输出起始日期
strOutEDate = '20001231'  # 中间结果输出结束日期
iPcp = 0  # 降雨量
iTempMax = 0  # 最高气温
iTempMin = 0  # 最低气温
iTempMean = 0  # 平均气温
iSlr = 0  # 太阳辐射
iHmd = 0  # 相对湿度
iWnd = 0  # 平均风速
iPET = 0  # 潜在蒸散量
iAET = 1  # 实际蒸散量
iCI = 0  # 冠层截留
iSnowWater = 0  # 雪水当量
iAI = 0  # 干旱指数
iRouteOut = 0  # 栅格汇流演算结果
iSurfQ = 1  # 时段地表径流
iLatQ = 0  # 时段壤中径流
iBaseQ = 0  # 时段地下径流
iInfilRate = 0  # 时段土壤下渗率
iWaterYieldType = 1  # 栅格产流类型
iProfileSoilWater = 0  # 土层剖面含水量
iAvgSoilWater = 0  # 土层平均含水量

# [PREPROCESS PARAMETERS]
D8AccThreshold = 1000
threshold = 0  # threshold for stream extraction from D8-flow accumulation weighted Peuker-Douglas stream sources
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
filledDem = demName + "_fip.tif"  # Fill pits
flowDir = demName + "_fld.tif"  # Flow direction with D8
flowDirDinf = demName + "_fdd.tif"  # Flow direction with Dinf
slope = demName + "_slp.tif"  # Slope
slopeDinf = demName + "_spd.tif"  # Slope with Dinf
acc = demName + "_acu.tif"  # Accumulation
streamRaster = demName + "_snk.tif"  # Stream network
watershed = demName + "_wby.tif"  # Watershed boundary
modifiedOutlet = "outletM.shp"  # Modified outlet shp
streamSkeleton = demName + "_stk.tif"  # Stream skeleton
flowPath = demName + "_mln.tif"  # Maximum flow length
tLenFlowPath = demName + "_tln.tif"  # Totle length of flow
streamOrder = demName + "_sor.tif"  # Strahler order
chNetwork = "chNetwork.txt"  # Network txt
chCoord = "chCoord.txt"  # Coord txt
streamNet = demName + "streamNet.shp"  # Stream net shp
subbasin = demName + "_sws.tif"  # Sub watershed
routingCode = demName + "_rtc.tif"  # Routing code
routingSequ = demName + "_ros.tif"  # Routing Optional Sequence
routingOdr = demName + "_ror.tif"  # Routing Optional Rank
gridUD = demName + "_gud.txt"  # Grid upslope and downslope
gridFlowLength = demName + "_grl.tif"  # Grid river length
gridMeanSlp = demName + "_grs.tif"  # Grid river slope
routingTime_GST = demName + "_gst.tif"  # Grid surface runoff route Time
routingTime_GLT = demName + "_glt.tif"  # Grid lateral route time
routingTime_GBT = demName + "_gbt.tif"  # Grid base route Time
MuskCoeffFile = "muskingum_coeff.txt"  # muskingum coef file
WaterYearTypeFile = "WaterYearType.txt" #Water Year Type
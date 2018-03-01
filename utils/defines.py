# -*- coding: utf-8 -*-
"""
Created Feb 2018

@author: Hao Chen
<<<<<<< HEAD
         Huiran Gao

Functions:
    定义模型方法、参数识别值
    定义常数
=======

Functions:
    定义模型方法、参数识别值
>>>>>>> upstream/master

"""

# 最大植被、土壤分层数量、类型数量
MAX_SOIL_LAYERS = 10
MAX_VEG_TYPES = 300
MAX_SOIL_TYPES = 300

# 逐日LAI计算方法
DAILY_LAI_CAL_SINE = 1  # 正弦函数法
DAILY_LAI_CAL_LINEAR = 2  # 线性插值法
DAILY_LAI_BY_MONTH = 3  # 用月平均值代替逐日值

# 空间离散计算方法
SPATIAL_IDW_METHOD = 1  # inversed distance weighing method
SPATIAL_NEARIST_METHOD = 2  # Nearist Neighbour interpose method
SPATIAL_THIESSEN_METHOD = 3  # Thissen method
SPATIAL_PRISM_METHOD = 4  # PRISM	method
SPATIAL_GIDW_METHOD = 5  # Gradient inversed distance squared method

# 潜在蒸散发计算方法
PET_PENMAN_MONTEITH = 1  # Penman-Monteith Method;
PET_PRISTLEY_TAYLOR = 2  # Pristley Taylor Method;
PET_HARGREAVES = 3  # Hargreaves Method;
PET_REAL = 4  # PET read from real observed data
PET_FAO_PENMAN_MONTEITH = 5  # FAO Penman-Monteith Method;
PET_DEBRUIN = 6  # Debruin Method

# 实际蒸散发计算方法
AET_BY_CROP_COEFFICIENTS = 1  # 利用作物系数法求实际蒸散发
AET_BY_COMPRELATIONSHIP = 2  # 利用互补相关理论求实际蒸散发
AET_BY_COMPRELA_AND_KOJIMA = 3  # 利用互补相关理论+Kojima法求实际蒸散发

# 干旱指数计算方法
AI_BY_SSWC = 1  # Surface Soil Water Content法
AI_BY_CWSI = 2  # Crop Water Shortage Index法

# 降雨～径流过程模拟类型
STORM_RUNOFF_SIMULATION = 1  # 暴雨径流过程
LONGTERM_RUNOFF_SIMULATION = 2  # 长时段降雨径流过程

# 下渗曲线类型
INFILTRATION_HORTON = 1  # 霍顿下渗曲线
INFILTRATION_GREEN_AMPT = 2  # 格林－安普特下渗曲线
INFILTRATION_PHILIP = 3  # 菲利普下渗曲线

# 水力学计算河道类型
M_RIVER_SECTION_TRIANGLE = 1  # 曼宁 -- 三角形河道断面
M_RIVER_SECTION_RECTANGLE = 2  # 曼宁 -- 宽浅矩形河道断面
M_RIVER_SECTION_PARABOLA = 3  # 曼宁 -- 宽浅抛物线形河道断面
M_RIVER_SECTION_HILLSIDE = 4  # 曼宁 -- 坡地（用于坡面运动波汇流）

C_RIVER_SECTION_TRIANGLE = 5  # 谢才 -- 三角形河道断面
C_RIVER_SECTION_RECTANGLE = 6  # 谢才 -- 宽浅矩形河道断面
C_RIVER_SECTION_PARABOLA = 7  # 谢才 -- 宽浅抛物线形河道断面
C_RIVER_SECTION_HILLSIDE = 8  # 谢才 -- 坡地（用于坡面运动波汇流）

# 产流分水源类型
RUNOFF_ELEMENT_SURFQ = 1  # 地表径流
RUNOFF_ELEMENT_LATERALQ = 2  # 壤中流
RUNOFF_ELEMENT_BASEQ = 3  # 地下径流
RUNOFF_ELEMENT_RIVERQ = 4  # 河道水流

# 汇流方案
ROUTE_MUSK_CONGE = 0  # 马斯京根-康吉法
ROUTE_PURE_LAG = 1  # 滞时演算法
ROUTE_MUSKINGUM_COMBINE_FIRST = 2  # 马斯京根法－先合后演
ROUTE_MUSKINGUM_ROUTE_FIRST = 3  # 马斯京根法－先演后合

# 水量年份
WATER_LOW_YEAR = 1  # 枯水年
WATER_MID_YEAR = 2  # 平水年
WATER_HIGH_YEAR = 3  # 丰水年

<<<<<<< HEAD
# 常数
PI = 3.141592654
I0 = 4.921
AV = 0.2618
RAD = 57.29578
STEF_BOLTZ = 4.903e-9

=======
>>>>>>> upstream/master


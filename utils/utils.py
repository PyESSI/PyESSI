#coding=utf-8
## @Utility functions
#
#
import os,math,datetime,time
from osgeo import gdal,ogr,osr,gdalconst
from gdalconst import *
import shutil
import geojson
import xlrd
import numpy
import math

####  Climate Utility Functions  ####
def IsLeapYear(year):
    if( (year%4 == 0 and year%100 != 0) or (year%400 == 0)):
        return True
    else:
        return False

def GetDayNumber(year, month):
    if month in [1,3,5,7,8,10,12]:
        return 31
    elif month in [4,6,9,11]:
        return 30
    elif IsLeapYear(year):
        return 29
    else:
        return 28

## Solar Radiation Calculation
#  @param doy day of year
#  @param n   sunshine duration
#  @param lat latitude of sites
#  invoke   Rs(doy, n, lat)
# day of year
def doy(dt):
    sec = time.mktime(dt.timetuple())
    t = time.localtime(sec)
    return t.tm_yday

#earth-sun distance 
def dr(doy):
    return 1 + 0.033*math.cos(2*math.pi*doy/365)

#declination
def dec(doy):
    return 0.409*math.sin(2*math.pi*doy/365 - 1.39)

#sunset hour angle
def ws(lat, dec):
    x = 1 - math.pow(math.tan(lat), 2)*math.pow(math.tan(dec), 2)
    if x < 0:
        x = 0.00001
    #print x
    return 0.5*math.pi - math.atan(-math.tan(lat)*math.tan(dec)/math.sqrt(x))

#solar radiation
def Rs(doy, n, lat):
    """n is sunshine duration"""
    lat = lat * math.pi / 180.
    a = 0.25
    b = 0.5
    d = dec(doy)
    w = ws(lat, d)
    N = 24*w/math.pi
    #Extraterrestrial radiation for daily periods
    ra = (24*60*0.082*dr(doy)/math.pi)*(w*math.sin(lat)*math.sin(d) + math.cos(lat)*math.cos(d)*math.sin(w))
    return (a + b*n/N)*ra


####  Spatial Utility Functions  ####

DELTA = 0.000001

def FloatEqual(a, b):
    return abs(a - b) < DELTA

class Raster:
    def __init__(self, nRows, nCols, data, noDataValue=None, geotransform=None, srs=None):
        self.nRows = nRows
        self.nCols = nCols
        self.data = data
        self.noDataValue = noDataValue
        self.geotrans = geotransform
        self.srs = srs
        
        self.dx = geotransform[1]
        self.xMin = geotransform[0]
        self.xMax = geotransform[0] + nCols*geotransform[1]
        self.yMax = geotransform[3]
        self.yMin = geotransform[3] + nRows*geotransform[5]

def ReadRaster(rasterFile):
    ds = gdal.Open(rasterFile)
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    xsize = band.XSize
    ysize = band.YSize
    noDataValue = band.GetNoDataValue()
    geotrans = ds.GetGeoTransform()
    
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    #print srs.ExportToProj4()
    if noDataValue is None:
        noDataValue = -9999
    return Raster(ysize, xsize, data, noDataValue, geotrans, srs) 

def CopyShpFile(shpFile, dstFile):
    #copy the reach file to new file
    RemoveShpFile(dstFile)
    extlist = ['.shp', '.dbf', '.shx', '.prj']
    prefix = os.path.splitext(shpFile)[0]
    dstPrefix = os.path.splitext(dstFile)[0]
    for ext in extlist:
        src = prefix + ext
        if os.path.exists(src):
            dst = dstPrefix + ext
            shutil.copy(src, dst)
    
def RemoveShpFile(shpFile):
    extlist = ['.shp', '.dbf', '.shx', '.prj']
    prefix = os.path.splitext(shpFile)[0]
    for ext in extlist:
        filename = prefix + ext
        if os.path.exists(filename):
            os.remove(filename)

def NextDay(date):
    year = date.year
    mon = date.month
    day = date.day
    day = day + 1
    if day > GetDayNumber(year, mon):
        day = 1
        mon = mon + 1
    if mon > 12:
        mon = 1
        year = year + 1
    return datetime.datetime(year, mon, day)

def NextHalfDay(date):
    year = date.year
    mon = date.month
    day = date.day
    h = date.hour
    h = h + 12
    if h >= 24:
        h = h - 24
        day = day + 1
    if day > GetDayNumber(year, mon):
        day = 1
        mon = mon + 1
    if mon > 12:
        mon = 1
        year = year + 1
    #print year, mon, day, h
    return datetime.datetime(year, mon, day, h)


def LastHalfDay(date):
    year = date.year
    mon = date.month
    day = date.day
    h = date.hour
    h = h - 12
    if h < 0:
        h = h + 24
        day = day - 1
    
    if day < 1:
        if mon == 1:
            year = year - 1
            mon = 12
            day = 31
        else:
            mon = mon - 1
            day = GetDayNumber(year, mon)
            
    return datetime.datetime(year, mon, day, h)


def IsLeapYear(year):
    if( (year%4 == 0 and year%100 != 0) or (year%400 == 0)):
        return True
    else:
        return False

def GetDayNumber(year, month):
    if month in [1,3,5,7,8,10,12]:
        return 31
    elif month in [4,6,9,11]:
        return 30
    elif IsLeapYear(year):
        return 29
    else:
        return 28

def GetNumberList(s):
    a = []
    iCursor = 0
    for i in range(len(s)):
        if not s[i].isdigit():
            if(s[iCursor:i].isdigit()):
                a.append(int(s[iCursor:i]))
            iCursor = i + 1
    if s[iCursor:].isdigit():
        a.append(int(s[iCursor:]))
    return a


def isNumericValue(x):
    try:
        xx = float(x) + 10.
    except TypeError:
        return False
    except ValueError:
        return False
    except 'Exception':
        return False
    else:
        return True


def NashCoef(qObs, qSimu):
    n = len(qObs)
    ave = sum(qObs)/n
    a1 = 0
    a2 = 0
    for i in range(n):
        a1 = a1 + pow(qObs[i]-qSimu[i], 2)
        a2 = a2 + pow(qObs[i] - ave, 2)
    return 1 - a1/a2

def RMSE(list1, list2):
    n = len(list1)
    s = 0
    for i in range(n):
        s = s + pow(list1[i] - list2[i], 2)
    return math.sqrt(s/n)

def GetRasterStat(rasterFile):
    dataset = gdal.Open(rasterFile,GA_ReadOnly)
    if not dataset is None:
        band = dataset.GetRasterBand(1)
        max = band.GetMaximum()
        min = band.GetMinimum()
        if max is None or min is None:
            (min,max) = band.ComputeRasterMinMax(1)
        mean, std = band.ComputeBandStats()
        band = None
        dataset = None
        return (max,min,mean,std)
    dataset = None

def WriteAscFile(filename, data, xsize, ysize, geotransform, noDataValue):
    header = """NCOLS %d
NROWS %d
XLLCENTER %f
YLLCENTER %f
CELLSIZE %f
NODATA_VALUE %f
""" % (xsize, ysize, geotransform[0] + 0.5*geotransform[1], geotransform[3]-(ysize-0.5)*geotransform[1], geotransform[1], noDataValue)
        
    f = open(filename, 'w')
    f.write(header)
    for i in range(0, ysize):
        for j in range(0, xsize):
            f.write(str(data[i][j]) + "\t")
        f.write("\n")
    f.close() 
    
def WriteGTiffFile(filename, nRows, nCols, data, geotransform, srs, noDataValue, gdalType):
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    ds = driver.Create(filename, nCols, nRows, 1, gdalType)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(srs.ExportToWkt())
    ds.GetRasterBand(1).SetNoDataValue(noDataValue)
    ds.GetRasterBand(1).WriteArray(data)
    
    ds = None
    print("\tSave as: %s" % filename)

def WriteGTiffFileByMask(filename, data, mask, gdalType):
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    ds = driver.Create(filename, mask.nCols, mask.nRows, 1, gdalType)
    ds.SetGeoTransform(mask.geotrans)
    ds.SetProjection(mask.srs.ExportToWkt())
    ds.GetRasterBand(1).SetNoDataValue(mask.noDataValue)
    ds.GetRasterBand(1).WriteArray(data)
    
    ds = None
    

def MaskRaster(dir, maskFile, inputFile, outputFile, outputAsc=False, noDataValue=-9999):
    id = os.path.basename(maskFile) + "_" + os.path.basename(inputFile)
    configFile = "%s%smaskConfig_%s_%s.txt" % (dir, os.sep, id, str(time.time()))
    fMask = open(configFile, 'w')
    fMask.write(maskFile + "\n1\n")
    fMask.write("%s\t%d\t%s\n" % (inputFile, noDataValue, outputFile))
    fMask.close()
    asc = ""
    if outputAsc:
        asc = "-asc"
    # s = "%s/mask_rasters/build/mask_raster %s %s" % (config.CPP_PROGRAM_DIR, configFile, asc)
    # os.system(s)
    os.remove(configFile)


def StripStr(str):
    # @Function: Remove space(' ') and indent('\t') at the begin and end of the string
    oldStr = ''
    newStr = str
    while oldStr != newStr:
        oldStr = newStr
        newStr = oldStr.strip('\t')
        newStr = newStr.strip(' ')
    return newStr


def SplitStr(str, spliters=None):
    # @Function: Split string by spliter space(' ') and indent('\t') as default
    # spliters = [' ', '\t']
    # spliters = []
    # if spliter is not None:
    #     spliters.append(spliter)
    if spliters is None:
        spliters = [' ', '\t']
    destStrs = []
    srcStrs = [str]
    while True:
        oldDestStrs = srcStrs[:]
        for s in spliters:
            for srcS in srcStrs:
                tempStrs = srcS.split(s)
                for tempS in tempStrs:
                    tempS = StripStr(tempS)
                    if tempS != '':
                        destStrs.append(tempS)
            srcStrs = destStrs[:]
            destStrs = []
        if oldDestStrs == srcStrs:
            destStrs = srcStrs[:]
            break
    return destStrs


def createForld(forldPath):
    ## Create forld
    if not os.path.isdir(forldPath):
        os.makedirs(forldPath)


## Calculate Nash coefficient
def NashCoef(qObs, qSimu, obsNum=9999):
    n = len(qObs)
    ave = sum(qObs) / n
    a1 = 0
    a2 = 0
    for i in range(n):
        if qObs[i] != 0:
            a1 = a1 + pow(float(qObs[i]) - float(qSimu[i]), 2)
            a2 = a2 + pow(float(qObs[i]) - ave, 2)
    if a2 == 0:
        a2 = 1.e-6
    if obsNum > 1:
        return "%.3f" % round(1 - a1 / a2, 3)
    else:
        return "NAN"


## Calculate R2
def RSquare(qObs, qSimu, obsNum=9999):
    n = len(qObs)
    sim = []
    for k in range(n):
        sim.append(float(qSimu[k]))
    obsAvg = sum(qObs) / n
    predAvg = sum(sim) / n
    obsMinusAvgSq = 0
    predMinusAvgSq = 0
    obsPredMinusAvgs = 0
    for i in range(n):
        if qObs[i] != 0:
            obsMinusAvgSq = obsMinusAvgSq + pow((qObs[i] - obsAvg), 2)
            predMinusAvgSq = predMinusAvgSq + pow((sim[i] - predAvg), 2)
            obsPredMinusAvgs = obsPredMinusAvgs + (qObs[i] - obsAvg) * (sim[i] - predAvg)
    ## Calculate RSQUARE
    yy = (pow(obsMinusAvgSq, 0.5) * pow(predMinusAvgSq, 0.5))
    if yy == 0:
        yy = 1.e-6
    RSquare = round(pow((obsPredMinusAvgs / yy), 2), 3)
    if obsNum > 1:
        return "%.3f" % RSquare
    else:
        return "NAN"

def getFileList(dataDir, ftype):
    '''
    :param dataDir: 文件夹路径
    :param ftype: 数据文件后缀，(.*)
    :return: 文件全路径，文件名（不加后缀）
    '''
    fileFullPathList = []
    fileNameList = []
    filenameList = os.listdir(dataDir)
    for fn in filenameList:
        file_name, file_ext = os.path.splitext(fn)
        if file_ext == ftype:
            fileFullPathList.append(dataDir + os.sep + fn)
            fileNameList.append(file_name)
    return fileFullPathList, fileNameList



## DateTime
def getDayByDay(timeStart, timeEnd):
    oneday = datetime.timedelta(days=1)
    timeArr = [timeStart]
    while timeArr[len(timeArr) - 1] < timeEnd:
        tempday = timeArr[len(timeArr) - 1] + oneday
        timeArr.append(tempday)
    return timeArr


## DateTime
def GetDateArr_days(timeStart, timeEnd):
    TIME_Start = datetime.datetime.strptime(timeStart, "%Y-%m-%d")
    TIME_End = datetime.datetime.strptime(timeEnd, "%Y-%m-%d")
    dateArr = getDayByDay(TIME_Start, TIME_End)
    # print dateArr
    return dateArr


def GetDateArr(years):
    dateArr = []
    for y in years:
        dateArr.append(datetime.datetime.strptime(str(y), "%Y"))
    # print dateArr
    return dateArr


def ReadDatafromExcel(xlsfile, sheet_name, ytype, yindex, t_index=[]):
    bk = xlrd.open_workbook(xlsfile)
    y = []
    for sh in bk.sheets():
        # print len(sh.col_values(0))
        # print "Sheet:", sh.name
        if sh.name == sheet_name:
            # y = numpy.zeros((len(ytype), days_num))
            for j in range(len(ytype)):
                k = []
                # col_len = len(filter(lambda x: x != "", sh.col_values(j))) # 获取列的长度
                row_len = sh.nrows
                if j not in t_index:
                    for i in range(row_len - 1):
                        k.append(sh.cell(i + 1, yindex[j]).value)
                    y.append(k)
                else:
                    # 如果是时间字段，则读取为 datetime 类型
                    for i in range(row_len - 1):
                        k.append(xlrd.xldate.xldate_as_datetime(sh.cell(i + 1, yindex[j]).value, bk.datemode))
                    y.append(k)
    return y

def CalculateLocalVariance(arr, size_ft):
    '''
    计算局部方差
    :param arr:
    :param size_ft: 窗口大小
    :return:
    '''
    arr_lv = []
    for i in range(len(arr)):
        if i < size_ft:
            v = CalculateVariance(arr[i:i + size_ft])
            arr_lv.append(v)
        elif i > len(arr) - size_ft:
            v = CalculateVariance(arr[i - size_ft:i])
            arr_lv.append(v)
        else:
            v1 = CalculateVariance(arr[i:i + size_ft])
            v2 = CalculateVariance(arr[i - size_ft:i])
            arr_lv.append(numpy.min([v1, v2]))

    return arr_lv

def CalculateVariance(arr):
    '''
    计算方差
    :param arr: 输入数组
    :return: 数组arr的方差
    '''
    n = len(arr)
    mean = numpy.mean(arr)
    sum = 0
    for d in arr:
        sum += (d - mean) * (d - mean)
    variance = sum / n
    # print(variance)
    return variance


def CalculateRange(arr):
    '''
    计算极差
    :param arr:
    :return: 极差
    '''
    return numpy.max(arr) - numpy.min(arr)


def Normalize(arr):
    '''
    数值标准化至0-1之间
    :param arr:
    :return:
    '''
    d_max = numpy.max(arr)
    d_min = numpy.min(arr)
    arr_norm = []
    for i in range(len(arr)):
        arr_norm.append((arr[i] - d_min)/(d_max - d_min))
    return arr_norm


def getSRSPair(dataset):
    '''
    获得给定数据的投影参考系和地理参考系
    :param dataset: GDAL地理数据
    :return: 投影参考系和地理参考系
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs, geosrs


def geo2lonlat(dataset, x, y):
    '''
    将投影坐标转为经纬度坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param x: 投影坐标x
    :param y: 投影坐标y
    :return: 投影坐标(x, y)对应的经纬度坐标(lon, lat)
    '''
    prosrs, geosrs = getSRSPair(dataset)
    ct = osr.CoordinateTransformation(prosrs, geosrs)
    coords = ct.TransformPoint(x, y)
    return coords[:2]


def lonlat2geo(dataset, lon, lat):
    '''
    将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param lon: 地理坐标lon经度
    :param lat: 地理坐标lat纬度
    :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    prosrs, geosrs = getSRSPair(dataset)
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    coords = ct.TransformPoint(lon, lat)
    return coords[:2]

def imagexy2geo(dataset, row, col):
    '''
    根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
    :param dataset: GDAL地理数据
    :param row: 像素的行号
    :param col: 像素的列号
    :return: 行列号(row, col)对应的投影坐标或地理坐标(x, y)
    '''
    trans = dataset.GetGeoTransform()
    px = trans[0] + row * trans[1] + col * trans[2]
    py = trans[3] + row * trans[4] + col * trans[5]
    return px, py


def geo2imagexy(dataset, x, y):
    '''
    根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    :param dataset: GDAL地理数据
    :param x: 投影或地理坐标x
    :param y: 投影或地理坐标y
    :return: 影坐标或地理坐标(x, y)对应的影像图上行列号(row, col)
    '''
    trans = dataset.GetGeoTransform()
    a = numpy.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = numpy.array([x - trans[0], y - trans[3]])
    return numpy.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解



def imageTOvector(arr2D):
    '''
    二维数组转一维
    :param arr2D:
    :return:
    '''
    arr = []
    for i in range(len(arr2D)):
        for j in range(len(arr2D[i])):
            arr.append(arr2D[i][j])
    return arr

## Array process
def GreaterThan0(arr):
    '''
    Make all elements larger than 0
    :param arr:
    :return:
    '''
    arr_new = []
    for k in range(len(arr)):
        if arr[k] < 0:
            if k < 10:
                sum_v = []
                for v in arr[k:k + 10]:
                    if v > 0:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
            elif k > len(arr) - 10:
                sum_v = []
                for v in arr[k - 10:k]:
                    if v > 0:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
            else:
                sum_v = []
                for v in arr[k - 5:k + 5]:
                    if v > 0:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
        else:
            arr_new.append(arr[k])
    return arr_new


def RemoveInvalidVal(arr, valid_range):
    '''
    Remove invalid values by valid range
    :param arr:
    :param range_value:
    :return:
    '''

    arr_new = []
    for k in range(len(arr)):
        if arr[k] <= valid_range[0] or arr[k] >= valid_range[1]:
            if k < 6:
                sum_v = []
                for v in arr[k:k + 6]:
                    if v > valid_range[0] and v < valid_range[1]:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
            elif k > len(arr) - 6:
                sum_v = []
                for v in arr[k - 6:k]:
                    if v > valid_range[0] and v < valid_range[1]:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
            else:
                sum_v = []
                for v in arr[k - 3:k + 3]:
                    if v > valid_range[0] and v < valid_range[1]:
                        sum_v.append(v)
                if len(sum_v) > 0:
                    arr_new.append(numpy.mean(sum_v))
                else:
                    arr_new.append(arr[k])
        else:
            arr_new.append(arr[k])
    return arr_new


def Avg_arr2d(arr):
    '''
    求二维数组逐列均值
    :param arr: 2D array
    :return: array
    '''
    arr_avg = []
    for i in range(len(arr[0])):
        arr_avg.append(numpy.average([x[i] for x in arr]))
    return arr_avg

# if __name__ == "__main__":
#     print(Avg_arr2d([[1,2,3],[4,5,6]]))
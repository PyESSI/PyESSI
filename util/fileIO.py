# -*- coding: utf-8 -*-
"""
Created Dec 2017

@author: Hao Chen

Functions:
    class: Raster
    readRaster
    writeRaster

"""

# load needed python modules
import sys

try:
    from osgeo import gdal, ogr, osr, gdal_array, gdalconst
except:
    sys.exit('ERROR: cannot find GDAL.OGR modules')

# Enable GDAL/OGR exceptions
gdal.UseExceptions()


class Raster:
    def __init__(self, nRows, nCols, data, noDataValue=None, geoTransform=None, srs=None):
        self.nRows = nRows
        self.nCols = nCols
        self.data = data
        self.noDataValue = noDataValue
        self.geoTransform = geoTransform
        self.srs = srs

        ## GeoTransforms are lists of information used to geoReference an image
        ## From the GDAL documentation:
        # geoTransform[0] /* top left x */
        # geoTransform[1] /* w-e pixel resolution */
        # geoTransform[2] /* rotation, 0 if image is "north up" */
        # geoTransform[3] /* top left y */
        # geoTransform[4] /* rotation, 0 if image is "north up" */
        # geoTransform[5] /* n-s pixel resolution */


        self.xRes = geoTransform[1]
        self.yRes = geoTransform[5]
        self.xMin = geoTransform[0]
        self.xMax = self.xMin + nCols * self.xRes
        self.yMax = geoTransform[3]
        self.yMin = self.yMax + nRows * self.yRes


def readRaster(rasterFilename):
    ds = gdal.Open(rasterFilename)
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    cols = band.XSize
    rows = band.YSize
    noDataValue = band.GetNoDataValue()
    geoTrans = ds.GetGeoTransform()
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    if noDataValue is None:
        noDataValue = -9999
    return Raster(rows, cols, data, noDataValue, geoTrans, srs)


def writeRaster(filename, nRows, nCols, data, geoTransform, srs, noDataValue, gdalType):
    format = 'GTiff'
    driver = gdal.GetDriverByName(format)
    ds = driver.Create(filename, nCols, nRows, 1, gdalType)
    ds.SetGeoTransform(geoTransform)
    ds.SetProjection(srs.ExportToWkt())
    ds.GetRasterBand(1).SetNoDataValue(noDataValue)
    ds.GetRasterBand(1).WriteArray(data)
    ds = None
    return True


def GetCellXYByPoint(in_raster, in_shp, bright=False, bbottom=False):
    '''
    根据栅格中心坐标得到栅格的行列号
    :param in_raster: 流域范围栅格
    :param in_shp: 流域出水口矢量点
    :param bright:
    :param bbottom:
    :return:
    '''
    r = readRaster(in_raster)
    coords = GetShpPointCoords(in_shp)[0]

    dcol = (coords[0] - r.geoTransform[0]) / r.geoTransform[1]
    drow = (r.geoTransform[3] - coords[1]) / r.geoTransform[1]

    col = int(dcol + 0.5)
    row = int(drow + 0.5)

    if (bright):
        if ((dcol - int(dcol)) > 0.5):
            col = int(dcol) + 1

    if (bbottom):
        if ((drow - int(drow)) > 0.5):
            row = int(drow) + 1

    if (col < 0 or row < 0):
        return -1
    else:
        return row, col


def GetShpPointCoords(in_shp):
    '''
    获取矢量点的地理坐标
    :return:
    '''
    driver = ogr.GetDriverByName('ESRI Shapefile')
    ds = driver.Open(in_shp)
    if ds is None:
        raise Exception('Could not open %s!' % in_shp, ds)
    # 获取第0个图层
    layer0 = ds.GetLayerByIndex(0)
    feature = layer0.GetNextFeature()
    defn = layer0.GetLayerDefn()
    iFieldCount = defn.GetFieldCount()

    # 遍历图层中的要素
    coords = []
    for index in range(iFieldCount):
        if feature is not None:
            # 获取要素中的几何体
            geometry = feature.GetGeometryRef()
            coords.append([geometry.GetX(), geometry.GetY()])
    feature.Destroy()
    ds.Destroy()

    return coords


def GetRasterStat(rasterFile):
    dataset = gdal.Open(rasterFile, gdalconst.GA_ReadOnly)
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

# if __name__ == "__main__":
#     r = r"D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM\test\watershed.tif"
#     p = r"D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\DCBAM\test\outlet.shp"
#
#     print(GetCellXYByPoint(r, p))


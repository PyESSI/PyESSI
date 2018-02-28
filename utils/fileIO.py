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


#Enable GDAL/OGR exceptions
gdal.UseExceptions()


class Raster:
    def __init__(self, nRows, nCols, data, noDataValue = None, geoTransform = None, srs = None):
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
    ds =  driver.Create(filename, nCols, nRows, 1, gdalType)
    ds.SetGeoTransform(geoTransform)
    ds.SetProjection(srs.ExportToWkt())
    ds.GetRasterBand(1).SetNoDataValue(noDataValue)
    ds.GetRasterBand(1).WriteArray(data)
    ds = None
    return True





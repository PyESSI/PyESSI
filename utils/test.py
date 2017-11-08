#test scripts
#

import os, os.path
from utils.file_io import *
import numpy as np

raster_file = r'F:\00000000000000ESSI_srb\DEM\srbdem_projected\srb.tif'

sourceDem = ReadRaster(raster_file)

resultdata = np.zeros((sourceDem.nRows,sourceDem.nCols))

for row in range(sourceDem.nRows):
    for col in range(sourceDem.nCols):
        resultdata[row][col] = sourceDem.data[row][col]

WriteRaster(r'C:\Users\chenh\Desktop\test1.tif', sourceDem.nRows, sourceDem.nCols, resultdata, sourceDem.geotrans, sourceDem.srs, sourceDem.noDataValue, gdal.GDT_Float32)



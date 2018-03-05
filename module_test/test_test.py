
import os
import time
from util.config import *
from util.fileIO import *

s = time.time()
for i in range(10000):
    # curPcp = readRaster(workSpace + os.sep + 'test' + os.sep + 'YLXDem240.tif')
    curPcp = 0
e = time.time()

print(e - s)

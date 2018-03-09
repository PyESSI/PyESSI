# -*- coding: utf-8 -*-
from numba import jit
import numpy
import time

@jit(nopython=True)
def sum2d(arr):
    M, N = arr.shape
    r1 = 0
    r2 = 0
    for k in range(100):
        for i in range(M):
            for j in range(N):
                a = 1.0001
                b = 1
                r1 += a
                r2 += b

    return r1 / 100, r2 / 100

a = numpy.zeros((900, 600))
start_time = time.time()
r1, r2 = sum2d(a)
print(r1, r2)
end_time = time.time()
print (end_time - start_time)
# -*- coding: utf-8 -*-
from numba import jit
import numpy
import time

@jit(nopython=True)
def sum2d(arr):
    M, N = arr.shape
    result = 0.0
    for k in range(1000):
        for i in range(M):
            for j in range(N):
                a = 1
                b = a
                c = a + b
                result = c
    return result

a = numpy.zeros((900, 600))
start_time = time.time()
# for i in range(100):
sum2d(a)
end_time = time.time()
print (end_time - start_time)
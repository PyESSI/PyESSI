
import os
import time

import numpy
class A():
    def __init__(self):
        self.a = 1
        self.b = 1
        self.c = 1
        self.d = 1
        self.e = 1
        self.f = 1
        self.g = 1


s = time.time()
arr = []
for i in range(5):
        arr.append((i, A))
e = time.time()

ad = dict(arr)
print(ad[3].c)

print("time: %.3f" % (e - s))



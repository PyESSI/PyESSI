
import os
import time
import numpy

class A():
    pass


a = []
for i in range(2):
    for j in range(3):
        a.append(A)

# print(a)
arr = numpy.array(a)
arr = arr.reshape(2,3)
# arr = list(a[0])

print(arr)


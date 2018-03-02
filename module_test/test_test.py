class A():
    def __init__(self):
        self.x = 0
        self.y = 0

arr = []

for i in range(10):
    a = A()
    a.x = i
    arr.append(a)



print(arr[7].x)
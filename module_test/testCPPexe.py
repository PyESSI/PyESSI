
import subprocess

exePath = r"D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\CPP_Test\test\Debug\test.exe"
a = 1
b = 10
strCmd = "%s %d %d" % (exePath, a, b)
print(strCmd)

process = subprocess.Popen(strCmd, shell=False, stdout=subprocess.PIPE)

result = process.stdout.readlines()

print(result)


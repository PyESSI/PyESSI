
import subprocess

exePath = r"D:\GaohrWS\DoctorWorks\DoctorWork\PyESSI\CPP_Test\test\Debug\test.exe"
strCmd = "%s" % exePath
print(strCmd)

process = subprocess.Popen(strCmd, shell=False, stdout=subprocess.PIPE)

print(process.stdout.readlines())


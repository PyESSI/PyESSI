## PyESSI V1.0 Released
### Python in ESSI (Distributed Hydrological Model )
---
![Logo of ESSI](https://raw.githubusercontent.com/gaohr/MyImages/master/imgs/study/gaohr/ESSI/ESSI_ss.jpg "Logo of ESSI")

Developers:

+ Hao Chen & Huiran Gao


***Getting Start***<br>

**1.Python environment**<br>
------[Anaconda 3](https://www.anaconda.com/)<br>
------[GDAL for Python](https://pypi.python.org/pypi/GDAL/)<br> 
------[TauDEM](http://hydrology.usu.edu/taudem/taudem5/)<br>

**2.Project**<br>
Please refer DEMO data for details.<br>
~~~
+   /Demo
+   ------/DEM
+   ------/Forcing
+   ------/pcpdata
+   ------/------/petdata
+   ------/------/tmpmeandata
+   ------/------/tmpmxdata
+   ------/------/tmpmndata
+   ------/------/slrdata
+   ------/------/hmddata
+   ------/-----/wnddata
+   ------/LookupTable
+   ------/------/LulcType.txt
+   ------/------/soiltype.txt
+   ------/Output
+   ------/Soil
+   ------/------/*.sol
+   ------/Vegetation
+   ------/------/*.veg
~~~

**3.util/Config.py**<br>
+ Model parameters setup accordingly<br> 
including:<br> 
  + workSpace<br>
  + startTime<br>
  + endTime<br>
  + pyESSI GridIO File<br> 
  + PyESSI Model Running Parameters<br>
  + PyESSI Model Input Parameters<br> 
  + PyESSI Forcing Parameters<br> 
  + PyESSI Model MidGridOut Parameters<br> 

**4.RunPyESSI.py**<br>

<font color="#ff9900">Have fun！</font>


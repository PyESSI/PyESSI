## PyESSI V1.0 Released
### Python in ESSI (Distributed Hydrological Model )
---
![Logo of ESSI](https://raw.githubusercontent.com/gaohr/MyImages/master/imgs/study/gaohr/ESSI/ESSI_s.jpg "Logo of ESSI")

Developer:

+ Hao Chen & Huiran Gao


***Getting Start***<br>

**1.Python environment**<br>
------[Anaconda 3](https://www.anaconda.com/)<br>
------[GDAL for Python](https://pypi.python.org/pypi/GDAL/)<br> 
------[TauDEM](http://hydrology.usu.edu/taudem/taudem5/)<br>

**2.Project**<br>
Please refer DEMO data for details.<br>
~~~
+   ------DEM<br>
+   ------Forcing<br>
+   ------pcpdata<br>
+   ------|------petdata<br>
+   ------|------tmpmeandata<br>
+   ------|------tmpmxdata<br>
+   ------|------tmpmndata<br>
+   ------|------slrdata<br>
+   ------|------hmddata<br>
+   ------|------wnddata<br>
+   ------LookupTable<br>
+   ------|------LulcType.txt<br>
+   ------|------soiltype.txt<br>
+   ------Output<br>
+   ------Soil<br>
+   ------|------*.sol<br>
+   ------Vegetation<br>
+   ------|------*.veg<br>
~~~

**3.Config.py**<br>
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








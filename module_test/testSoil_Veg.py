# -*- coding: utf-8 -*-


from modules.Hydro.SoilPara import *
from modules.Hydro.VegetationPara import *
from modules.Hydro.HydroSimulate import CHydroSimulate

h = CHydroSimulate()
h.LoadLookupTable()
h.LoadSolVegFile()

veg1 = VegInfo(h.vegTypeName, h.vegFile)
veg1.ReadVegFile('PINE.veg')

print(veg1.Veg_Name)
print(veg1.LAIMX)
print(veg1.LAIMN)
print(veg1.doffset)
print(veg1.dManning_n)
print(veg1.LAI)
print(veg1.Albedo)
print(veg1.CoverDeg)


soil1 = SoilInfo(h.soilTypeName, h.solFile)
soil1.ReadSoilFile('HJCT.sol')
print(soil1.Soil_Name)
print(soil1.iLayer)
print(soil1.rootdepth)
print(soil1.albedo)
print(soil1.Horton_K)
print(soil1.InitSWP)
print(soil1.SL_ID)
print(soil1.SL_Z)
print(soil1.SL_BD)
print(soil1.SL_AWC)
print(soil1.SL_Sat_K)
print(soil1.SL_Stable_F)
print(soil1.SL_Org_C)
print(soil1.SL_Clay)
print(soil1.SL_Silt)
print(soil1.SL_Sand)
print(soil1.SL_Rock)
print(soil1.SL_Init_F)
print(soil1.SL_bFillOK)


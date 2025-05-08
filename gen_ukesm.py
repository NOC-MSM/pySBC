"""
Generate Surface Boundary conditions from UKESM output

-- under constuction 2025/05/08 --
"""

import xarray as xr
import iris

glosat_path = '/gws/nopw/j04/glosat/production/UKESM/raw/'
src_path = glosat_path + 'u-ck651/18500101T0000Z/'
print (src_path)
fn = src_path + "ck651a.p51850jan.pp"

cube = iris.load(fn)
print (cube)
ds = xr.Dataset.from_iris(cube)

print (ds)

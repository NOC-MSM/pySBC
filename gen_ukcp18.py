"""
Generate Surface Boundary conditions from UKCP18 output

-- under constuction 2026/05/29 --

TODO: merge with gen_ukesm.py - lots of duplication
"""

import xarray as xr
import iris
import numpy as np
import cf
from dask.diagnostics import ProgressBar
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import config

### ---- model specific choices ---- ###

case = "enuk_amm15_amm15-SMCa"
# map variable names
var_map = {
        "x_wind": "u10",
        "y_wind": "v10",
        "air_temperature": "t1500mm",
        "air_pressure_at_sea_level": "mslp",
        "surface_downwelling_longwave_flux_in_air": "msdwlwrf",
        "surface_downwelling_shortwave_flux_in_air": "msdwswrf",
        "snowfall_flux": "msr",
        "precipitation_flux": "mtpr",
        "specific_humidity": "sph"}

stash_codes = ["m01s03i237",
               "m01s16i222",
               "m01s03i209",
               "m01s03i210",
               "m01s03i236",
               "m01s02i207",
               "m01s01i235",
               "m01s05i215",
               "m01s05i216"]

def format_coords(da):
    """
    Add netCDF attributes and format coordinates

    +++
    DUPLICATE of gen_era5 needs removing
    +++

    """

    # mesh lat and lon
    mlon, mlat = np.meshgrid(da.grid_longitude, da.grid_latitude)
  
    # assign X/Y as indexes
    da = da.drop(['grid_longitude','grid_latitude'])
    da = da.rename({'grid_longitude':'x','grid_latitude':'y'})
    da = da.assign_coords({'longitude':(["y","x"], mlon),
                           'latitude':(["y","x"], mlat)})

    return da

def flood_fill_sbc(da, is_wind=False):
    """
    flood fill sbc based on land sea mask
    """

    # get LSM derived from UKESM domain_cfg - see gen_land_sea_mask()
    lsm_fn = xr.open_dataset(
                       "/gws/ssde/j25b/jmmp/sberthou/enuk_landsea_mask.nc")
    lsm = lsm_fn.land_binary_mask

    lsm = format_coords(lsm)

    # interpolate from u/v grid to t grid
    # TODO: it might be better to map the LSM to u/v grid
    if is_wind:
        da = interpolate(da, lsm, name=da.name, method="linear")

    # mask da
    da_msk = da.where(lsm == 0)

    # bug with "where" means lon coords are dropped
    da_msk = da_msk.assign_coords(longitude=da.longitude)

    da_filled= interpolate(da_msk, da_msk, name=da.name, method="nearest")

    return da_filled

def gen_ukcp18(var_list, y0=1850, y1=1851):
    
    year_range = np.arange(y0,y1)
    
    for j, key in enumerate(var_list.keys()):

        print ("CODE", key)
        for yyyy in year_range:
            print ("year: ", yyyy)
            
            da_acum, ds1_acum = [], []
            for month in range(1,13):
                print ("month: ", month)
                for day in range(1,31):
        
                    print ("day: ", day)
                    
                    mm = str(month).zfill(2)
                    dd = str(day).zfill(2)
                    fn = config.raw_path + f'{case}.p6{yyyy}{mm}{dd}.pp'
                    #b_grid_codes = ["m01s03i225","m01s03i226"]
                    b_grid_codes = ["m01s03i209","m01s03i210"]
                    if key in ["x_wind","y_wind"]:
                        cubes = iris.load(fn, key)
                        for cube in cubes:
                                if cube.attributes["STASH"] in b_grid_codes:
                                    break
                    else:
                        cube = iris.load_cube(fn, key)
                    with ProgressBar():
                        da = xr.DataArray.from_iris(cube)

                    print ('')
                    print ("loaded name ", da.name)
                    print ('')

                    da = format_coords(da)

                    da_24h = []
                    for t, da_h in da.groupby("time"):
                        print ("hour: ", t)

                        da_24h.append(flood_fill_sbc(da_h))

                    da_24h= xr.concat(da_24h, "time")
                    da_acum.append(da_24h)
        
            da = xr.concat(da_acum, "time")
    
            da.name = var_map[da.name]

            # save
            out_fn = config.processed_path + f"{case}_{da.name}_y{yyyy}.nc"
            da.to_netcdf(out_fn)

### -------------------------------- ###

def interpolate(src, tgt, name="unknown", method="nearest"):

    if len(src.longitude.dims) == 1:
        mlon, mlat = np.meshgrid(src.longitude, src.latitude)

        src_lon = mlon.flatten()
        src_lat = mlat.flatten()
    else:
        src_lon = src.longitude.data.flatten()
        src_lat = src.latitude.data.flatten()
    
    values = (src.values.flatten())

    src_lon = src_lon[~np.isnan(values)]
    src_lat = src_lat[~np.isnan(values)]
    values = values[~np.isnan(values)]
    
    # format source sdata
    points = list(zip(src_lat, src_lon))

    tgt_lon =  tgt.longitude.load()
    tgt_lat =  tgt.latitude.load()
    
    target = (tgt_lat, tgt_lon)
    
    n_grid = griddata(points, values, target, method=method)

    n_grid_xr = xr.DataArray(name=name, data=n_grid, dims=('y','x'))

    da_rgrd = n_grid_xr.assign_coords(
           dict(latitude=(['y','x'], tgt.latitude.data),
                longitude=(['y','x'], tgt.longitude.data)))
    return da_rgrd

if __name__ == "__main__":
    gen_ukcp18(var_map, y0=1990, y1=1991)


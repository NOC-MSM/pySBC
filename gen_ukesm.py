"""
Generate Surface Boundary conditions from UKESM output

-- under constuction 2025/05/08 --
"""

import xarray as xr
import iris
import numpy as np

### ---- model specific choices ---- ###

# map variable names
var_map = {
        "x_wind": "u10",
        "y_wind": "v10",
        "air_temperature": "t1500mm",
        "air_pressure_at_sea_level": "mslp",
        "surface_net_downward_longwave_flux": "msdwlwrf",
        "surface_net_downward_shortwave_flux": "msdwswrf",
        "snowfall_flux": "msr",
        "precipitation_flux": "mtpr"}
        
def extract_iris_cube(fn, cube_indices):
    ''' extract ukesm data and move to netcdf formats '''

    cubes = iris.load(fn)
    da_vars = []
    for ind in cube_indices:
        cube = cubes[ind]
        da = xr.DataArray.from_iris(cube)
        if 'height' in da.coords:
            da = da.drop('height')
        da_vars.append(da)

    return xr.merge(da_vars)
    
def extract_glosat(year_dir, month_dir, month):
    glosat_path = '/gws/nopw/j04/glosat/production/UKESM/raw/'
    src_path = glosat_path + f'u-ck651/{year_dir}{month_dir}01T0000Z/'
    
    if month == 'dec': year_dir = year_dir - 1
    fn = src_path + f"ck651a.p5{year_dir}{month}.pp"
    #cube_indices = [188,189,218,223,228,240,241,270,275]
    cube_indices = [218,223]
    ds0 = extract_iris_cube(fn, cube_indices)
    
    fn = src_path + f"ck651a.pd{year_dir}{month}.pp"
    cube_indices = [14,16,22,27,29,38,40]
    ds1 = extract_iris_cube(fn, cube_indices)

    return ds0, ds1

def format_coords(da):
    """
    Add netCDF attributes and format coordinates

    +++
    DUPLICATE of gen_era5 needs removing
    +++

    """

    # mesh lat and lon
    mlon, mlat = np.meshgrid(da.longitude, da.latitude)
    lon_attrs={'long_name':'longitude','units':'degrees_east'}
    lat_attrs={'long_name':'latitude', 'units':'degrees_north'}
    mlon = xr.DataArray(mlon, dims=['y','x'], attrs=lon_attrs)
    mlat = xr.DataArray(mlat, dims=['y','x'], attrs=lat_attrs)
  
    # assign X/Y as indexes
    da = da.drop(['longitude','latitude'])
    da = da.rename({'longitude':'x','latitude':'y'})
    da = da.assign_coords({'longitude':mlon,'latitude':mlat})

    return da

def extract_vars(var_map, ds):
    var_list = list(set(ds) & set(var_map.keys()))

    for var in var_list:
        print (var)
        # select variable and rename
        da = ds[var]
        da.name = var_map[var]

        da = format_coords(da)

        # save
        out_path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/SBC/"
        out_fn = out_path + "glosat_" + var_map[var] + f"_y{year}.nc"
        print (out_fn)
        da.to_netcdf(out_fn)

year0 = 1850
year1 = 1851

year_range = np.arange(year0,year1)

month_dirs = ["01","04","07","10","01"]
month_list = [["jan","feb"],
              ["mar","apr","may"],
              ["jun","jul","aug"],
              ["sep","oct","nov"],
              ["dec"]]

for year in year_range:
    print ("year: ", year)
    year_list = list(np.tile(year,4)) + [year+1] 
    
    ds0_acum, ds1_acum = [], []
    for i, month_dir in enumerate(month_dirs):
        for month in month_list[i]:

            year_dir = year_list[i]
            print (year_dir)
            print ("year_nam: ", year_dir)
            print ("month_nam: ", month_dir)
            print ("month: ", month)
            ds0, ds1 = extract_glosat(year_dir, month_dir, month)


            ds0_acum.append(ds0)
            ds1_acum.append(ds1)


    ds0 = xr.concat(ds0_acum, "time")
    ds1 = xr.concat(ds1_acum, "time")

    extract_vars(var_map, ds0)
    extract_vars(var_map, ds1)

### -------------------------------- ###

def main(): 
    print ('')

    # loop over year

        # loop over variable

            # rename variable

            # save

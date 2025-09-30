"""
Generate Surface Boundary conditions from UKESM output

-- under constuction 2025/05/08 --
"""

import xarray as xr
import iris
import numpy as np
import cf
from dask.diagnostics import ProgressBar
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

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
        "precipitation_flux": "mtpr",
        "specific_humidity": "sph"}
        
#stash_codes = ["m01s03i237",
#               "m01s16i222",
#               "m01s03i209",
#               "m01s03i210",
stash_codes = [
               "m01s03i236",
               "m01s01i201",
               "m01s02i201",
               "m01s05i215",
               "m01s05i216"]

#glosat_path = '/gws/nopw/j04/glosat/production/UKESM/raw/'
#src_path = glosat_path + f'u-ck651/18500101T0000Z/'
#fn = src_path + f"ck651a.p51850jan.pp"
#for code in list(var_map.keys()):
#    print ("code: ", code)
#    cubes = iris.load(fn, code)
#    for cube in cubes:
#        print (cube)
#print (akdsjf)


def extract_iris_cube(fn, cube_indices):
    ''' extract ukesm data and move to netcdf formats '''

    #ll = ["m01s01i235"]
    cubes = iris.load(fn, ll)
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
    fn = src_path + f"ck651a.pd{year_dir}{month}.pp"
    ds = extract_iris_cube(fn)#, cube_indices)
    #fn = src_path + f"ck651a.p5{year_dir}{month}.pp"
    #cube_indices = [188,189,218,223,228,240,241,270,275]
    #cube_indices = [218,223]
    #cube_indices = [223]
    
    #cube_indices = [14]
    #cube_indices = [14,16,22,27,29,38,40]
    #ds1 = extract_iris_cube(fn, cube_indices)

    with ProgressBar():
        ds = ds.load()
        #ds1 = ds1.load()

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
    #lon_attrs={'long_name':'longitude','units':'degrees_east'}
    #lat_attrs={'long_name':'latitude', 'units':'degrees_north'}
    #mlon = xr.DataArray(mlon, dims=['y','x'], attrs=lon_attrs)
    #mlat = xr.DataArray(mlat, dims=['y','x'], attrs=lat_attrs)
  
    # assign X/Y as indexes
    da = da.drop(['longitude','latitude'])
    da = da.rename({'longitude':'x','latitude':'y'})
    da = da.assign_coords({'longitude':(["y","x"], mlon),
                           'latitude':(["y","x"], mlat)})

    return da

def extract_vars(var_map, ds, year):
    var_list = list(set(ds) & set(var_map.keys()))

    for var in var_list:
        print (var)
        # select variable and rename
        da = ds[var]

        da.name = var_map[var]

        # save
        out_path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/SBC/"
        out_fn = out_path + "glosat_" + var_map[var] + f"_y{year}.nc"
        print (out_fn)
        da.to_netcdf(out_fn)

def flood_fill_sbc(da, is_wind=False):
    """
    flood fill sbc based on land sea mask
    """

    # get LSM derived from UKESM domain_cfg - see gen_land_sea_mask()
    path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/"
    lsm = xr.open_dataarray(path + "SBC/LSM.nc")

    # interpolate from u/v grid to t grid
    if is_wind:
        da = interpolate(da, lsm, name=da.name, method="linear")

    # mask da
    da_msk = da.where(lsm == 0)

    # bug with "where" means lon coords are dropped
    da_msk = da_msk.assign_coords(longitude=da.longitude)

    da_filled= interpolate(da_msk, da_msk, name=da.name, method="nearest")

    return da_filled

def gen_ukesm(stash_codes):
    year0 = 1850
    year1 = 1851
    
    year_range = np.arange(year0,year1)
    
    month_dirs = ["01","04","07","10","01"]
    month_list = [["jan","feb"],
                  ["mar","apr","may"],
                  ["jun","jul","aug"],
                  ["sep","oct","nov"],
                  ["dec"]]
    
    glosat_path = '/gws/nopw/j04/glosat/production/UKESM/raw/'
    
    for j, code in enumerate(stash_codes):

        print ("CODE", code)
        for year in year_range:
            print ("year: ", year)
            year_list = list(np.tile(year,4)) + [year+1] 
            
            da_acum, ds1_acum = [], []
            for i, month_dir in enumerate(month_dirs):
                for month in month_list[i]:
        
                    year_dir = year_list[i]
                    print (year_dir)
                    print ("year_nam: ", year_dir)
                    print ("month_nam: ", month_dir)
                    print ("month: ", month)
                    src_path = glosat_path + f'u-ck651/{year_dir}{month_dir}01T0000Z/'
                    if month == 'dec': year_dir = year_dir - 1
                   
                    fn = src_path + f"ck651a.p5{year_dir}{month}.pp"
                    cube = iris.load_cube(fn, code)
                    with ProgressBar():
                        da = xr.DataArray.from_iris(cube).load()

                    print ('')
                    print ("loaded name ", da.name)
                    print ('')

                    if 'height' in da.coords:
                        da = da.drop('height')

                    da = format_coords(da)

                    if da.name in ["x_wind","y_wind"]:
                        da = flood_fill_sbc(da, is_wind=True)
                    else:
                        da = flood_fill_sbc(da)

                    da_acum.append(da)
        
            da = xr.concat(da_acum, "time")
    
        da.name = var_map[da.name]

        # save
        out_path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/SBC/"
        out_fn = out_path + "glosat_" + da.name + f"_y{year}.nc"
        print (out_fn)
        da.to_netcdf(out_fn)

### -------------------------------- ###

def dep_interpolate_lev(ds):
    """ nearest neighbour interpolation for a single level """

    var_list = list(set(ds) & set(var_map.keys()))

    #with ProgressBar():
    #    ds = ds.load()

    da_set = []
    for var in var_list:
        da = ds[var]
        src_lon =  da.longitude.values.flatten()
        src_lat =  da.latitude.values.flatten()
        
        values = (da.values.flatten())

        src_lon = src_lon[~np.isnan(values)]
        src_lat = src_lat[~np.isnan(values)]
        values = values[~np.isnan(values)]
        
        # format source sdata
        points = list(zip(src_lat, src_lon))

        tgt_lon =  da.longitude.load()
        tgt_lat =  da.latitude.load()
        
        target = (tgt_lat, tgt_lon)
        
        n_grid = griddata(points, values, target, method='linear')

        n_grid_xr = xr.DataArray(name=var, data=n_grid, dims=('y','x'))
        da_set.append(n_grid_xr)

    n_grid = xr.merge(da_set)
    ds = ds.assign_coords(
           dict(latitude=(['y','x'], ds.latitude.data),
                longitude=(['y','x'], ds.longitude.data)))

    return ds

def main(): 
    print ('')
    # loop over year

        # loop over variable

            # rename variable

            # save
def interpolate(src, tgt, name="unknown", method="nearest"):

    print (src)
    print( len(src.longitude.dims))
    if len(src.longitude.dims) == 1:
        mlon, mlat = np.meshgrid(src.longitude, src.latitude)

        src_lon = mlon.flatten()
        src_lat = mlat.flatten()
        print ("option a")
    else:
        print ("option b")
        src_lon = src.longitude.data.flatten()
        src_lat = src.latitude.data.flatten()
    
    values = (src.values.flatten())

    print (values.shape)
    print (src_lon.shape)
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

def gen_land_sea_mask(path):
    """ generate land-sea mask from parent domain configuration file """

    # get land sea mask
    cfg = xr.open_dataset(path + "DOM/UKESM/domcfg_UKESM1p1_gdept.nc", chunks="auto")
    lsm = xr.where(cfg.top_level == 0, 1, 0)
    lsm.name = "LSM"
    latitude = cfg.nav_lat.data
    longitude = xr.where(cfg.nav_lon.data < 0, cfg.nav_lon.data + 360,
                                               cfg.nav_lon.data)
    lsm = lsm.assign_coords(
             dict(latitude=(['y','x'], latitude),
                  longitude=(['y','x'], longitude)))

    # interpolate to atmosphere grid
    out_path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/SBC/"
    out_fn = out_path + "glosat_u10_y1850.nc"
    da = xr.open_dataarray(out_fn)


    rgrd = interpolate(lsm, da, name="LSM", method="linear")
    lsm = interpolate(rgrd, da, name="LSM", method="nearest")
    
    lsm = xr.where(lsm == 0, 0, 1)

    # save
    with ProgressBar():
        lsm.to_netcdf(path + "SBC/LSM.nc")

domcfg_path = "/gws/nopw/j04/verify_oce/NEMO/Preprocessing/"
#gen_land_sea_mask(domcfg_path)
gen_ukesm(stash_codes)

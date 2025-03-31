# pySBC

Scripts for generating surface boundary conditions for regional NEMO 
configurations.

 - config.py: Contains file paths, variable names, and dates etcetera that 
   are used during processing.
 - gen_era5.py: Based on a script of Nico's, which processes ERA5 data
   ready for use with NEMO. The reference parameter choices are for AMM15.
 - get_era5.py: Downloads ERA5 variables defined in config.py.
 - gen_LSM.py: Extracts and processes land-sea mask from global file.

## Setup
### conda environment
Use the following to configure a conda environment for use with pySBC.
~~~
conda env create -f environment.yml
~~~

### Usage
Before processing, the user is required to set the desired domain choices in
config.py. The processing is then done in a two steps:
1. Download data (get_era5.py)
2. Process data (gen_era5.py, gen_LSM.py)

### CDS configuration
In order to download data from the CDS service you'll need to have an access token stored on your local system. A guide to these tokens can be found at: https://cds.climate.copernicus.eu/how-to-api

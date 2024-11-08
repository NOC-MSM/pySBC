**31 Jan 24 - RDP**

**This repository had issues with the time coordinates
and the orientation of latitude. A correction has now be applied but not tested.**

# pySBC

Scripts for generating surface boundary conditions for regional NEMO 
configurations.

 - gen_era5.py: Based on a script of Nico's, which processes ERA5 data
   ready for use with NEMO. The reference parameter choices are for AMM15.
 - gen_era5_legacy.py: Nico's original script.

## Setup
### conda environment
Use the following to configure a conda environment for use with pySBC.
~~~
conda env create -f environment.yml
~~~
### CDS configuration
In order to download data from the CDS service you'll need to have an access token stored on your local system. A guide to these tokens can be found at: https://cds.climate.copernicus.eu/how-to-api

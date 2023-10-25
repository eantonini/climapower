import xarray as xr
import xesmf as xe

import modules.directories as directories


# Define the reference ERA5 variable. Irrelevant which variable is chosen.
ERA5_variable_name = '100m_u_component_of_wind'

# Define the CORDEX variable to be regridded.
# CORDEX_variable_name = {'long': '10m_wind_speed', 'short': 'sfcWind'}
# CORDEX_variable_name = {'long': '2m_air_temperature', 'short': 'tas'}
# CORDEX_variable_name = {'long': 'surface_solar_radiation_downwards', 'short': 'rsds'}
# CORDEX_variable_name = {'long': 'surface_upwelling_shortwave_radiation', 'short': 'rsus'}
CORDEX_variable_name = {'long': 'total_run_off_flux', 'short': 'mrro'}

if CORDEX_variable_name['long'] == 'total_run_off_flux':
    CORDEX_time_resolution = '6hourly'
else:
    CORDEX_time_resolution = '3hourly'

# Load the ERA5 data.
ds_era5 = xr.open_dataset(directories.get_climate_data_path(2010, ERA5_variable_name, climate_data_source='historical'), engine='netcdf4')
ds_cordex = xr.open_dataset(directories.get_climate_data_path(2010, CORDEX_variable_name['long'], CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections').replace('.nc', '__original.nc'), engine='netcdf4')

# Rename coordinates of ds_era5 to match xesmf requirements.
ds_era5 = ds_era5.rename({'latitude': 'lat', 'longitude': 'lon'})

# Create the regridder object.
regridder = xe.Regridder(ds_cordex, ds_era5, "bilinear")

# For each year, regrid the CORDEX data and save it to a netcdf file.
start_year = 2010
end_year = 2100
for year in range(start_year,end_year+1):
    
    # Get the full data path of the CORDEX data.
    data_file = directories.get_climate_data_path(year, CORDEX_variable_name['long'], CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections')

    # Load the CORDEX data.
    ds_cordex = xr.open_dataset(data_file.replace('.nc', '__original.nc'), engine='netcdf4')

    # Regrid the CORDEX data.
    regridded_ds_cordex = regridder(ds_cordex[CORDEX_variable_name['short']]).rename(CORDEX_variable_name['long'])

    # Rename the coordinates to match the original ds_era5.
    regridded_ds_cordex = regridded_ds_cordex.rename({'lon': 'longitude', 'lat': 'latitude'})

    # Save the regridded data to a netcdf file.
    regridded_ds_cordex.to_netcdf(data_file)
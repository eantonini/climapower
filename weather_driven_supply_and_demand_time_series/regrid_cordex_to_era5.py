import xarray as xr
import xesmf as xe

import modules.settings as settings

# Define the ERA5 source data and the CORDEX target data

# ERA5_variable_name = '100m_u_component_of_wind'
# ERA5_variable_name = '2m_temperature'
ERA5_variable_name = 'surface_solar_radiation_downwards'
custom_ERA5_variable_name = 'hourly_'+ERA5_variable_name

# representative_concentration_pathway = 'rcp_2_6'
# representative_concentration_pathway = 'rcp_4_5'
representative_concentration_pathway = 'rcp_8_5'

global_climate_model = 'cnrm_cerfacs_cm5'

regional_climate_model = 'cnrm_aladin63'

# CORDEX_variable_name = '10m_wind_speed'
# CORDEX_variable_name = '2m_air_temperature'
# CORDEX_variable_name = 'surface_solar_radiation_downwards'
# CORDEX_variable_name = 'surface_upwelling_shortwave_radiation'
CORDEX_variable_name = 'total_run_off_flux'
# custom_CORDEX_variable_name = '3h_'+CORDEX_variable_name
custom_CORDEX_variable_name = '6h_'+CORDEX_variable_name
# CORDEX_short_variable_name = 'sfcWind'
# CORDEX_short_variable_name = 'tas'
# CORDEX_short_variable_name = 'rsds'
# CORDEX_short_variable_name = 'rsus'
CORDEX_short_variable_name = 'mrro'

CORDEX_data_folder = '/CORDEX-Europe-'+representative_concentration_pathway.upper()+'-'+global_climate_model.upper()+'-'+regional_climate_model.upper()+'-'+CORDEX_variable_name

# Load the ERA5 data
ds_era5 = xr.open_dataset(settings.climate_data_directory+'/ERA5-Europe-'+ERA5_variable_name+'/ERA5-1959-gridded_'+custom_ERA5_variable_name+'.nc', engine='netcdf4')
ds_cordex = xr.open_dataset(settings.climate_data_directory+CORDEX_data_folder+'/CORDEX-2010-gridded_'+custom_CORDEX_variable_name+'_original.nc', engine='netcdf4')

# Rename coordinates of ds_era5 to match xesmf requirements
ds_era5 = ds_era5.rename({'latitude': 'lat', 'longitude': 'lon'})

# Create the regridder object
regridder = xe.Regridder(ds_cordex, ds_era5, "bilinear")

# For each year, regrid the CORDEX data and save it to a netcdf file
start_year = 2010
end_year = 2100
for year in range(start_year,end_year+1):
    # Load the CORDEX data
    data_file = settings.climate_data_directory+CORDEX_data_folder+'/CORDEX-{:d}-gridded_'.format(year)+custom_CORDEX_variable_name+'_original.nc'
    ds_cordex = xr.open_dataset(data_file, engine='netcdf4')

    # Regrid the CORDEX data
    regridded_ds_cordex = regridder(ds_cordex[CORDEX_short_variable_name]).rename(CORDEX_variable_name)

    # Rename the coordinates to match the original ds_era5
    regridded_ds_cordex = regridded_ds_cordex.rename({'lon': 'longitude', 'lat': 'latitude'})

    # Save the regridded data to a netcdf file
    regridded_ds_cordex.to_netcdf(settings.climate_data_directory+CORDEX_data_folder+'/CORDEX-{:d}-gridded_'.format(year)+custom_CORDEX_variable_name+'.nc')
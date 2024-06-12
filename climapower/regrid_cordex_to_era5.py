import xarray as xr
import xesmf as xe

import modules.directories as directories


# Define the reference ERA5 variable. Irrelevant which variable is chosen.
ERA5_variable_name = '2m_temperature'

# Define the CORDEX variable to be regridded.
CORDEX_variables = [{'long': '10m_wind_speed', 'short': 'sfcWind'},
                    {'long': '2m_air_temperature', 'short': 'tas'},
                    {'long': 'surface_solar_radiation_downwards', 'short': 'rsds'},
                    {'long': 'surface_upwelling_shortwave_radiation', 'short': 'rsus'},
                    {'long': 'total_run_off_flux', 'short': 'mrro'},
                    ]

# Define the CORDEX experiment and models.
models = {'set_1' : {'global_climate_model' : 'cnrm_cerfacs_cm5',
                     'regional_climate_model' : 'cnrm_aladin63',
                     'rcps' : ['rcp_2_6',
                               'rcp_4_5',
                               'rcp_8_5']},
          'set_2' : {'global_climate_model' : 'mpi_m_mpi_esm_lr',
                     'regional_climate_model' : 'ictp_regcm4_6',
                     'rcps' : ['rcp_2_6',
                               'rcp_8_5']},
          'set_3' : {'global_climate_model' : 'miroc_miroc5',
                     'regional_climate_model' : 'clmcom_clm_cclm4_8_17',
                     'rcps' : ['rcp_2_6',
                               'rcp_8_5']}
          }

# Define the years over which to regrid the CORDEX files.
start_year = 2006
end_year = 2009

for CORDEX_variable_name in CORDEX_variables:

    if CORDEX_variable_name['long'] == 'total_run_off_flux':
        CORDEX_time_resolution = '6hourly'
    else:
        CORDEX_time_resolution = '3hourly'
    
    for model_set in models.keys():
        
        for rcp in models[model_set]['rcps']:
            
            # Load the ERA5 data.
            ds_era5 = xr.open_dataset(directories.get_climate_data_path(start_year, ERA5_variable_name, climate_data_source='reanalysis'), engine='netcdf4')
            ds_cordex = xr.open_dataset(directories.get_climate_data_path(start_year, CORDEX_variable_name['long'], time_resolution=CORDEX_time_resolution, climate_data_source='projections',
                                                                          representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']).replace('.nc', '__original.nc'), engine='netcdf4')

            # Rename coordinates of ds_era5 to match xesmf requirements.
            ds_era5 = ds_era5.rename({'latitude': 'lat', 'longitude': 'lon'})

            # Create the regridder object.
            regridder = xe.Regridder(ds_cordex, ds_era5, "bilinear")

            # For each year, regrid the CORDEX data and save it to a netcdf file.
            for year in range(start_year,end_year+1):
                
                # Get the full data path of the CORDEX data.
                data_file = directories.get_climate_data_path(year, CORDEX_variable_name['long'], time_resolution=CORDEX_time_resolution, climate_data_source='projections',
                                                              representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model'])

                # Load the CORDEX data.
                ds_cordex = xr.open_dataset(data_file.replace('.nc', '__original.nc'), engine='netcdf4')

                # Regrid the CORDEX data.
                regridded_ds_cordex = regridder(ds_cordex[CORDEX_variable_name['short']]).rename(CORDEX_variable_name['long'])

                # Rename the coordinates to match the original ds_era5.
                regridded_ds_cordex = regridded_ds_cordex.rename({'lon': 'longitude', 'lat': 'latitude'})

                # Save the regridded data to a netcdf file.
                regridded_ds_cordex.to_netcdf(data_file)
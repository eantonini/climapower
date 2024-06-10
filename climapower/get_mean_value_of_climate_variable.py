import xarray as xr
import numpy as np
import os
from datetime import datetime

import settings
import modules.directories as directories

# Define the variable to average
# variable_to_average = '100m_wind_power_density'
# variable_to_average = 'forecast_surface_roughness'
# short_variable_name = 'fsr'
variable_to_average = 'surface_solar_radiation_downwards'
short_variable_name = 'ssrd'

# Create a Dask cluster and client
from dask_mpi import initialize
from distributed import Client
initialize(local_directory=settings.working_directory, memory_limit='95GB')
client = Client()

# Define function to write to log file
def write_to_log_file(variable_to_average, message, new_file=False):
    if not os.path.exists(settings.working_directory+'/Err_and_log_files'):
        os.mkdir(settings.working_directory+'/Err_and_log_files')
    mode = 'w' if new_file else 'a'
    with open(settings.working_directory+'/Err_and_log_files/get_mean_'+variable_to_average+'.txt', mode) as outputFile:
        outputFile.write(message)

# Write the start time to the log file
now = datetime.now()
current_time = now.strftime('%H:%M:%S')
write_to_log_file(variable_to_average, 'Starting task at '+current_time+'\n\n', new_file=True)

# Write the client information to the log file
write_to_log_file(variable_to_average, 'Client information: '+str(client)+'\n\n')

if variable_to_average == '100m_wind_power_density':
    # Load variables
    u_component_name = '100m_u_component_of_wind'
    v_component_name = '100m_v_component_of_wind'
    u_component_filename_list = [directories.get_climate_data_filename(year, u_component_name) for year in range(settings.start_year_for_mean_climate_variable,settings.end_year_for_mean_climate_variable+1)]
    v_component_filename_list = [directories.get_climate_data_filename(year, v_component_name) for year in range(settings.start_year_for_mean_climate_variable,settings.end_year_for_mean_climate_variable+1)]
    u_component_data = xr.open_mfdataset(u_component_filename_list, engine='netcdf4', parallel=True, chunks={'latitude':20, 'longitude':20})
    v_component_data = xr.open_mfdataset(v_component_filename_list, engine='netcdf4', parallel=True, chunks={'latitude':20, 'longitude':20})
    write_to_log_file(variable_to_average, 'Variables loaded\n\n')

    # Calculate the wind speed time series and the power density time series for each grid point in the domain and then calculate the mean power density for the whole domain (i.e. the mean power density for each grid point in the domain) 
    wind_speed_time_series = np.sqrt(np.power(u_component_data.u100,2)+np.power(v_component_data.v100,2))
    power_density_time_series = 0.5*np.power(wind_speed_time_series,3)
    averaged_variable = power_density_time_series.mean(dim='time')
    write_to_log_file(variable_to_average, 'Variables calculated\n\n')
else:
    # Load variables
    variable_filename_list = [directories.get_climate_data_filename(year, variable_to_average) for year in range(settings.start_year_for_mean_climate_variable,settings.end_year_for_mean_climate_variable+1)]
    variable_data = xr.open_mfdataset(variable_filename_list, engine='netcdf4', parallel=True, chunks={'latitude':20, 'longitude':20})
    write_to_log_file(variable_to_average, 'Variables loaded\n\n')

    # Calculate the mean value of the variable
    averaged_variable = variable_data[short_variable_name].mean(dim='time')
    write_to_log_file(variable_to_average, 'Variables calculated\n\n')

# Compute the mean power density in parallel and save it to a NetCDF file
averaged_variable.compute()
averaged_variable.to_netcdf(directories.get_mean_climate_data_filename(variable_to_average), engine='netcdf4')
write_to_log_file(variable_to_average, 'Variables saved\n\n')

# Write the end time to the log file
now = datetime.now()
current_time = now.strftime('%H:%M:%S')
write_to_log_file(variable_to_average, 'Ending task at '+current_time)

# Close the Dask client and cluster
client.close()
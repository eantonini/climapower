import tarfile

import modules.directories as directories

# Define the CORDEX variable to extract and rename.
# CORDEX_variable_name='10m_wind_speed'
# CORDEX_variable_name='2m_air_temperature'
# CORDEX_variable_name='surface_solar_radiation_downwards'
# CORDEX_variable_name='surface_upwelling_shortwave_radiation'
CORDEX_variable_name='total_run_off_flux'

if CORDEX_variable_name == 'total_run_off_flux':
    CORDEX_time_resolution ='6hourly'
else
    CORDEX_time_resolution ='3hourly'

# For each year, extract the CORDEX data.
start_year = 2010
end_year = 2100
for year in range(start_year,end_year+1):

    # Define original data path.
    original_data_file = directories.get_climate_data_path(year, CORDEX_variable_name, CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections').replace('.nc', '.tar.gz')

    # Define new data path.
    new_data_file = directories.get_climate_data_path(year, CORDEX_variable_name, CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections').replace('.nc', '__original.nc')

    # Extract the compressed data file.
    with tarfile.open(original_data_file, 'r:gz') as tar:
        extracted_filename = tar.getnames()[0]
        tar.extract(filename, path=directories.get_climate_data_path(year, CORDEX_variable_name, CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections', return_folder=True))
    
    # Rename the extracted file.
    os.rename(extracted_filename, new_data_file)

    # Remove original data file.
    os.remove(original_data_file)

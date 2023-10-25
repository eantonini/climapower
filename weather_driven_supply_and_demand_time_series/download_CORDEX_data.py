import cdsapi
import os

import modules.directories as directories


# Create a new CDS API session.
c = cdsapi.Client()

# Define the CORDEX variable to download.
# CORDEX_variable_name = '10m_wind_speed'
# CORDEX_variable_name = '2m_air_temperature'
# CORDEX_variable_name = 'surface_solar_radiation_downwards'
# CORDEX_variable_name = 'surface_upwelling_shortwave_radiation'
CORDEX_variable_name = 'total_run_off_flux'

# The total runoff flux is available at 6-hourly resolution.
if CORDEX_variable_name == 'total_run_off_flux':
    temporal_resolution = '6_hours'
    CORDEX_time_resolution = '6hourly'
else:
    temporal_resolution = '3_hours'
    CORDEX_time_resolution = '3hourly'

# Some variables require an additional year in the settings, even though a single year is downloaded.
if CORDEX_variable_name == '10m_wind_speed' or CORDEX_variable_name == '2m_air_temperature':
    additional_year = 1
else:
    additional_year = 0

# Download the CORDEX data.
for year in range(2010,2041):
# for year in range(2041,2071):
# for year in range(2071,2101):

    data_folder = directories.get_climate_data_path(year, CORDEX_variable_name, CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections', return_folder=True)

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    data_file = directories.get_climate_data_path(year, CORDEX_variable_name, CORDEX_time_resolution=CORDEX_time_resolution, climate_data_source='projections').replace('.nc', '.tar.gz')
    
    c.retrieve(
    'projections-cordex-domains-single-levels',
    {
        'format': 'tgz',
        'domain': 'europe',
        'experiment': representative_concentration_pathway,
        'horizontal_resolution': '0_11_degree_x_0_11_degree',
        'temporal_resolution': temporal_resolution,
        'variable': CORDEX_variable_name,
        'gcm_model': global_climate_model,
        'rcm_model': regional_climate_model,
        'ensemble_member': 'r1i1p1',
        'start_year': str(int(year)),
        'end_year': str(int(year+additional_year)),
    },
    data_file)
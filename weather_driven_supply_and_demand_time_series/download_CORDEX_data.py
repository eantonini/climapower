import cdsapi
import os

import modules.settings as settings


# Create a new CDS API session
c = cdsapi.Client()

# Define the CORDEX data to download

representative_concentration_pathway = 'rcp_2_6'
# representative_concentration_pathway = 'rcp_4_5'
# representative_concentration_pathway = 'rcp_8_5'

global_climate_model = 'cnrm_cerfacs_cm5'

regional_climate_model = 'cnrm_aladin63'

# CORDEX_variable_name = '10m_wind_speed'
# CORDEX_variable_name = '2m_air_temperature'
# CORDEX_variable_name = 'surface_solar_radiation_downwards' # Do not add +1 in end_year
# CORDEX_variable_name = 'surface_upwelling_shortwave_radiation' # Do not add +1 in end_year
CORDEX_variable_name = 'total_run_off_flux' # Do not add +1 in end_year
# custom_variable_name = '3h_'+CORDEX_variable_name
custom_variable_name = '6h_'+CORDEX_variable_name # For total_run_off_flux

# temporal_resolution = '3_hours'
temporal_resolution = '6_hours' # For total_run_off_flux

# Download the CORDEX data

for year in range(2010,2041):
# for year in range(2041,2071):
# for year in range(2071,2101):

    data_folder = settings.climate_data_directory+'/CORDEX-Europe-'+representative_concentration_pathway.upper()+'-'+global_climate_model.upper()+'-'+regional_climate_model.upper()+'-'+CORDEX_variable_name

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    data_file = data_folder+'/CORDEX-{:d}-gridded_'.format(year)+custom_variable_name+'.tar.gz'
    
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
        'end_year': str(int(year)),
    },
    data_file)
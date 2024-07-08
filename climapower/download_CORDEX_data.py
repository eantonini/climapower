import cdsapi
import os

import modules.directories as directories


# Create a new CDS API session.
c = cdsapi.Client()

# Define the CORDEX variable to download.
CORDEX_variables = ['2m_air_temperature',
                    '10m_wind_speed',
                    'surface_solar_radiation_downwards',
                    'surface_upwelling_shortwave_radiation',
                    'total_run_off_flux',
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

# Define the years for the data download.
start_year = 2010
end_year = 2100

# Download the CORDEX data.
for CORDEX_variable_name in CORDEX_variables:

    # The total runoff flux is available at 6-hourly resolution.
    if CORDEX_variable_name == 'total_run_off_flux':
        temporal_resolution = '6_hours'
        CORDEX_time_resolution = '6hourly'
    else:
        temporal_resolution = '3_hours'
        CORDEX_time_resolution = '3hourly'
    
    for model_set in models.keys():

        # Some variables require an additional year in the settings, even though a single year is downloaded.
        if ((models[model_set]['global_climate_model'] == 'cnrm_cerfacs_cm5' or models[model_set]['global_climate_model'] == 'mpi_m_mpi_esm_lr') and
            (CORDEX_variable_name == '10m_wind_speed' or CORDEX_variable_name == '2m_air_temperature')):
            additional_year = 1
        else:
            additional_year = 0
        
        for rcp in models[model_set]['rcps']:

            for year in range(start_year,end_year+1):

                data_folder = directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections', return_folder=True,
                                                                representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model'])

                if not os.path.exists(data_folder):
                    os.makedirs(data_folder)

                data_file = directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections',
                                                              representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']).replace('.nc', '.tar.gz')
                
                c.retrieve(
                'projections-cordex-domains-single-levels',
                {
                    'format': 'tgz',
                    'domain': 'europe',
                    'experiment': rcp,
                    'horizontal_resolution': '0_11_degree_x_0_11_degree',
                    'temporal_resolution': temporal_resolution,
                    'variable': CORDEX_variable_name,
                    'gcm_model': models[model_set]['global_climate_model'],
                    'rcm_model': models[model_set]['regional_climate_model'],
                    'ensemble_member': 'r1i1p1',
                    'start_year': str(int(year)),
                    'end_year': str(int(year+additional_year)),
                },
                data_file)
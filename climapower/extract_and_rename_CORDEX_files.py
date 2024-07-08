import os
import tarfile

import modules.directories as directories


# Define the CORDEX variable to extract and rename.
CORDEX_variable = [#'10m_wind_speed',
                   '2m_air_temperature',
                   'surface_solar_radiation_downwards',
                   'surface_upwelling_shortwave_radiation',
                   'total_run_off_flux'
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

# Define the years over which to extract and rename the CORDEX files.
start_year = 2006
end_year = 2100

for CORDEX_variable_name in CORDEX_variable:

    if CORDEX_variable_name == 'total_run_off_flux':
        CORDEX_time_resolution ='6hourly'
    else:
        CORDEX_time_resolution ='3hourly'
    
    for model_set in models.keys():

        for rcp in models[model_set]['rcps']:

            for year in range(start_year,end_year+1):

                # Define original data path.
                original_data_file = directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections',
                                                                       representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']).replace('.nc', '.tar.gz')

                # Define new data path.
                new_data_file = directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections',
                                                                  representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']).replace('.nc', '__original.nc')

                # Extract the compressed data file.
                with tarfile.open(original_data_file, 'r:gz') as tar:
                    extracted_filename = tar.getnames()[0]
                    tar.extract(extracted_filename, filter='data', path=directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections', return_folder=True,
                                                                                                          representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']))
                
                # Add the full path to the extracted file.
                extracted_filename = directories.get_climate_data_path(year, CORDEX_variable_name, time_resolution=CORDEX_time_resolution, climate_data_source='CORDEX_projections', return_folder=True,
                                                                       representative_concentration_pathway=rcp, global_climate_model=models[model_set]['global_climate_model'], regional_climate_model=models[model_set]['regional_climate_model']) + extracted_filename

                # Rename the extracted file.
                os.rename(extracted_filename, new_data_file)

                # Remove original data file.
                os.remove(original_data_file)
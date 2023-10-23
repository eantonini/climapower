##BSUB -J extract_CORDEX_data
##BSUB -oo Err_and_log_files/extract_CORDEX_data.log
##BSUB -eo Err_and_log_files/extract_CORDEX_data.err
##BSUB -n 1
##BSUB -q p_long
##BSUB -P R000 # 0352

climate_data_directory='/work/seme/ea02323/climate_to_energy_conversion/climate_data'

# representative_concentration_pathway='rcp_2_6'
# representative_concentration_pathway='rcp_4_5'
representative_concentration_pathway='rcp_8_5'

global_climate_model='cnrm_cerfacs_cm5'

regional_climate_model='cnrm_aladin63'

# CORDEX_variable_name='10m_wind_speed'
# CORDEX_variable_name='2m_air_temperature'
# CORDEX_variable_name='surface_solar_radiation_downwards'
# CORDEX_variable_name='surface_upwelling_shortwave_radiation'
CORDEX_variable_name='total_run_off_flux'
# custom_variable_name='3h_'$CORDEX_variable_name
custom_variable_name='6h_'$CORDEX_variable_name

data_folder='/CORDEX-Europe-'${representative_concentration_pathway^^}'-'${global_climate_model^^}'-'${regional_climate_model^^}'-'$CORDEX_variable_name'/'

for year in {2010..2100}
do
    # Define original data path based on 'CORDEX-Europe-RCP_2_6-CNRM_CERFACS_CM5-CNRM_ALADIN63-10m_wind_speed/CORDEX-2023-gridded_3h_10m_wind_speed.tar.gz'
    original_data_file='/CORDEX-'${year}'-gridded_'${custom_variable_name}'.tar.gz'

    # Define new data path based on 'CORDEX-Europe-RCP_2_6-CNRM_CERFACS_CM5-CNRM_ALADIN63-10m_wind_speed/CORDEX-2023-gridded_3h_10m_wind_speed_original.nc'
    new_data_file='/CORDEX-'${year}'-gridded_'${custom_variable_name}'_original.nc'

    # Extract and rename data file
    extracted_filename=$(tar -xvzf ${climate_data_directory}${data_folder}${original_data_file} -C ${climate_data_directory}${data_folder})
    mv ${climate_data_directory}${data_folder}${extracted_filename} ${climate_data_directory}${data_folder}${new_data_file}

    # Remove original data file
    rm ${climate_data_directory}${data_folder}${original_data_file}
done
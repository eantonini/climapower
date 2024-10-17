import os

# Define if the code is running on a local machine or on zeus.
on_hpc = True

# Set working directory and data directories.
working_directory = os.getcwd()
energy_data_directory = working_directory + '/energy_data'
# climate_data_directory = working_directory + '/climate_data'
climate_data_directory = '/work/cmcc/ea02323/climate_data'
geospatial_data_directory = working_directory + '/geospatial_data'

# Set folder where results will be saved.
result_folder = working_directory + '/postprocessed_results'
if not os.path.exists(result_folder):
    os.makedirs(result_folder)

# Decide whether to make and save plots.
make_plots = True
save_plots = True

# Set folder where plots will be saved.
if save_plots:
    figure_folder = working_directory + '/figures'
    if not os.path.exists(figure_folder):
        os.mkdir(figure_folder)

# Define the climate data source.
climate_data_source = 'reanalysis' # 'reanalysis' or 'CORDEX_projections' or 'CMIP6_projections

# Set the years over which to aggregate climate data.
if climate_data_source == 'reanalysis':

    focus_region = 'Europe' # 'Europe' or 'World'
    data_product = 'ERA5'
    aggregation_start_year = 1940
    aggregation_end_year = 2023

elif climate_data_source == 'CORDEX_projections':

    focus_region = 'Europe'
    data_product = 'CORDEX'
    aggregation_start_year = 2006
    aggregation_end_year = 2100

    # Define the CORDEX experiment and models.
    CORDEX_experiment_and_models = {
        'representative_concentration_pathway' : 'rcp_2_6', # 'rcp_2_6' or 'rcp_4_5' or 'rcp_8_5'
        'global_climate_model' : 'miroc_miroc5', # 'cnrm_cerfacs_cm5' or 'mpi_m_mpi_esm_lr' or 'miroc_miroc5'
        'regional_climate_model' : 'clmcom_clm_cclm4_8_17' # 'cnrm_aladin63' or 'ictp_regcm4_6' or 'clmcom_clm_cclm4_8_17'
    }

elif climate_data_source == 'CMIP6_projections':

    focus_region = 'World'
    data_product = 'CMIP6'
    aggregation_start_year = 2015
    aggregation_end_year = 2100

    # Define the CMIP6 experiment and models.
    CMIP6_experiment_and_model = {
        'shared_socioeconomic_pathway' : 'ssp1_2_6', # 'ssp1_2_6' or 'ssp2_4_5' or 'ssp5_8_5'
        'climate_model' : 'hadgem3_gc31_ll' # 'mpi_esm1_2_lr' or 'cmcc_esm2' or 'cesm2' or 'hadgem3_gc31_ll' or 'bcc_csm2_mr'
    }

# Set the chunk size for the climate data.
chunk_size_lon_lat = {'longitude': 10, 'latitude': 10}
chunk_size_x_y = {'x': 10, 'y': 10}

# Set the years over which to calculate the mean climate variables used to estimate the capacity factors of wind and solar.
start_year_for_mean_climate_variable = 2000
end_year_for_mean_climate_variable = 2020

# Set the data source against which to calibrate the results. This is used only for the calibration of wind and solar capacity factors.
calibration_data_source = 'entsoe' # 'open_power_system_database' or 'era5' or 'entsoe'

# Decide whether to calibrate the results. The calibration is implemented for wind capacity factors and hydropower inflow time series.
calibration_folder = working_directory + '/calibration_results'
calibrate = True
if calibrate:
    if not os.path.exists(calibration_folder):
        os.mkdir(calibration_folder)

# Settings for wind resource.
offshore_wind_turbine = 'IEA_10MW_198_RWT.yaml'
onshore_wind_turbine = 'IEA_3.4MW_130_RWT.yaml'
read_wind_coefficients = False

# Settings for solar resource.
solar_panel = 'CSi'
read_solar_coefficients = False

# Settings for hydropower resource.
read_hydropower_coefficients = False

# Settings for heating demand.
heating_daily_temperature_threshold = 15.0

# Settings for cooling demand.
cooling_daily_temperature_threshold = 24.0
cooling_hourly_temperature_threshold = 28.0
import os

# Define if the code is running on a local machine or on zeus.
on_zeus = True

# Set working directory and data directories.
working_directory = os.getcwd()
energy_data_directory = working_directory + '/energy_data'
climate_data_directory = working_directory + '/climate_data'
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

# Define climate dataset info.
dataset_info = {
    'last_historical_year' : 2022,
    'focus_region' : 'Europe',
    'historical_dataset' : 'ERA5',
    'future_dataset' : 'CORDEX',
    'representative_concentration_pathway' : 'rcp_4_5',
    'global_climate_model' : 'cnrm_cerfacs_cm5',
    'regional_climate_model' : 'cnrm_aladin63'
}

# Set the chunk size for the climate data.
chunk_size_lon_lat = {'longitude': 10, 'latitude': 10}
chunk_size_x_y = {'x': 10, 'y': 10}

# Set the years over which to aggregate climate data.
aggregation_start_year = 1940
aggregation_end_year = 2022
climate_data_source = 'historical' # 'historical' or 'projections'

# Set the years over which to calculate the mean climate variables used to estimate the capacity factors of wind and solar.
start_year_for_mean_climate_variable = 2000
end_year_for_mean_climate_variable = 2020

# Set the data source against which to compare the results. This is used only for the validation of wind and solar capacity factors.
validation_data_source = 'entsoe' # 'open_power_system_database' or 'era5' or 'entsoe'

# Decide whether to calibrate the results. The calibration is implemented for wind capacity factors and hydropower inflow time series.
calibration_folder = working_directory + '/calibration_results'
calibrate = False
if calibrate:
    if not os.path.exists(calibration_folder):
        os.mkdir(calibration_folder)

# Settings for wind resource.
offshore_wind_turbine = 'IEA_10MW_198_RWT.yaml'
onshore_wind_turbine = 'IEA_3.4MW_130_RWT.yaml'
read_wind_coefficients = True

# Settings for solar resource.
solar_panel = 'CSi'
read_solar_coefficients = True

# Settings for hydropower resource.
read_hydropower_coefficients = True

# Settings for heating demand.
heating_daily_temperature_threshold = 15.0

# Settings for cooling demand.
cooling_daily_temperature_threshold = 24.0
cooling_hourly_temperature_threshold = 28.0
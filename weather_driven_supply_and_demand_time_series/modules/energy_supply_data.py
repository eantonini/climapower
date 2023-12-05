import pandas as pd
import xarray as xr
import numpy as np

from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from modules.exceptions import NotEnoughDataError

import settings
import modules.directories as directories
import modules.general_utilities as general_utilities
import modules.energy_utilities as energy_utilities


# Define the ENTSO-E API key.
ENTSOE_API_KEY = '5c0f2faa-fde8-43fa-9b70-c89b4f37b868'


def get_entsoe_generation(country_info, year, generation_code, start=None, end=None, remove_outliers=True, add_all_missing_timesteps=True):
    '''
    Retrieve the generation time series and the total installed capacity from ENTSO-E.

    Source: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
    Source: https://github.com/EnergieID/entsoe-py

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    generation_code : str
        ENTSO-E generation code
    offshore : bool
        True if the resource of interest is offshore wind
    start : pandas.Timestamp, optional
        Specified start date of the data retrieval
    end : pandas.Timestamp, optional
        Specified end date of the data retrieval

    Returns
    -------
    entsoe_generation_time_series : pandas.Series
        Time series of the generation for the given year and country
    entsoe_total_installed_capacity : float
        Total installed capacity for the given year and country
    '''
    
    # Define the ENTSO-E API client.
    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

    # Define the start and end dates for the data retrieval.
    if start is None:
        start = pd.Timestamp(str(year), tz='UTC')
    if end is None:
        end = pd.Timestamp(str(year+1), tz='UTC')

    # Retrieve the generation time series.
    entsoe_generation_time_series = client.query_generation(country_info['ISO Alpha-2'], start=start, end=end, psr_type=generation_code)
    entsoe_generation_time_series = entsoe_generation_time_series.tz_convert(None)
    
    # If the generation time series is a DataFrame, keep only the first column.
    if isinstance(entsoe_generation_time_series, pd.DataFrame):
        print('ENTSO-E data is a Pandas DataFrame. ENTSO-E variable extracted:', entsoe_generation_time_series.iloc[:,0].name, '.')
        entsoe_generation_time_series = entsoe_generation_time_series.iloc[:,0]
    
    # Sanitize the generation time series.
    entsoe_generation_time_series = energy_utilities.sanitize_time_series(entsoe_generation_time_series, start, end, add_all_missing_timesteps=add_all_missing_timesteps)
    
    # If the generation time series has a higher temporal resolution than hourly, resample it to hourly.
    entsoe_generation_time_series = energy_utilities.resample_to_hourly(entsoe_generation_time_series)
    
    # Check and remove outliers if the time series has more than 2/3 of the values.
    if remove_outliers and entsoe_generation_time_series.notnull().sum() > len(entsoe_generation_time_series)*2/3:
        entsoe_generation_time_series = general_utilities.remove_outliers(entsoe_generation_time_series)
    
    return entsoe_generation_time_series


def get_entsoe_capacity(country_info, year, generation_code):
    '''
    Retrieve the total installed capacity from ENTSO-E.

    Source: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
    Source: https://github.com/EnergieID/entsoe-py

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    generation_code : str
        ENTSO-E generation code
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    entsoe_generation_time_series : pandas.Series
        Time series of the generation for the given year and country
    entsoe_total_installed_capacity : float
        Total installed capacity for the given year and country
    '''
    
    # Define the ENTSO-E API client.
    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

    # Define the start and end dates for the data retrieval.
    start = pd.Timestamp(str(year), tz='UTC')
    end = pd.Timestamp(str(year+1), tz='UTC')

    # Retrieve the total installed capacity.
    entsoe_total_installed_capacity = client.query_installed_generation_capacity(country_info['ISO Alpha-2'], start=start, end=end, psr_type=generation_code).squeeze()

    return entsoe_total_installed_capacity


def get_entsoe_reservoir_filling_level(country_info, year, start=None, end=None, remove_outliers=True, add_all_missing_timesteps=True):
    '''
    Retrieve the hydropower generation time series from ENTSO-E.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    start : pandas.Timestamp, optional
        Specified start date of the data retrieval
    end : pandas.Timestamp, optional
        Specified end date of the data retrieval
    
    Returns
    -------
    entsoe_hydropower_generation_time_series : pandas.Series
        Time series of the hydropower generation for the given year and country
    '''

    # Define the ENTSO-E API key client.
    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

    # Define the start and end dates for the data retrieval.
    if start is None:
        start = pd.Timestamp(str(year), tz='UTC')
    if end is None:
        end = pd.Timestamp(str(year+1), tz='UTC')

    # Retrieve the hydropower generation (MW) and reservoir filling level (MWh) time series.
    entsoe_reservoir_filling_level_time_series = client.query_aggregate_water_reservoirs_and_hydro_storage(country_info['ISO Alpha-2'], start=start, end=end)
    entsoe_reservoir_filling_level_time_series = entsoe_reservoir_filling_level_time_series.tz_convert(None)

    # If the time series is a DataFrame, keep only the first column.
    if isinstance(entsoe_reservoir_filling_level_time_series, pd.DataFrame):
        print('ENTSO-E data is a Pandas DataFrame. ENTSO-E variable extracted:', entsoe_reservoir_filling_level_time_series.iloc[:,0].name, '.')
        entsoe_reservoir_filling_level_time_series = entsoe_reservoir_filling_level_time_series.iloc[:,0]

    # Get a clean time index for the time series.
    entsoe_reservoir_filling_level_time_series.index = energy_utilities.get_weekly_time_index(entsoe_reservoir_filling_level_time_series, start, end, keep_missing_timesteps=True)
    
    # Sanitize the reservoir filling level time series.
    entsoe_reservoir_filling_level_time_series = energy_utilities.sanitize_time_series(entsoe_reservoir_filling_level_time_series, start, end, add_all_missing_timesteps=add_all_missing_timesteps)

    # Check and remove outliers if the time series has more than 2/3 of the values.
    if remove_outliers and entsoe_reservoir_filling_level_time_series.notnull().sum() > len(entsoe_reservoir_filling_level_time_series)*2/3:
        entsoe_reservoir_filling_level_time_series = general_utilities.remove_outliers(entsoe_reservoir_filling_level_time_series)

    return entsoe_reservoir_filling_level_time_series


def get_entsoe_hydropower_inflow(country_info, year):
    '''
    Retrieve the hydropower generation and reservoir filling level time series from ENTSO-E and compute the hydropower inflow time series.

    Source: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
    Source: https://github.com/EnergieID/entsoe-py
    Source: https://doi.org/10.1016/j.isci.2021.102999

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest

    Returns
    -------
    entsoe_hydropower_inflow_time_series : pandas.Series
        Time series of the hydropower inflow for the given year and country
    '''

    # Define the start and end dates for the data retrieval.
    # Extend the time period by 14 days to avoid missing values at the beginning and at the end of the year because hydropower reservoir filling level have weekly values.
    # The maximum retrival period is one year, so the time period is split in three parts: the week before the year of interest, the year of interest, and the week after the year of interest.
    start_previous_period = pd.Timestamp(str(year), tz='UTC') - pd.Timedelta(days=14)
    end_previous_period = pd.Timestamp(str(year), tz='UTC') + pd.Timedelta(days=7)
    start_year = pd.Timestamp(str(year), tz='UTC')
    end_year = pd.Timestamp(str(year+1), tz='UTC')
    start_following_period = pd.Timestamp(str(year+1), tz='UTC') - pd.Timedelta(days=7)
    end_following_period = pd.Timestamp(str(year+1), tz='UTC') + pd.Timedelta(days=14)

    # Set the ENTSO-E generation code.
    generation_code = 'B12' # B10 Hydro Pumped Storage, B11 Hydro Run-of-river and poundage, or B12 Hydro Water Reservoir

    # Retrieve the hydropower generation (MW) time series for the year of interest and a buffer of 2 weeks before and after.
    entsoe_hydropower_generation_time_series = get_entsoe_generation(country_info, year, generation_code)
    try:
        entsoe_hydropower_generation_time_series_previous_period = get_entsoe_generation(country_info, year, generation_code, start=start_previous_period, end=end_previous_period, add_all_missing_timesteps=False)
    except (NoMatchingDataError, NotEnoughDataError):
        print('No hydropower generation data available for the previous period')
        entsoe_hydropower_generation_time_series_previous_period = pd.Series(dtype=float)
    try:
        entsoe_hydropower_generation_time_series_next_period = get_entsoe_generation(country_info, year, generation_code, start=start_following_period, end=end_following_period, add_all_missing_timesteps=False)
    except (NoMatchingDataError, NotEnoughDataError):
        print('No hydropower generation data available for the next period')
        entsoe_hydropower_generation_time_series_next_period = pd.Series(dtype=float)

    # Combine the hydropower generation time series.
    entsoe_hydropower_generation_time_series = pd.concat([entsoe_hydropower_generation_time_series_previous_period, entsoe_hydropower_generation_time_series, entsoe_hydropower_generation_time_series_next_period])

    # Drop duplicate values.
    entsoe_hydropower_generation_time_series = entsoe_hydropower_generation_time_series[~entsoe_hydropower_generation_time_series.index.duplicated(keep='first')]

    # Downsample the hydropower generation time series to weekly resolution. Weekly bins start on Monday and end on Sunday. The label of the bins is set to the right bin edge.
    entsoe_weekly_hydropower_generation_time_series = entsoe_hydropower_generation_time_series.resample('1W').sum()

    # Adjust the ends of the time series.
    entsoe_weekly_hydropower_generation_time_series = energy_utilities.adjust_time_series_ends(entsoe_weekly_hydropower_generation_time_series, year, start_previous_period, start_year, end_year, end_following_period)

    # Retrieve the reservoir filling level (MWh) time series for the year of interest and a buffer of 2 weeks before and after.
    entsoe_reservoir_filling_level_time_series = get_entsoe_reservoir_filling_level(country_info, year, remove_outliers=False)
    try:
        entsoe_reservoir_filling_level_time_series_previous_period = get_entsoe_reservoir_filling_level(country_info, year, start=start_previous_period, end=end_previous_period, remove_outliers=False, add_all_missing_timesteps=False)
    except (NoMatchingDataError, NotEnoughDataError):
        print('No hydropower reservoir filling level data available for the previous period')
        entsoe_reservoir_filling_level_time_series_previous_period = pd.Series(dtype=float)
    try:
        entsoe_reservoir_filling_level_time_series_next_period = get_entsoe_reservoir_filling_level(country_info, year, start=start_following_period, end=end_following_period, remove_outliers=False, add_all_missing_timesteps=False)
    except (NoMatchingDataError, NotEnoughDataError):
        print('No hydropower reservoir filling level data available for the next period')
        entsoe_reservoir_filling_level_time_series_next_period = pd.Series(dtype=float)

    # Combine the reservoir filling level time series.
    entsoe_reservoir_filling_level_time_series = pd.concat([entsoe_reservoir_filling_level_time_series_previous_period, entsoe_reservoir_filling_level_time_series, entsoe_reservoir_filling_level_time_series_next_period])

    # Drop duplicate values.
    entsoe_reservoir_filling_level_time_series = entsoe_reservoir_filling_level_time_series[~entsoe_reservoir_filling_level_time_series.index.duplicated(keep='first')]

    # Adjust the ends of the time series.
    entsoe_reservoir_filling_level_time_series = energy_utilities.adjust_time_series_ends(entsoe_reservoir_filling_level_time_series, year, start_previous_period, start_year, end_year, end_following_period)

    # Calculate the hydropower inflow time series using an energy balance. The hydropower inflow is the difference between the reservoir filling level at the end of the week and the reservoir filling level at the beginning of the week plus the hydropower generation during the week.
    weekly_hydropower_inflow_time_series = entsoe_reservoir_filling_level_time_series[1:].values - entsoe_reservoir_filling_level_time_series[:-1].values + entsoe_weekly_hydropower_generation_time_series[:-1].values # type: ignore
    weekly_hydropower_inflow_time_series = pd.Series(data=weekly_hydropower_inflow_time_series, index=entsoe_weekly_hydropower_generation_time_series.index[:-1], name='Hydropower inflow')
    
    # Remove negative values.
    weekly_hydropower_inflow_time_series[weekly_hydropower_inflow_time_series<0] = 0

    # Keep only values where the index is in the current year.
    weekly_hydropower_inflow_time_series = weekly_hydropower_inflow_time_series[weekly_hydropower_inflow_time_series.index.year==year]

    return weekly_hydropower_inflow_time_series


def get_opsd_generation_and_capacity(country_info, year, resource_type, offshore=False, remove_outliers=True):
    '''
    Retrieve wind and solar generation time series and the total installed capacity from the Open Power System Database.

    Source: https://data.open-power-system-data.org/time_series/

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    resource_type : str
        Type of resource of interest ('wind' or 'solar')
    offshore : bool
        True if the resource of interest is offshore wind
    
    Returns
    -------
    opsd_generation_time_series : pandas.Series
        Time series of the generation for the given year and country
    opsd_total_installed_capacity : float
        Total installed capacity for the given year and country
    '''

    # Check if the resource type is implemented.
    if resource_type not in ['wind', 'solar']:
        raise AssertionError('Resource type not recognized or implemented')

    # Read the Open Power System Database.
    open_power_system_database_filename = settings.energy_data_directory+'/OPSD_time_series_60min_singleindex.csv'
    open_power_system_database = pd.read_csv(open_power_system_database_filename, parse_dates=True, index_col=0)

    # Remove the timezone from the index.
    open_power_system_database.index = open_power_system_database.index.tz_convert(None) # type: ignore

    # Keep only the generation time series for the given year and country.
    open_power_system_database = open_power_system_database[(open_power_system_database.index >= str(year)) & (open_power_system_database.index < str(year+1))]

    # Check if the generation time series is available for the given year and country.
    try:
        generation_column_name = country_info['ISO Alpha-2']+'_'+resource_type+'_'+('offshore_' if (resource_type == 'wind' and offshore) else ('onshore_' if (resource_type == 'wind' and not offshore) else ''))+'generation_actual'
        opsd_generation_time_series = open_power_system_database[generation_column_name]

        # Sanitize the generation time series.
        opsd_generation_time_series = energy_utilities.sanitize_time_series(opsd_generation_time_series, pd.Timestamp(str(year), tz='UTC'), pd.Timestamp(str(year+1), tz='UTC'))

        # Check and remove outliers if the time series has more than 2/3 of the values.
        if remove_outliers and opsd_generation_time_series.notnull().sum() > len(opsd_generation_time_series)*2/3:
            opsd_generation_time_series = general_utilities.remove_outliers(opsd_generation_time_series)
    
    except (KeyError, NotEnoughDataError):
        print('No OPSD ' + ('offshore ' if (resource_type == 'wind' and offshore) else ('onshore ' if (resource_type == 'wind' and not offshore) else '')) + resource_type + ' generation data available for the given year and country')
        opsd_generation_time_series = None
    
    # Check if the total installed capacity is available for the given year and country. 
    try:
        capacity_column_name = country_info['ISO Alpha-2']+'_'+resource_type+'_'+('offshore_' if (resource_type == 'wind' and offshore) else ('onshore_' if (resource_type == 'wind' and not offshore) else ''))+'capacity'
        opsd_total_installed_capacity = open_power_system_database[capacity_column_name]

    except (KeyError, NotEnoughDataError):
        print('No OPSD ' + ('offshore ' if (resource_type == 'wind' and offshore) else ('onshore ' if (resource_type == 'wind' and not offshore) else '')) + resource_type + ' capacity data available for the given year and country')
        opsd_total_installed_capacity = None
    
    return opsd_generation_time_series, opsd_total_installed_capacity


def get_ei_capacity(country_info, year, resource_type):
    '''
    Retrieve the total installed capacity from the Energy Institute Statistical Review of World Energy (previously BP Statistical Review of World Energy).

    Source: https://www.energyinst.org/statistical-review
    Source: https://www.bp.com/en/global/corporate/energy-economics/statistical-review-of-world-energy

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    resource_type : str
        Type of resource of interest ('wind' or 'solar')

    Returns
    -------
    ei_total_installed_capacity : float
        Total installed capacity for the given year and country
    '''

    # Check if the resource type is implemented.
    if resource_type not in ['wind', 'solar']:
        raise AssertionError('Resource type not recognized or implemented')
    
    # Read the Energy Institute Statistical Review of World Energy database.
    ei_energy_database_filename = settings.energy_data_directory+'/EI-stats-review-2023-all-data.xlsx'
    ei_energy_database = pd.read_excel(ei_energy_database_filename, sheet_name=resource_type.capitalize()+' Capacity', skiprows=2, header=1, nrows=66, usecols=np.arange(28))

    # Rename the columns and remove the rows with missing values.
    ei_energy_database = ei_energy_database.rename(columns={'Megawatts': 'Country'})
    ei_energy_database = ei_energy_database[~ei_energy_database['Country'].isnull()]
    ei_energy_database = ei_energy_database.fillna(0)

    # Remove the rows with the total capacity for the world and for the continents.
    ei_energy_database = ei_energy_database[~ei_energy_database['Country'].str.contains('Other')]
    ei_energy_database = ei_energy_database[~ei_energy_database['Country'].str.contains('Total')]

    # Extract the total installed capacity for the given year and country.
    ei_total_installed_capacity = (ei_energy_database[ei_energy_database['Country']==country_info['Name']][year].values)[0]

    return ei_total_installed_capacity


def get_era5_resource_time_series(country_info, year, resource_type, offshore=False):
    '''
    Retrieve the capacity factor time series calculated from the ERA5 reanalysis.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    resource_type : str
        Type of resource of interest ('wind', 'solar', or 'hydro')
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    era5_resource_time_series : pandas.Series
        Time series of the capacity factor for the given year and country
    '''
    
    # Define the variable name based on the resource type.
    if resource_type == 'wind':
        variable_name = 'wind'+('_offshore' if offshore else '_onshore')+'_capacity_factor'

    elif resource_type == 'solar':
        variable_name = 'solar_capacity_factor'

    elif resource_type == 'hydro':
        variable_name = 'hydropower_inflow'

    else:
        raise AssertionError('Resource type not recognized or implemented')

    # Open the ERA5 capacity factor time series.
    era5_resource_time_series = xr.open_dataset(directories.get_postprocessed_data_path(country_info, variable_name, climate_data_source='historical'))

    # Rename the variable.
    era5_resource_time_series = era5_resource_time_series['__xarray_dataarray_variable__'].to_series().rename('Capacity factor')

    # Keep only the time series for the given year.
    era5_resource_time_series = era5_resource_time_series.loc[pd.date_range(str(year), str(year+1), freq='H')[:-1]]
    
    return era5_resource_time_series


def get_actual_capacity_factor(country_info, year, resource_type, offshore=False):
    '''
    Retrieve the actual capacity factor time series for the given country and year.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    resource_type : str
        Type of resource of interest ('wind' or 'solar')
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    actual_capacity_factor_time_series : pandas.Series
        Time series of the capacity factor for the given year and country
    '''
    
    # Retrieve the actual capacity factor time series based on the data source.
    if settings.validation_data_source == 'entsoe':

        # Set the ENTSO-E generation code based on the resource type.
        if resource_type == 'wind':
            if offshore:
                generation_code = 'B18' # Offshore wind
            else:
                generation_code = 'B19' # Onshore wind

        elif resource_type == 'solar':
            generation_code = 'B16'

        else:
            raise AssertionError('Resource type not recognized or implemented')

        try:
            actual_generation_time_series = get_entsoe_generation(country_info, year, generation_code)
        except:
            print('ENTSO-E generation data retrieval failed')
        
        try:
            actual_total_installed_capacity = get_entsoe_capacity(country_info, year, generation_code)

            if actual_total_installed_capacity < actual_generation_time_series.max():

                print('ENTSO-E installed capacity is lower than the actual generation')

                try:
                    actual_total_installed_capacity = get_ei_capacity(country_info, year, resource_type)
                except:
                    print('EI capacity data retrieval failed')
                    actual_total_installed_capacity = actual_generation_time_series.max()*1.2
        except:
            print('ENTSO-E capacity data retrieval failed')

            try:
                actual_total_installed_capacity = get_ei_capacity(country_info, year, resource_type)
            except:
                print('EI capacity data retrieval failed')
                actual_total_installed_capacity = actual_generation_time_series.max()*1.2

        actual_capacity_factor_time_series = actual_generation_time_series/actual_total_installed_capacity

    elif settings.validation_data_source == 'open_power_system_database':

        actual_generation_time_series, actual_total_installed_capacity = get_opsd_generation_and_capacity(country_info, year, resource_type, offshore)

        if not isinstance(actual_total_installed_capacity, pd.Series):
            actual_total_installed_capacity = get_ei_capacity(country_info, year, resource_type)

        actual_capacity_factor_time_series = actual_generation_time_series/actual_total_installed_capacity

    elif settings.validation_data_source == 'era5':

        actual_capacity_factor_time_series = get_era5_resource_time_series(country_info, year, resource_type, offshore)

    else:

        raise AssertionError('Data source not recognized or implemented')

    # Rename the time series.
    actual_capacity_factor_time_series.name = 'Capacity factor'
    
    return actual_capacity_factor_time_series
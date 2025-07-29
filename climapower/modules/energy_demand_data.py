import numpy as np
import pandas as pd

import eurostat
from entsoe import EntsoePandasClient

import modules.general_utilities as general_utilities
import modules.energy_utilities as energy_utilities


# Define the ENTSO-E API key.
ENTSOE_API_KEY = 'your-api-key'


def get_entsoe_demand(country_info, year, start=None, end=None, remove_outliers=True, add_all_missing_timesteps=True):
    '''
    Retrieve the electricity demand time series in MW from ENTSO-E.

    Source: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
    Source: https://github.com/EnergieID/entsoe-py

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
    remove_outliers : bool, optional
        If True, remove outliers from the time series
    add_all_missing_timesteps : bool, optional
        If True, add all missing timesteps to the time series

    Returns
    -------
    entsoe_electricity_demand_time_series : pandas.Series
        Time series of the electricity demand in the given country and year
    '''
    
    # Define the ENTSO-E API client.
    client = EntsoePandasClient(api_key=ENTSOE_API_KEY)

    # Define the start and end dates for the data retrieval.
    if start is None:
        start = pd.Timestamp(str(year), tz='UTC')
    if end is None:
        end = pd.Timestamp(str(year+1), tz='UTC')

    # Retrieve the electricity demand time series.
    entsoe_electricity_demand_time_series = client.query_load(country_info['ISO Alpha-2'], start=start, end=end)
    entsoe_electricity_demand_time_series = entsoe_electricity_demand_time_series.tz_convert(None)
    
    # If the electricity demand time series is a DataFrame, keep only the first column.
    if isinstance(entsoe_electricity_demand_time_series, pd.DataFrame):
        print('ENTSO-E data is a Pandas DataFrame. ENTSO-E variable extracted:', entsoe_electricity_demand_time_series.iloc[:,0].name, '.')
        entsoe_electricity_demand_time_series = entsoe_electricity_demand_time_series.iloc[:,0]
    
    # Sanitize the electricity demand time series.
    entsoe_electricity_demand_time_series = energy_utilities.sanitize_time_series(entsoe_electricity_demand_time_series, start, end, add_all_missing_timesteps=add_all_missing_timesteps)
    
    # If the electricity demand time series has a higher temporal resolution than hourly, resample it to hourly.
    entsoe_electricity_demand_time_series = energy_utilities.resample_to_hourly(entsoe_electricity_demand_time_series)
    
    # Check and remove outliers if the time series has more than 2/3 of the values.
    if remove_outliers and entsoe_electricity_demand_time_series.notnull().sum() > len(entsoe_electricity_demand_time_series)*2/3:
        entsoe_electricity_demand_time_series = general_utilities.remove_outliers(entsoe_electricity_demand_time_series)
    
    return entsoe_electricity_demand_time_series


def get_eurostat_fraction_of_demand_in_application(country_info, year, application, siec_codes):
    '''
    Get the fraction of total demand that is used in the given application. The demand can be the total or electricity demand.
    This disaggregation is available only for the residential sectior. It can be assumed that the services sector has a similar disagregation.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    application : str
        Application of interest ('space heating', 'water heating', 'cooking', or 'space cooling')
    siec_codes : list of str
        List of SIEC codes of interest
        
    Returns
    -------
    fraction_of_demand_in_application : float
        Fraction of total demand that is used in the given application
    '''

    # Define the code for the Eurostat dataset "Disaggregated final energy consumption in households - quantities".
    eurostat_code = 'nrg_d_hhq'

    # Get the Eurostat database of the given code and select the given country and unit.
    eurostat_database = eurostat.get_data_df(eurostat_code).fillna(0)
    eurostat_database = eurostat_database[np.logical_and(eurostat_database['geo\TIME_PERIOD']==country_info['ISO Alpha-2'], eurostat_database['unit']=='TJ')]

    # Define the code for the target application.
    if application == 'space heating':
        # "Final consumption - other sectors - households - energy use - space heating"
        application_code = 'FC_OTH_HH_E_SH'
    elif application == 'water heating':
        # "Final consumption - other sectors - households - energy use - water heating"
        application_code = 'FC_OTH_HH_E_WH'
    elif application == 'cooking':
        # "Final consumption - other sectors - households - energy use - cooking"
        application_code = 'FC_OTH_HH_E_CK'
    elif application == 'space cooling':
        # "Final consumption - other sectors - households - energy use - space cooling"
        application_code = 'FC_OTH_HH_E_SC'
    
    # Get the total demand and the demand in the given application.
    total_annual_demand = 0
    annual_demand_in_application = 0
    for siec_code in siec_codes:
        total_annual_demand = total_annual_demand + eurostat_database[np.logical_and(eurostat_database['nrg_bal']=='FC_OTH_HH_E', eurostat_database['siec']==siec_code)][str(year)].values[0]
        annual_demand_in_application = annual_demand_in_application + eurostat_database[np.logical_and(eurostat_database['nrg_bal']==application_code, eurostat_database['siec']==siec_code)][str(year)].values[0]
    
    # Calculate the fraction of total demand that is used in the given application.
    fraction_of_demand_in_application = annual_demand_in_application/total_annual_demand
        
    return fraction_of_demand_in_application


def get_eurostat_building_demand(country_info, year, sector='all', application='all', carrier='all'):
    '''
    Get the annual electricity or heating demand for the building sector in TJ (residential and services sectors).

    Source: https://ec.europa.eu/eurostat/databrowser/explore/all/envir?lang=en&subtheme=nrg.nrg_quant.nrg_quanta&display=list&sort=category
    SIEC vocabulary: https://dd.eionet.europa.eu/vocabulary/eurostat/siec/view
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    sector : str
        Sector of interest ('all', 'residential' or 'services')
    application : str
        Application of interest ('all', 'space heating', 'water heating', 'cooking', or 'space cooling')
    carrier : str
        Carrier of interest ('all' or 'electricity')
    
    Returns
    -------
    building_annual_demand : float
        Annual demand for the building sector
    '''

    # Define the code for the Eurostat dataset "Complete energy balances".
    eurostat_code = 'nrg_bal_c'

    # Get the Eurostat database of the given code and select the given country and unit.
    eurostat_database = eurostat.get_data_df(eurostat_code).fillna(0)
    eurostat_database = eurostat_database[np.logical_and(eurostat_database['geo\TIME_PERIOD']==country_info['ISO Alpha-2'], eurostat_database['unit']=='TJ')]

    # Define the codes for the sector of interest.
    if sector == 'all':
        sector_codes = ['FC_OTH_HH_E', # "Final consumption - other sectors - households - energy use"
                        'FC_OTH_CP_E'] # "Final consumption - other sectors - commercial and public services - energy use"
    elif sector == 'residential':
        sector_codes = ['FC_OTH_HH_E'] # "Final consumption - other sectors - households - energy use"
    elif sector == 'services':
        sector_codes = ['FC_OTH_CP_E'] # "Final consumption - other sectors - commercial and public services - energy use"
    
    # Define the SIEC codes for the given carrier.
    if carrier == 'all':

        siec_codes = ['TOTAL']

    elif carrier == 'electricity':

        siec_codes = ['E7000', # 'Electricity'
                      'RA600'] # 'Ambient heat (heat pumps)'
    
    # Initialize the annual demand for the building sector.
    building_annual_demand = 0

    for sector_code in sector_codes:

        # Initialize the annual demand in the given sector.
        annual_demand_in_sector = 0

        # Get the annual demand in the given sector by looping over the SIEC codes.
        for siec_code in siec_codes:

            annual_demand_in_sector = annual_demand_in_sector + eurostat_database[np.logical_and(eurostat_database['nrg_bal']==sector_code, eurostat_database['siec']==siec_code)][str(year)].values[0]

        # If the application is not 'all', get the fraction of total demand that is used in the given application.
        if application != 'all':
            annual_demand_in_sector = annual_demand_in_sector * get_eurostat_fraction_of_demand_in_application(country_info, year, application, siec_codes)
    
        # Add the annual demand in the given sector to the total annual demand for the building sector.
        building_annual_demand = building_annual_demand + annual_demand_in_sector

    return building_annual_demand

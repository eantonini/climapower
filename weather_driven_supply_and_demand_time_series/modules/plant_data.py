import pandas as pd

import modules.settings as settings


def get_gem_plant_database(country_info, year, resource_type, offshore=False):
    '''
    Retrieve the power plant database for the given country and year from the Global Energy Monitor database.

    The Global Energy Monitor database includes:
    - wind farms with capacities of 10 or more,
    - solar farms with capacities of 20 megawatts or more,
    - hydroelectric power plants with capacities of 75 megawatts or more.

    Source: https://globalenergymonitor.org/

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
    plant_database : pandas.DataFrame
        Power plant database for the given country and year
    '''
    
    # Set the path of the plant database and the columns to read.
    if resource_type == 'wind':
        plant_database_filename = settings.energy_data_directory+'/Global-Wind-Power-Tracker-January-2023.xlsx'
        columns = ['Country', 'Project Name', 'Capacity (MW)', 'Installation Type', 'Status', 'Start year', 'Retired year', 'Latitude', 'Longitude', 'Subregion', 'Region']

    elif resource_type == 'solar':
        plant_database_filename = settings.energy_data_directory+'/Global-Solar-Power-Tracker-January-2023.xlsx'
        columns = ['Country', 'Project Name', 'Capacity (MW)', 'Technology Type', 'Status', 'Start year', 'Retired year', 'Latitude', 'Longitude', 'Subregion', 'Region']

    elif resource_type == 'hydro':
        plant_database_filename = settings.energy_data_directory+'/Global-Hydropower-Tracker-May-2023.xlsx'
        columns = ['Country1', 'Project Name', 'Capacity (MW)', 'Technology Type', 'Status', 'Start year', 'Retired year', 'Latitude', 'Longitude', 'Subregion 1', 'Region 1']

    else:
        raise AssertionError('Resource type not recognized or implemented')
    
    # Read the plant database according to the columns of interest.
    plant_database = pd.read_excel(plant_database_filename, sheet_name='Data', usecols=columns)
    plant_database = plant_database.rename(columns={'Longitude': 'x', 'Latitude': 'y'})

    # Select the rows that match the country of interest and where the status is 'operating'.
    plant_database = plant_database[plant_database['Country']==country_info['Name']]
    plant_database = plant_database[plant_database['Status']=='operating']

    # Select the rows that match the resource type of interest.
    if resource_type == 'wind':
        plant_database = plant_database[plant_database['Installation Type'] == ('offshore' if offshore else 'onshore')]
    elif resource_type == 'solar':
        plant_database = plant_database[plant_database['Technology Type'] == 'PV']
    
    # Select the rows that match the year of interest.
    plant_database = plant_database[(plant_database['Start year']<=year) | (plant_database['Start year'].isnull())]
    plant_database = plant_database[(plant_database['Retired year']>=year) | (plant_database['Retired year'].isnull())]
    
    return plant_database


def get_opsd_plant_database(country_info, year, resource_type, offshore=False):
    '''
    Retrieve the power plant database for the given country and year from the Open Power System Database.

    The database includes renewable power plants of Czechia, Denmark, France, Germany, Poland, Sweden, Switzerland and United Kingdom up to 2019.

    Source: https://data.open-power-system-data.org/renewable_power_plants/

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
    plant_database : pandas.DataFrame
        Power plant database for the given country and year
    '''

    # Read the Open Power System Database.
    plant_database_filename = settings.energy_data_directory+'/opsd-renewable_power_plants-2020-08-25/renewable_power_plants_'+country_info['ISO Alpha-2']+'.csv'
    columns = ['electrical_capacity', 'energy_source_level_2', 'technology', 'lon', 'lat', 'commissioning_date']

    # Read the plant database according to the columns of interest.
    plant_database = pd.read_csv(plant_database_filename, usecols=columns, engine='python')
    plant_database = plant_database.rename(columns={'electrical_capacity': 'Capacity (MW)', 'lon': 'x', 'lat': 'y'})
    
    # Select the rows that match the resource type of interest.
    if resource_type == 'wind':
        plant_database = plant_database[plant_database['energy_source_level_2'] == 'Wind']
        if offshore:
            plant_database = plant_database[plant_database['technology'] == 'Offshore']
        else:
            plant_database = plant_database[plant_database['technology'] != 'Offshore']
    elif resource_type == 'solar':
        plant_database = plant_database[plant_database['energy_source_level_2'] == 'Solar']

    # Set the missing commissioning dates with the beginning of the 20th century.
    plant_database['commissioning_date'] = plant_database['commissioning_date'].fillna('1900-01-01')

    # Convert the commissioning date to datetime.
    plant_database['commissioning_date'] = pd.to_datetime(plant_database['commissioning_date'])

    # Select the rows that match the year of interest.
    plant_database = plant_database[plant_database['commissioning_date']<=pd.to_datetime(str(year)+'-12-31')]

    # Convert the capacity and coordinate values to float.
    plant_database['Capacity (MW)'] = plant_database['Capacity (MW)'].astype(float)
    plant_database['x'] = plant_database['x'].astype(float)
    plant_database['y'] = plant_database['y'].astype(float)

    return plant_database
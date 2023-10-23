import modules.settings as settings


def get_climate_data_path(year, variable_name, CORDEX_time_resolution='3h'):
    '''
    Get full data path based on the year considered.

    Parameters
    ----------
    year : int
        Year of interest
    variable_name : str
        Name of the variable of interest
    CORDEX_time_resolution : str, optional
        Time resolution of the CORDEX data ('3h' or '6h')

    Returns
    -------
    climate_data_path : str
        Full data path with correct climate data filename
    '''
    
    climate_data_path = settings.climate_data_directory + '/'
                         
    if settings.climate_data_source == 'historical':
                              
        if settings.on_zeus:

            climate_data_path += (settings.dataset_info['historical_dataset'] + '-' +
                                  settings.dataset_info['focus_region'] + '-' +
                                  variable_name + '/')
            
        climate_data_path += (settings.dataset_info['historical_dataset'] + '-' +
                              '{:d}-gridded_'.format(year) + 'hourly_' + variable_name + '.nc')
    
    elif settings.climate_data_source == 'projections':
                              
        if settings.on_zeus:

            climate_data_path += (settings.dataset_info['future_dataset'] + '-' + 
                                  settings.dataset_info['focus_region'] + '-' +
                                  settings.dataset_info['representative_concentration_pathway'].upper() + '-' +
                                  settings.dataset_info['global_climate_model'].upper() + '-' +
                                  settings.dataset_info['regional_climate_model'].upper() + '-' +
                                  variable_name + '/')
        
        climate_data_path += (settings.dataset_info['future_dataset'] + '-' +
                              '{:d}-gridded_'.format(year) + CORDEX_time_resolution + '_' + variable_name + '.nc')
    
    return climate_data_path


def get_mean_climate_data_path(variable_name):
    '''
    Get full data path for the mean climate data.
    
    Parameters
    ----------
    variable_name : str
        Name of the variable of interest

    Returns
    -------
    mean_climate_data_path : str
        Full data path of mean climate data filename
    '''
    
    mean_climate_data_path = (settings.result_folder + '/' +
                              settings.dataset_info['historical_dataset'] + '-' +
                              settings.dataset_info['focus_region'] + '-' +
                              '{:d}-'.format(settings.start_year_for_mean_climate_variable) +
                              '{:d}'.format(settings.end_year_for_mean_climate_variable) + '-' +
                              'mean_' + variable_name + '.nc')
    
    return mean_climate_data_path


def get_tisr_path_for_cordex(year):
    '''
    Get full data path for the top-of-atmosphere (TOA) incident solar radiation for the given year.

    Parameters
    ----------
    year : int
        Year of interest
    
    Returns
    -------
    tisr_path_for_cordex : str
        Full data path of TOA incident solar radiation filename
    '''
    
    def isleap(year):
        '''Return True for leap years, False for non-leap years.'''
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    
    tisr_path_for_cordex = (settings.result_folder + '/' +
                            settings.dataset_info['historical_dataset'] + '-' +
                            settings.dataset_info['focus_region'] + '-')
    
    if isleap(year):
        tisr_path_for_cordex += 'toa_incident_solar_radiation_in_leap_year.nc'
    else:
        tisr_path_for_cordex += 'toa_incident_solar_radiation_in_non-leap_year.nc'

    return tisr_path_for_cordex


def get_postprocessed_data_path(country_info, variable_name, climate_data_source=None):
    '''
    Get full postprocessed data path based on the country and variable considered.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    variable_name : str
        Name of the variable of interest
    climate_data_source : str, optional
        Climate data source that can overwrite the default one set in settings.py
    
    Returns
    -------
    postprocessed_data_path : str
        Full postprocessed data filename
    '''

    if climate_data_source is None:
        climate_data_source = settings.climate_data_source
    
    postprocessed_data_path = settings.result_folder + '/'
    
    if climate_data_source == 'historical':
        
        postprocessed_data_path += settings.dataset_info['historical_dataset'] + '__'
    
    elif climate_data_source == 'projections':
        
        postprocessed_data_path += (settings.dataset_info['future_dataset'] + '__' +
                                    settings.dataset_info['representative_concentration_pathway'].upper() + '-' +
                                    settings.dataset_info['global_climate_model'].upper() + '-' +
                                    settings.dataset_info['regional_climate_model'].upper() + '__')
    
    postprocessed_data_path += country_info['ISO Alpha-2'] + '__' + variable_name + '.nc'
    
    return postprocessed_data_path


def get_calibration_coefficients_data_path(country_info, resource_type, additional_info=''):
    '''
    Get full data path of wind calibration coefficients based on the year.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    resource_type : str
        Type of resource of interest
    additional_info : str, optional
        Additional information to add to the filename

    Returns
    -------
    coefficients_data_path : str
        Full data path of calibration coefficients filename
    '''

    coefficients_data_path  = settings.calibration_folder + '/'

    if settings.climate_data_source == 'historical':

        coefficients_data_path += settings.dataset_info['historical_dataset'] + '-'

    elif settings.climate_data_source == 'projections':

        coefficients_data_path += settings.dataset_info['future_dataset'] + '-'
    
    else:

        raise AssertionError('The climate data source is not valid.')
    
    coefficients_data_path += country_info['ISO Alpha-2'] + '__' + resource_type + '__calibration_coefficients' + additional_info + '.csv'
    
    return coefficients_data_path
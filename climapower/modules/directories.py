import settings


def get_climate_data_path(year, variable_name, time_resolution='hourly', climate_data_source=None, return_folder=False,
                          representative_concentration_pathway=None, global_climate_model=None, regional_climate_model=None):
    '''
    Get full data path of the climate dataset.

    Parameters
    ----------
    year : int
        Year of interest
    variable_name : str
        Name of the variable of interest
    time_resolution : str, optional
        Time resolution of the data ('hourly' for ERA5 data, and '3hourly' or '6hourly' for CORDEX data)
    climate_data_source : str, optional
        Climate data source that can overwrite the default one set in settings.py
    return_folder : bool, optional
        Whether to return the folder or not

    Returns
    -------
    climate_data_path : str
        Full data path with correct climate data filename
    '''
    
    # Initialize the climate data path.
    climate_data_path = settings.climate_data_directory + '/'

    # Check whether to assign a custom climate data source.
    if climate_data_source is None:
        climate_data_source = settings.climate_data_source
    else:
        assert climate_data_source in ['reanalysis', 'projections'], 'The climate data source is not valid.'
    
    # Get the full data path.
    if climate_data_source == 'reanalysis':
                              
        if settings.on_hpc:

            climate_data_path += (settings.dataset_info['reanalysis_dataset'] + '__' +
                                  settings.dataset_info['focus_region'] + '__'
                                  + variable_name + '/')
            
        if return_folder:
            return climate_data_path
    
    elif climate_data_source == 'projections':
                              
        if settings.on_hpc:

            if representative_concentration_pathway is None:
                representative_concentration_pathway = settings.CORDEX_experiment_and_models['representative_concentration_pathway']
            else:
                assert representative_concentration_pathway in ['rcp_2_6', 'rcp_4_5', 'rcp_8_5'], 'The RCP is not valid.'
            
            if global_climate_model is None:
                global_climate_model = settings.CORDEX_experiment_and_models['global_climate_model']
            else:
                assert global_climate_model in ['cnrm_cerfacs_cm5', 'mpi_m_mpi_esm_lr', 'miroc_miroc5'], 'The global climate model is not valid.'
            
            if regional_climate_model is None:
                regional_climate_model = settings.CORDEX_experiment_and_models['regional_climate_model']
            else:
                assert regional_climate_model in ['cnrm_aladin63', 'ictp_regcm4_6', 'clmcom_clm_cclm4_8_17'], 'The regional climate model is not valid.'

            climate_data_path += (settings.dataset_info['projection_dataset'] + '__' +
                                  settings.dataset_info['focus_region'] + '__' +
                                  representative_concentration_pathway.upper() + '__' +
                                  global_climate_model.upper() + '__' +
                                  regional_climate_model.upper() + '__' +
                                  variable_name + '/')
            
        if return_folder:
            return climate_data_path
        
    climate_data_path += ('{:d}__'.format(year) + time_resolution + '_' + variable_name + '.nc')
    
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
    
    mean_climate_data_path = (settings.climate_data_directory + '/' +
                              settings.dataset_info['reanalysis_dataset'] + '__' +
                              settings.dataset_info['focus_region'] + '__' +
                              '{:d}_'.format(settings.start_year_for_mean_climate_variable) +
                              '{:d}'.format(settings.end_year_for_mean_climate_variable) + '__' +
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
    
    
    tisr_path_for_cordex = (settings.climate_data_directory + '/' +
                            settings.dataset_info['reanalysis_dataset'] + '__' +
                            settings.dataset_info['focus_region'] + '__')
    
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
    
    postprocessed_data_path = settings.result_folder + '/' + country_info['ISO Alpha-2'] + '__'
    
    if climate_data_source == 'reanalysis':
        
        postprocessed_data_path += settings.dataset_info['reanalysis_dataset'] + '__'
    
    elif climate_data_source == 'projections':
        
        postprocessed_data_path += (settings.dataset_info['projection_dataset'] + '__' +
                                    settings.CORDEX_experiment_and_models['representative_concentration_pathway'].upper() + '__' +
                                    settings.CORDEX_experiment_and_models['global_climate_model'].upper() + '__' +
                                    settings.CORDEX_experiment_and_models['regional_climate_model'].upper() + '__')
    
    postprocessed_data_path += variable_name + '.nc'
    
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

    coefficients_data_path  = settings.calibration_folder + '/' + country_info['ISO Alpha-2'] + '__'

    if settings.climate_data_source == 'reanalysis':

        coefficients_data_path += settings.dataset_info['reanalysis_dataset'] + '__'

    elif settings.climate_data_source == 'projections':

        coefficients_data_path += (settings.dataset_info['projection_dataset'] + '__RCP_2_6__' +
                                   settings.CORDEX_experiment_and_models['global_climate_model'].upper() + '__' +
                                   settings.CORDEX_experiment_and_models['regional_climate_model'].upper() + '__')
    
    else:

        raise AssertionError('The climate data source is not valid.')
    
    coefficients_data_path += resource_type + '__calibration_coefficients' + additional_info + '.csv'
    
    return coefficients_data_path
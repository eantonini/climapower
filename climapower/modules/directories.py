import settings


def get_climate_data_path(year, variable_name, return_folder=False, time_resolution='hourly', climate_data_source=None, focus_region=None,
                          representative_concentration_pathway=None, global_climate_model=None, regional_climate_model=None,
                          shared_socioeconomic_pathway=None, climate_model=None):
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
    representative_concentration_pathway : str, optional
        Representative concentration pathway (RCP) for CORDEX data
    global_climate_model : str, optional
        Global climate model for CORDEX data
    regional_climate_model : str, optional
        Regional climate model for CORDEX data
    shared_socioeconomic_pathway : str, optional
        Shared socioeconomic pathway (SSP) for CMIP6 data
    climate_model : str, optional
        Climate model for CMIP6 data

    Returns
    -------
    climate_data_path : str
        Full data path with correct climate data filename
    '''
    
    # Initialize the climate data path.
    climate_data_path = settings.climate_data_directory + '/'

    # Check whether to assign a custom focus region.
    if focus_region is None:
        region = settings.focus_region
    else:
        region = focus_region

    # Check whether to assign a custom climate data source.
    if climate_data_source is None:

        climate_data_source = settings.climate_data_source

        # Define the folder where the climate data are or will be stored.
        climate_data_folder = region + '__' + settings.data_product + '__'

    else:

        assert climate_data_source in ['reanalysis', 'CORDEX_projections', 'CMIP6_projections'], 'The climate data source is not valid.'
        
        if climate_data_source == 'reanalysis':
            data_product = 'ERA5'
        elif climate_data_source == 'CORDEX_projections':
            data_product = 'CORDEX'
        elif climate_data_source == 'CMIP6_projections':
            data_product = 'CMIP6'
    
        # Define the folder where the climate data are or will be stored.
        climate_data_folder = region + '__' + data_product + '__'

    if climate_data_source == 'CORDEX_projections':
                              
        # Check if the CORDEX experiment and models are set.
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

        # Add the CORDEX experiment and models to the folder name.
        climate_data_folder += representative_concentration_pathway.upper() + '__' + global_climate_model.upper() + '__' + regional_climate_model.upper() + '__'
    
    elif climate_data_source == 'CMIP6_projections':

        # Check if the CMIP6 experiment and model are set.
        if shared_socioeconomic_pathway is None:
            shared_socioeconomic_pathway = settings.CMIP6_experiment_and_model['shared_socioeconomic_pathway']
        else:
            assert shared_socioeconomic_pathway in ['ssp1_2_6', 'ssp2_4_5', 'ssp5_8_5'], 'The SSP is not valid.'
            
        if climate_model is None:
            climate_model = settings.CMIP6_experiment_and_model['climate_model']
        else:
            assert climate_model in ['mpi_esm1_2_lr', 'cmcc_esm2', 'cesm2', 'hadgem3_gc31_ll', 'bcc_csm2_mr'], 'The climate model is not valid.'
        
        # Add the CMIP6 experiment and model to the folder name.
        climate_data_folder += shared_socioeconomic_pathway.upper() + '__' + climate_model.upper() + '__'
    
    # Add the variable name to the folder name.
    climate_data_folder += variable_name + '/'

    # On the HPC, add the new folder to the climate data path.
    if settings.on_hpc:        
        climate_data_path = climate_data_path + climate_data_folder
    
    # If only the full folder path if wanted.
    if return_folder:
        return climate_data_path

    # Add the filename to the full folder path.
    climate_data_path += '{:d}__'.format(year) + time_resolution + '_' + variable_name + '.nc'
    
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
                              settings.focus_region + '__' +
                              settings.data_product + '__' +
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
                            settings.focus_region + '__' +
                            settings.data_product + '__')
    
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
    
    postprocessed_data_path = settings.result_folder + '/' + country_info['ISO Alpha-2'] + '__' + settings.data_product + '__'
    
    if climate_data_source == 'CORDEX_projections':
        
        postprocessed_data_path += (settings.CORDEX_experiment_and_models['representative_concentration_pathway'].upper() + '__' +
                                    settings.CORDEX_experiment_and_models['global_climate_model'].upper() + '__' +
                                    settings.CORDEX_experiment_and_models['regional_climate_model'].upper() + '__')
    
    elif climate_data_source == 'CMIP6_projections':

        postprocessed_data_path += (settings.CMIP6_experiment_and_model['shared_socioeconomic_pathway'].upper() + '__' +
                                    settings.CMIP6_experiment_and_model['climate_model'].upper() + '__')
    
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

        coefficients_data_path += settings.data_product + '__'

    elif settings.climate_data_source == 'CORDEX_projections':

        coefficients_data_path += (settings.data_product + '__RCP_2_6__' +
                                   settings.CORDEX_experiment_and_models['global_climate_model'].upper() + '__' +
                                   settings.CORDEX_experiment_and_models['regional_climate_model'].upper() + '__')
    
    else:

        raise AssertionError('The climate data source is not valid.')
    
    coefficients_data_path += resource_type + '__calibration_coefficients' + additional_info + '.csv'
    
    return coefficients_data_path
import atlite

import modules.settings as settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.geospatial_utilities as geospatial_utilities
import modules.validation_utilities as validation_utilities
import modules.climate_data as climate_data


def get_wind_capacity_factor_time_series(country_info, region_shape, year, offshore, alpha=1.0, beta=0.0):
    '''
    Read the climate data of the given year and convert them to the wind capacity factor time series for the given country.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    offshore : bool
        True if the resource/demand of interest is offshore
    alpha : float
        Calibration coefficient for the wind resource
    beta : float
        Calibration coefficient for the wind resource

    Returns
    -------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the wind capacity factor for the given year and country
    '''
    
    # Get the wind database for the given year and region.
    wind_database = climate_data.get_wind_database(year, region_shape)
        
    # Get wind turbine data from atlite.
    if offshore:
        turbine = atlite.resource.get_windturbineconfig(settings.offshore_wind_turbine)
    else:
        turbine = atlite.resource.get_windturbineconfig(settings.onshore_wind_turbine)
    
    # Read the wind calibration coefficients.
    if settings.read_wind_coefficients: 
        coefficients = validation_utilities.read_calibration_coefficients(country_info, 'wind', offshore=offshore)
        alpha = coefficients.loc['alpha']
        beta = coefficients.loc['beta']
    
    # Get wind speed data, interpolate to turbine hub height and convert to power.
    time_series = atlite.convert.convert_wind(wind_database, turbine, alpha, beta) # type: ignore

    return time_series


def compute_aggregated_wind_capacity_factor(country_info, offshore):
    '''
    Compute and save the aggregated capacity factor for the given country and for all the years in the time period of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    offshore : bool
        True if the resource of interest is offshore (used for wind resource)
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info, offshore)

    # Calculate the weights used to aggregate the time series (longitude x latitude).
    weights = geospatial_utilities.get_weights_for_wind_or_solar_aggregation(country_info, 'wind', offshore)
    
    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Calculate the time series of the capacity factor of the resource of interest for the given year and country.
        capacity_factor_time_series = get_wind_capacity_factor_time_series(country_info, region_shape, year, offshore)
        
        # Calculate the aggregated capacity factor.
        aggregated_capacity_factor = general_utilities.aggregate_time_series(capacity_factor_time_series, weights)

        # Add name and attributes to the aggregated time series.
        aggregated_capacity_factor = aggregated_capacity_factor.rename(('Offshore' if offshore else 'Onshore')+' wind capacity factor')
        aggregated_capacity_factor = aggregated_capacity_factor.assign_attrs(units='kW/kWi', description=('Offshore' if offshore else 'Onshore')+' wind capacity factor')
        
        # Save the aggregated capacity factor.
        general_utilities.save_time_series(aggregated_capacity_factor, country_info, 'wind__capacity_factor_time_series__'+('offshore' if offshore else 'onshore'))
import atlite

import modules.settings as settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.geospatial_utilities as geospatial_utilities
import modules.validation_utilities as validation_utilities
import modules.climate_data as climate_data


def get_solar_capacity_factor_time_series(country_info, region_shape, year, alpha=1.0, beta=0.0):
    '''
    Read the climate data of the given year and convert them to the solar capacity factor time series for the given country.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    alpha : float
        Calibration coefficient for the solar resource
    beta : float
        Calibration coefficient for the solar resource
    
    Returns
    -------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the solar capacity factor for the given year and country
    '''
    
    # Get the solar database for the given year and region.
    solar_database = climate_data.get_solar_database(year, region_shape)
    
    # Get solar panel data from atlite and set orientation.
    panel = atlite.resource.get_solarpanelconfig('CSi')
    orientation = 'latitude_optimal' # {'slope': 30.0, 'azimuth': 180.0}
    orientation = atlite.pv.orientation.get_orientation(orientation) # type: ignore

    # Convert climate data to power.
    time_series = atlite.convert.convert_pv(solar_database, panel, orientation, clearsky_model='simple') # type: ignore

    # Read the solar calibration coefficients.
    if settings.read_solar_coefficients: 
        coefficients = validation_utilities.read_calibration_coefficients(country_info, 'solar')
        alpha = coefficients.loc['alpha']
        beta = coefficients.loc['beta']

    # Apply calibration coefficients where the time series is not zero.
    time_series = time_series.where(time_series < 0.0001, alpha * time_series + beta)

    # Remove negative values.
    time_series = time_series.where(time_series > 0.0, 0.0)

    return time_series


def compute_aggregated_solar_capacity_factor(country_info):
    '''
    Compute and save the aggregated solar capacity factor for the given country and for all the years in the time period of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Calculate the weights used to aggregate the time series (longitude x latitude).
    weights = geospatial_utilities.get_weights_for_wind_or_solar_aggregation(country_info, 'solar')
    
    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Calculate the time series of the capacity factor of the resource of interest for the given year and country.
        capacity_factor_time_series = get_solar_capacity_factor_time_series(country_info, region_shape, year)
        
        # Calculate the aggregated capacity factor.
        aggregated_capacity_factor = general_utilities.aggregate_time_series(capacity_factor_time_series, weights)

        # Add name and attributes to the aggregated time series.
        aggregated_capacity_factor = aggregated_capacity_factor.rename('Solar capacity factor')
        aggregated_capacity_factor = aggregated_capacity_factor.assign_attrs(units='kW/kWi', description='Solar capacity factor')
        
        # Save the aggregated capacity factor.
        general_utilities.save_time_series(aggregated_capacity_factor, country_info, 'solar__capacity_factor_time_series')
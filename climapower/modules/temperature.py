import xarray as xr

import settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.climate_data as climate_data


def compute_aggregated_temperature(country_info):
    '''
    Compute the aggregated temperature for the given country and for all the years in the time period of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Get the temperature database for the given year and region.
        temperature_time_series = climate_data.get_temperature_database(year, region_shape)
        
        # Set the weights to 1 for aggregating the time series.
        weights = xr.ones_like(temperature_time_series.mean(dim='time'))

        # Aggregate the time series of the heating demand.
        aggregated_temperature_time_series = general_utilities.aggregate_time_series(temperature_time_series, weights)

        # Add name and attributes to the aggregated time series.
        aggregated_temperature_time_series = aggregated_temperature_time_series.rename('Temperature')
        aggregated_temperature_time_series = aggregated_temperature_time_series.assign_attrs(units='K', description='Temperature')
    
        # Save the aggregated time series of the heating demand.
        general_utilities.save_time_series(aggregated_temperature_time_series, country_info, 'temperature__time_series')
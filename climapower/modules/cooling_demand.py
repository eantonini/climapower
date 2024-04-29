import pandas as pd

import atlite

import settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.geospatial_utilities as geospatial_utilities
import modules.climate_data as climate_data


def get_cooling_demand_time_series(region_shape, year, threshold, hour_shift=0.0, hourly_series=False):
    '''
    Read the climate data of a given year and convert them to the cooling demand time series for the given country.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    threshold : float
        Threshold temperature for the time series
    hour_shift : float
        Number of hours to shift the time series
    hourly_series : bool
        True if the time series should be hourly
    
    Returns
    -------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the cooling demand for the given year and country
    '''
    
    # Get the temperature database for the given year and region.
    temperature_database = climate_data.get_temperature_database(year, region_shape)

    # Convert the temperature database to the cooling demand time series.
    time_series = atlite.convert.convert_heat_demand(temperature_database, threshold=threshold, a=1.0, constant=0.0, hour_shift=hour_shift, cooling=True, hourly_series=hourly_series)
        
    return time_series


def compute_aggregated_cooling_demand(country_info):
    '''
    Compute the aggregated cooling demand for the given country and for all the years in the time period of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Get the population density of the country of interest mapped to the grid cells in the bounding box of the country of interest
    weights = geospatial_utilities.get_population_density(country_info)

    # Calculate the time shift between UTC and the country time zone
    hour_shift = general_utilities.calculate_hour_shift(country_info)

    # Define a reference year for which we have total cooling demand data in kWh/year.
    reference_year = 2015

    # Calculate the time series of the cooling demand for the reference year and country. The time series has daily mean values and daily resolution.
    reference_daily_cooling_demand_time_series = get_cooling_demand_time_series(region_shape, reference_year, settings.cooling_daily_temperature_threshold, hour_shift=hour_shift)

    # Select the days in the reference year. Typically there is one extra day in the time series, so we remove it.
    reference_daily_cooling_demand_time_series = reference_daily_cooling_demand_time_series.sel(time=pd.date_range(str(reference_year), str(reference_year+1), freq='D')[:-1])

    # Aggregate the time series of the cooling demand for the reference year.
    reference_aggregated_daily_cooling_demand_time_series = general_utilities.aggregate_time_series(reference_daily_cooling_demand_time_series, weights)

    # Calculate the total cooling degree days in the reference year.
    reference_cooling_degree_days = float(reference_aggregated_daily_cooling_demand_time_series.sum(dim='time'))

    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Calculate the time series of the cooling demand for the given year and country. The time series has daily mean values and daily resolution.
        daily_cooling_demand_time_series = get_cooling_demand_time_series(region_shape, year, settings.cooling_daily_temperature_threshold, hour_shift=hour_shift)

        # Select the days in the given year. Typically there is one extra day in the time series, so we remove it.
        daily_cooling_demand_time_series = daily_cooling_demand_time_series.sel(time=pd.date_range(str(year), str(year+1), freq='D')[:-1])

        # Aggregate the time series of the cooling demand.
        aggregated_daily_cooling_demand_time_series = general_utilities.aggregate_time_series(daily_cooling_demand_time_series, weights)

        # Calculate the total cooling degree days in the given year.
        cooling_degree_days = float(aggregated_daily_cooling_demand_time_series.sum(dim='time'))

        # Calculate the interannual change in the cooling degree days.
        interannual_change = cooling_degree_days / reference_cooling_degree_days

        # Filter the time series of the cooling demand such that it is 0 or 1 (no cooling or cooling). Then upsample it to hourly resolution.
        cooling_switch = daily_cooling_demand_time_series.where(daily_cooling_demand_time_series==0, 1)
        cooling_switch = cooling_switch.reindex(time=pd.date_range(str(year), str(year+1), freq='H')[:-1], method='ffill')
        
        # Calculate the hourly time series of the cooling demand.
        hourly_cooling_demand_time_series = get_cooling_demand_time_series(region_shape, year, settings.cooling_hourly_temperature_threshold, hourly_series=True)
        hourly_cooling_demand_time_series = hourly_cooling_demand_time_series*cooling_switch

        # Calculate the aggregated hourly time series of the cooling demand.
        aggregated_hourly_cooling_demand_time_series = general_utilities.aggregate_time_series(hourly_cooling_demand_time_series, weights)

        # Smooth the time series of the cooling demand with a moving average filter.
        aggregated_hourly_cooling_demand_time_series = aggregated_hourly_cooling_demand_time_series.rolling(time=3, center=True, min_periods=1).mean()
        
        # Normalize the time series of the cooling demand and multiply it by the interannual change in the cooling degree days.
        aggregated_cooling_demand = aggregated_hourly_cooling_demand_time_series / aggregated_hourly_cooling_demand_time_series.sum() * interannual_change

        # Add name and attributes to the aggregated time series.
        aggregated_cooling_demand = aggregated_cooling_demand.rename('Cooling demand')
        aggregated_cooling_demand = aggregated_cooling_demand.assign_attrs(units='kW/kWh', description='Cooling demand per unit of total annual cooling demand')
        
        # Save the aggregated time series of the cooling demand.
        general_utilities.save_time_series(aggregated_cooling_demand, country_info, 'cooling__demand_time_series')
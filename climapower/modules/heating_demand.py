import numpy as np
import pandas as pd
import xarray as xr
import pytz

import atlite

import settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.geospatial_utilities as geospatial_utilities
import modules.climate_data as climate_data


def get_heating_demand_time_series(region_shape, year, threshold, hour_shift=0.0):
    '''
    Read the climate data of a given year and convert them to the heating demand time series for the given country.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    hour_shift : float
        Number of hours to shift the time series
    threshold : float
        Threshold temperature for the time series

    Returns
    -------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the heating demand for the given year and country
    '''
    
    # Get the temperature database for the given year and region.
    temperature_database = climate_data.get_temperature_database(year, region_shape)

    # Convert the temperature database to the heating demand time series.
    time_series = atlite.convert.convert_heat_demand(temperature_database, threshold=threshold, a=1.0, constant=0.0, hour_shift=hour_shift)
    
    return time_series


def get_intraday_heating_profile(country_info, year, sector, use, method='hourly_dependent', weights=None):
    '''
    Get the intraday profile of the heating demand for the given country.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    sector : str
        Sector of the heating demand
    use : str
        Use of the heating demand
    method : str
        Method to calculate the intraday profile of the heating demand
    weights : xarray.DataArray
        Weights to aggregate the temperature time series
    
    Returns
    -------
    hourly_intraday_profile : pandas.Series
        Hourly intraday profile of the heating demand for the given country
    '''

    # Get the country time zone.
    if country_info['Name'] == 'Kosovo':
        country_timezone = pytz.timezone('Europe/Belgrade')
    else:
        country_timezone = pytz.timezone(pytz.country_timezones[country_info['ISO Alpha-2']][0])

    # Create a pandas DatetimeIndex with the hours of the year.
    time_index_of_year = pd.date_range(str(year), str(year+1), freq='h')[:-1]

    # Extract the time periods, assign them the UTC time zone, and convert them to the country time zone.
    time_index_of_year_to_local_zone = time_index_of_year.tz_localize('UTC').tz_convert(country_timezone)

    # Calculate the time shift between UTC and the country time zone.
    hour_shift = general_utilities.calculate_hour_shift(country_info)

    if method == 'hourly_dependent':

        # From PyPSA-Eur / Atlite

        intraday_profiles = pd.read_csv(settings.energy_data_directory+'/heat_load_profile_BDEW.csv', index_col=0)

        # Create lists with the intraday profile (24 elements) of the heating demand for the given sector and use. The intraday profile is different for weekdays and weekends.
        weekday = list(intraday_profiles[f'{sector} {use} weekday'])
        weekend = list(intraday_profiles[f'{sector} {use} weekend'])

        # Combine the intraday profiles of the heating demand for the given sector and use into a single weekly profile (24 x 7 elements). Then convert it to a pandas Series.
        weekly_profile = weekday * 5 + weekend * 2
        weekly_profile = pd.Series(weekly_profile, index=np.arange(24 * 7))

        # Assign to each hour in the time index the corresponding number of the hour in the week (from 0 to 167, 12am Monday to 11pm Sunday).
        hour_of_the_week = pd.Series(data=[24 * dt.weekday() + dt.hour for dt in time_index_of_year_to_local_zone], index=time_index_of_year)

        # Map the hour of the week to the intraday profile of the heating demand.
        hourly_intraday_profile  = hour_of_the_week.map(weekly_profile)
    
    elif method == 'hourly_and_temperature_dependent':
        
        # From https://doi.org/10.1038/s41597-019-0199-y

        # Get the shape of the region of interest.
        region_shape = geometry.get_geopandas_region(country_info)

        # Get the temperature database for the given year and region.
        temperature_time_series = climate_data.get_temperature_database(year, region_shape)['temperature']

        # Aggregate the temperature time series by population density.
        aggregated_temperature_time_series = general_utilities.aggregate_time_series(temperature_time_series, weights)

        # Resample the temperature time series to daily mean values.
        dayly_aggregated_temperature_time_series = aggregated_temperature_time_series.resample(time='D', offset=pd.Timedelta(hour_shift, 'h')).mean()

        # Assign to each day a temperature class among the following: -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, where the temperature class is the closest multiple of 5 to the daily mean temperature.
        temperature_class = (np.round((dayly_aggregated_temperature_time_series - 273.15).clip(-15, 30) / 5) * 5).astype(int).astype(str)

        # Upsample the temperature class to hourly resolution.
        temperature_class = temperature_class.reindex(time=time_index_of_year, method='ffill')

        if sector == 'residential':

            # Read the intraday profiles of the heating demand for the given country and for the residential sector.
            intraday_profiles_SFH = pd.read_csv(settings.energy_data_directory+'/hourly_factors_SFH.csv', sep=';', decimal=',', index_col=0)
            intraday_profiles_MFH = pd.read_csv(settings.energy_data_directory+'/hourly_factors_MFH.csv', sep=';', decimal=',', index_col=0)

            # Average the intraday profiles of the single-family houses (SFH) and multi-family houses (MFH).
            intraday_profiles = 0.5 * (intraday_profiles_SFH + intraday_profiles_MFH)

            # Normalize each column of the intraday profiles of the heating demand.
            intraday_profiles = intraday_profiles / intraday_profiles.mean()

            # Reset the index of the intraday profiles.
            intraday_profiles = intraday_profiles.set_index(np.arange(0, 24))

            # Get the hour of the day.
            hour_of_the_day = [dt.hour for dt in time_index_of_year_to_local_zone]
        
            # Create a pandas Series with the intraday profile of the heating demand for the given temperature class. This concatenates the intraday profiles of the heating demand for the different dayly temperature classes.
            hourly_intraday_profile = pd.Series([intraday_profiles.loc[id1,id2] for id1, id2 in zip(hour_of_the_day, temperature_class.values)], index=time_index_of_year)
        
        elif sector == 'services':

            # Read the intraday profiles of the heating demand for the given country and for the services sector.
            intraday_profiles = pd.read_csv(settings.energy_data_directory+'/hourly_factors_COM.csv', sep=';', decimal=',', index_col=[0,1])

            # Normalize each column of the intraday profiles of the heating demand.
            intraday_profiles = intraday_profiles / intraday_profiles.mean()

            # Reset the index of the intraday profiles. The index is a MultiIndex with day of week and hour of the day.
            intraday_profiles = intraday_profiles.set_index(np.arange(0, 24 * 7))

            # Get the hour of the week.
            hour_of_the_week = [24 * dt.weekday() + dt.hour for dt in time_index_of_year_to_local_zone]

            # Create a pandas Series with the intraday profile of the heating demand for the given temperature class and day of the week. This concatenates the intraday profiles of the heating demand for the different dayly temperature classes and days of the week.
            hourly_intraday_profile = pd.Series([intraday_profiles.loc[id1,id2] for id1, id2 in zip(hour_of_the_week, temperature_class.values)], index=time_index_of_year)

    return hourly_intraday_profile


def get_hourly_heating_intraday_profile(country_info, year, method='hourly_dependent', weights=None):
    '''
    Get the intraday profile of the heating demand for the given country.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    method : str
        Method to calculate the intraday profile of the heating demand
    weights : xarray.DataArray
        Weights to aggregate the temperature time series

    Returns
    -------
    intraday_year_profiles : pandas.DataFrame
        Hourly intraday profile of the heating demand for the given country
    '''
    
    # Define the sectors and uses of the heating demand.
    sectors = ['residential', 'services']
    uses = ['space']

    # Create an empty xarray dataset to store the intraday profiles of the heating demand.
    hourly_intraday_profiles = xr.Dataset(coords={'time': pd.date_range(str(year), str(year+1), freq='h')[:-1]})

    for sector in sectors:
        for use in uses:

            # Get the intraday profiles of the heating demand for the given country.
            hourly_intraday_profiles[f'{sector}_{use}'] = get_intraday_heating_profile(country_info, year, sector, use, method=method, weights=weights).to_xarray()
    
    return hourly_intraday_profiles


def compute_aggregated_heating_demand(country_info):
    '''
    Compute the aggregated space heating demand for the given country and for all the years in the time period of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Get the population density of the country of interest mapped to the grid cells in the bounding box of the country of interest.
    weights = geospatial_utilities.get_population_density(country_info)

    # Calculate the time shift between UTC and the country time zone.
    hour_shift = general_utilities.calculate_hour_shift(country_info)

    # Define a reference year for which we have total heating demand data in kWh/year.
    reference_year = 2015

    # Calculate the time series of the heating demand for the reference year and country. The time series has daily mean values and daily resolution.
    reference_daily_heating_demand_time_series = get_heating_demand_time_series(region_shape, reference_year, settings.heating_daily_temperature_threshold, hour_shift=hour_shift)

    # Aggregate the time series of the heating demand for the reference year.
    reference_aggregated_daily_heating_demand_time_series = general_utilities.aggregate_time_series(reference_daily_heating_demand_time_series, weights)

    # Select the days in the reference year. Typically there is one extra day in the time series, so we remove it.
    reference_aggregated_daily_heating_demand_time_series = reference_aggregated_daily_heating_demand_time_series.sel(time=pd.date_range(str(reference_year), str(reference_year+1), freq='D')[:-1])

    # Calculate the total heating degree days in the reference year.
    reference_heating_degree_days = float(reference_aggregated_daily_heating_demand_time_series.sum(dim='time'))

    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Calculate the time series of the heating demand for the given year and country. The time series has daily mean values and daily resolution.
        daily_heating_demand_time_series = get_heating_demand_time_series(region_shape, year, settings.heating_daily_temperature_threshold, hour_shift=hour_shift)

        # Select the days in the given year. Typically there is one extra day in the time series, so we remove it.
        daily_heating_demand_time_series = daily_heating_demand_time_series.sel(time=pd.date_range(str(year), str(year+1), freq='D')[:-1])

        # Aggregate the time series of the heating demand.
        aggregated_daily_heating_demand_time_series = general_utilities.aggregate_time_series(daily_heating_demand_time_series, weights)

        # Calculate the total heating degree days in the given year.
        heating_degree_days = float(aggregated_daily_heating_demand_time_series.sum(dim='time'))

        # Calculate the interannual change in the heating degree days.
        interannual_change = heating_degree_days / reference_heating_degree_days

        # Upsample the time series of the heating demand to hourly resolution. The series has still daily mean values but hourly resolution.
        aggregated_daily_heating_demand_time_series_at_hourly_resolution = aggregated_daily_heating_demand_time_series.reindex(time=pd.date_range(str(year), str(year+1), freq='h')[:-1], method='ffill')

        # Read the intraday profiles of the heating demand for the given country.
        hourly_intraday_profiles = get_hourly_heating_intraday_profile(country_info, year, method='hourly_and_temperature_dependent', weights=weights)

        for sector_and_use in list(hourly_intraday_profiles.data_vars):

            # Multiply the time series of the heating demand by the intraday profile.
            aggregated_hourly_heating_demand_time_series = aggregated_daily_heating_demand_time_series_at_hourly_resolution * hourly_intraday_profiles[sector_and_use]
        
            # Normalize the time series of the heating demand and multiply it by the interannual change in the heating degree days.
            aggregated_heating_demand = aggregated_hourly_heating_demand_time_series / aggregated_hourly_heating_demand_time_series.sum() * interannual_change

            # Add name and attributes to the aggregated time series.
            aggregated_heating_demand = aggregated_heating_demand.rename(sector_and_use.replace('_', ' ').capitalize()+' heating demand')
            aggregated_heating_demand = aggregated_heating_demand.assign_attrs(units='kW/kWh', description=sector_and_use.replace('_', ' ').capitalize()+' heating demand per unit of total annual heating demand')
        
            # Save the aggregated time series of the heating demand.
            general_utilities.save_time_series(aggregated_heating_demand, country_info, 'heating__demand_time_series__'+sector_and_use)
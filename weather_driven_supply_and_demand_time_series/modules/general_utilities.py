import os
import argparse
import xarray as xr
import pandas as pd
import pytz
from datetime import datetime
from dask.diagnostics.progress import ProgressBar

import modules.settings as settings
import modules.directories as directories


def get_countries():
    '''
    Returns a dataframe with the countries in the focus region, their ISO codes, and whether they have offshore wind.

    Returns
    -------
    countries : pandas.DataFrame
        Dataframe with the countries in the focus region, their ISO codes, and whether they have offshore wind
    '''

    # Read European EU countries and their information.
    countries = pd.read_csv(settings.working_directory + '/EU27_countries.csv', index_col='Name', usecols=['Name','ISO Alpha-3','ISO Alpha-2', 'Offshore'])

    # Read European non-EU countries and their information.
    countries = pd.concat([countries, pd.read_csv(settings.working_directory + '/European_non_EU_countries.csv', index_col='Name', usecols=['Name','ISO Alpha-3','ISO Alpha-2', 'Offshore'])])

    # Sort the countries by name.
    countries = countries.sort_values(by=['Name'])
    countries = countries.reset_index()
    
    return countries


def read_command_line_arguments():
    '''
    Create a parser for the command line arguments and read them.

    Returns
    -------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Create a parser for the command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('country_name', metavar='country_name', type=str, help='The name of the country of interest')

    # Read the arguments from the command line.
    args = parser.parse_args()

    # Get the countries in the focus region.
    country_info_list = get_countries()

    # Get the country of interest.
    country_info = country_info_list.loc[country_info_list['Name']==args.country_name].squeeze()

    return country_info


def aggregate_time_series(time_series, weights):
    '''
    Compute the aggregated time series based on given weights.

    Parameters
    ----------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the resource/demand of interest for the given year and country
    weights : xarray.DataArray or xarray.Dataset
        Weights (longitude x latitude) used to aggregate the time series dataset

    Returns
    -------
    aggregated_time_series : xarray.DataArray
        Aggregated time series (time) of the resource/demand of interest for the given year and country
    '''
    
    # Select a subset of the time series based on the weights' spatial extent (usually they already have the same spatial extent).
    subset_of_time_series = time_series.sel(x=slice(weights.x.min(),weights.x.max()),y=slice(weights.y.min(),weights.y.max()))

    # Calculate the aggregated time series
    aggregated_time_series = (subset_of_time_series*weights).sum(dim='x').sum(dim='y')/weights.sum()

    # Perform the calculation.
    with ProgressBar():
        print('Aggregating the time series...')
        aggregated_time_series = aggregated_time_series.compute()
    
    return aggregated_time_series


def save_time_series(time_series, country_info, variable_name):
    '''
    Save the time series of the resource/demand of interest for the given year and country.
    Append if the file already exists.

    Parameters
    ----------
    time_series : xarray.DataArray
        Time series (time) of the resource/demand of interest for the given year and country
    country_info : pandas.Series
        Series containing the information of the country of interest
    variable_name : str
        Name of the variable of interest
    '''

    # Define the output data path.
    postprocessed_data_path = directories.get_postprocessed_data_path(country_info, variable_name)

    # If the file already exists, append the new time series.
    if os.path.exists(postprocessed_data_path):
        with xr.open_dataarray(postprocessed_data_path) as original_time_series:
            time_series = xr.concat([original_time_series,time_series],dim='time')
            time_series = time_series.sortby('time')
    
    # Save the time series.
    time_series.to_netcdf(postprocessed_data_path, engine='netcdf4')


def calculate_hour_shift(country_info):
    '''
    Calculate the time shift between UTC and the time zone of the country of interest.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest

    Returns
    -------
    hour_shift : float
        Time shift between UTC and the time zone of the country of interest, in hours
    '''

    # Get the country time zone.
    country_timezone = pytz.timezone(pytz.country_timezones[country_info['ISO Alpha-2']][0])

    # Get the UTC time zone.
    utc_timezone = pytz.timezone('UTC')

    # Get an arbitrary time expressed both in UTC and in the country time zone.
    datetime1 = utc_timezone.localize(datetime(2000, 1, 1))
    datetime2 = country_timezone.localize(datetime(2000, 1, 1))

    # Calculate the time shift between UTC and the country time zone, in hours.
    hour_shift = (datetime2 - datetime1).total_seconds()/3600

    return hour_shift
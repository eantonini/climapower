import os
import argparse
import numpy as np
import xarray as xr
import pandas as pd
import pytz
from datetime import datetime
from dask.diagnostics.progress import ProgressBar
import matplotlib.pyplot as plt

import settings
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


def write_to_log_file(filename, message, new_file=False, write_time=False):
    '''
    Write a message to a log file.

    Parameters
    ----------
    filename : str
        Name of the log file without the extension
    message : str
        Message to write to the log file
    new_file : bool, optional
        If True, the log file is created
    write_time : bool, optional
        If True, the current time is written before the message
    '''
    
    # Create the log file if it does not exist.
    if not os.path.exists(settings.working_directory+'/log_files'):
        os.makedirs(settings.working_directory+'/log_files')
    
    # Determine whether to append or overwrite the log file.
    mode = 'w' if new_file else 'a'

    # Write the message to the log file.
    with open(settings.working_directory+'/log_files/'+filename+'.log', mode) as output_file:
        if write_time:
            # Write the current time to the log file.
            now = datetime.now()
            prefix_time = now.strftime('%H:%M:%S') + ' - '
            output_file.write(prefix_time + message)
        else:
            output_file.write(message)


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


def get_time_series_frequency(time_series):
    '''
    Get the frequency of a time series.

    Parameters
    ----------
    time_series : pandas.Series
        Time series of interest

    Returns
    -------
    frequency : str
        Frequency of the time series
    '''

    # Get the frequency of the time series.
    if time_series.index.freqstr != None:
        frequency = time_series.index.freqstr
    else:
        time_resolution_in_minutes = time_series.index.to_series().diff().dt.total_seconds().div(60).median()
        if time_resolution_in_minutes == 60*24*7:
            frequency = 'W'
        elif time_resolution_in_minutes == 60:
            frequency = 'H'
        elif time_resolution_in_minutes == 30:
            frequency = '30T'
        elif time_resolution_in_minutes == 15:
            frequency = '15T'
        else:
            frequency = 'W'
            print('The time series frequency is not recognized. The frequency is set to weekly.')
        
    return frequency


def linearly_interpolate(time_series, consecutive_missing_values=1):
    '''
    Linearly interpolate the missing values in a time series only if they are isolated or in couples.
    
    Parameters
    ----------
    time_series : pandas.Series
        Time series of interest
    consecutive_missing_values : int, optional
        Threshold of consecutive missing values to interpolate. It can be 1 (default) or 2.
    
    Returns
    -------
    time_series : pandas.Series
        Time series of interest with the missing values interpolated
    '''

    # Get the number of original non-null values.
    original_non_null_values = time_series.notnull().sum()

    # Create a copy of the time series.
    time_series_copy = time_series.copy()

    # Interpolate the missing values.
    if consecutive_missing_values == 1:

        # Where there is a NaN value, replace it with the average of the previous and next values. This takes care of replacing isolated NaN values.
        time_series_copy[time_series.isnull()] = (time_series.shift(-1) + time_series.shift(1))/2

        interpolated_values = time_series_copy.notnull().sum()-original_non_null_values

        if interpolated_values > 0:
            
            # Print the number of interpolated values.
            print('Interpolated {:d} isolated missing values.'.format(interpolated_values))
    
    elif consecutive_missing_values == 2:

        # Find the first of the two consecutive NaN values that are within two non-NaN values.
        first_nan = (time_series.shift(-2).notnull()) & (time_series.shift(-1).isnull()) & (time_series.isnull()) & (time_series.shift(1).notnull())

        # Find the second of the two consecutive NaN values that are within two non-NaN values.
        second_nan = (time_series.shift(-1).notnull()) & (time_series.isnull()) & (time_series.shift(1).isnull()) & (time_series.shift(2).notnull())

        # Interpolate the missing values.
        time_series_copy[first_nan] = time_series.shift(1) + (time_series.shift(-2)-time_series.shift(1))*1/3
        time_series_copy[second_nan] = time_series.shift(2) + (time_series.shift(-1)-time_series.shift(2))*2/3
    
        interpolated_values = int((time_series_copy.notnull().sum()-original_non_null_values)/2)

        if interpolated_values > 0:
        
            # Print the number of interpolated values.
            print('Interpolated {:d} couples of missing values.'.format(interpolated_values))
    
    return time_series_copy


def remove_outliers(time_series):
    '''
    Remove the outliers from the time series.

    Parameters
    ----------
    time_series : xarray.DataArray
        Time series (time) where to check for outliers

    Returns
    -------
    time_series : xarray.DataArray
        Time series (time) where the outliers have been removed
    '''

    # Calculate maximum value.
    max_value = time_series.quantile(0.99)*1.5

    # Make a copy of the time series.
    original_time_series = time_series.copy()

    # Assign -1 to NaN values.
    time_series = time_series.where(time_series.notnull(), -1)

    # Assign NaN to the outliers.
    time_series = time_series.where(time_series <= max_value, np.nan)
    
    # Check if there are NaN values.
    if time_series.isnull().any():

        # Count the number of NaN values.
        number_of_outliers = time_series.isnull().sum()

        # Interpolate the time series.
        time_series = time_series.interpolate()

        fig, ax = plt.subplots()
        original_time_series.plot(ax=ax, color='red', label='Original time series')
        time_series.where(time_series >= 0, np.nan).plot(ax=ax, color='green', label='Interpolated time series')

        print('Removed '+ str(number_of_outliers) +' outliers by interpolation.')

    # Assign NaN to the negative values to recover the missing values in the original time series.
    time_series = time_series.where(time_series >= 0, np.nan)

    return time_series
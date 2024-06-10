import pandas as pd
import numpy as np

from modules.exceptions import NotEnoughDataError

import modules.general_utilities as general_utilities


def check_data_availability(time_series, start, end, missing_data_threshold=0.6):
    '''
    Check if the time series has sufficient data availability.

    Parameters
    ----------
    time_series : pandas.Series
        Time series to check
    start : pandas.Timestamp
        Start date of the period of interest
    end : pandas.Timestamp
        End date of the period of interest
    missing_timesteps_threshold : float
        Fraction of missing timesteps above which the data retrieval is considered failed
    '''

    # Get the frequency of the time series.
    frequency = general_utilities.get_time_series_frequency(time_series)

    if time_series.isnull().sum() > len(time_series)*missing_data_threshold:

        raise NotEnoughDataError('{:d}% of the values are NaN. ENTSO-E data retrieval failed.'.format(int(time_series.isnull().sum()/len(time_series)*100)))

    if len(time_series) < len(pd.date_range(start, end, freq=frequency))*(1-missing_data_threshold):

        raise NotEnoughDataError('{:d}% of the timesteps are missing. ENTSO-E data retrieval failed.'.format(int((1-len(time_series)/len(pd.date_range(start, end, freq=frequency)))*100)))

    if (time_series < 1e-6).sum() > len(time_series)*missing_data_threshold:

        print('{:d}% of the values are zero.'.format(int((time_series < 1e-6).sum()/len(time_series)*100)))


def get_weekly_time_index(original_time_series, start, end, keep_missing_timesteps=False):
    '''
    Get the weekly time index.

    Parameters
    ----------
    original_time_series : pandas.Series
        Original time series
    start : pandas.Timestamp
        Start date of the period of interest
    end : pandas.Timestamp
        End date of the period of interest
    keep_missing_timesteps : bool
        If True, keep the timesteps that are missing in the original time series

    Returns
    -------
    time_series_index : pandas.DatetimeIndex
        Weekly time index
    '''
    
    # Convert the start and end dates to tz-naive.
    start = start.tz_convert(None)
    end = end.tz_convert(None)

    # If the first timestep is before the start date, substract a week from the start date.
    if original_time_series.index[0] < start:
        start = (start - pd.Timedelta(hours=24*7))
    
    # If the first timestep is not a Sunday, it means that the weekly resolution starts on a Monday. Substract a day from the start date.
    if original_time_series.index[0].weekday() != 6:
        start = (start - pd.Timedelta(hours=24))
            
    # Calculate the weekly time index.
    time_series_index = pd.date_range(start, end, freq='W')

    # Exclude the last timestep only if it falls on the same day of the end date or in close proximity. 
    # if (time_series_index[-1].month == 12 and time_series_index[-1].day == 31) or (time_series_index[-1].year > time_series_index.year.to_series().median()):
    if np.abs(time_series_index[-1] - end) <= pd.Timedelta(hours=24):
        time_series_index = time_series_index[:-1]
    
    if keep_missing_timesteps:

        # Check if the new timesteps are present in the original time series.
        # They are present if the difference between any of the new timesteps and any of the original timesteps is less than 24 hours.
        # This is done because timesteps in the original and new time series have the same day but might not have exactly the same hour.
        
        # Initialize a list to store the results.
        index_is_present = []
        
        for tt in range(len(time_series_index)):

            # Calculate the minimum difference between any of the new timesteps and any of the original timesteps.
            minimum_index_difference = np.min(np.abs(original_time_series.index - time_series_index[tt]))

            # If the minimum difference is less than or equal to 24 hours, the timestep is present in the original time series.
            if minimum_index_difference <= pd.Timedelta(hours=24):
                index_is_present.append(True)
            else:
                index_is_present.append(False)
        
        # Remove timesteps that are not present in the original time series.
        time_series_index = time_series_index[index_is_present]

    return time_series_index


def add_missing_timesteps(time_series, start, end, add_all_missing_timesteps=True):
    '''
    Add missing timesteps to the time series. The values corresponding to the added timesteps are NaN.

    Parameters
    ----------
    time_series : pandas.Series
        Time series where missing values are added
    start : pandas.Timestamp
        Start date of the period of interest
    end : pandas.Timestamp
        End date of the period of interest
    add_all_missing_timesteps : bool
        True if all the timesteps in the period of interest are added to the time series
    
    Returns
    -------
    time_series : pandas.Series
        Time series with missing values added
    '''

    # Get the frequency of the time series.
    frequency = general_utilities.get_time_series_frequency(time_series)

    if add_all_missing_timesteps:

        # Create a time series with all the timesteps in the period of interest.
        if frequency[0] == 'W':
            all_timesteps = get_weekly_time_index(time_series, start, end)
            
        else:
            # If the frequency is not weekly, the last timestep is excluded.
            all_timesteps = pd.date_range(start, end, freq=frequency)[:-1]
    
    else:

        # Create a time series with all the timesteps in the period of interest.
        all_timesteps = pd.date_range(time_series.index[0], time_series.index[-1], freq=frequency)
    
    # Check if the timesteps are tz-aware.
    if all_timesteps.tz is not None:

        # Convert the time series to tz-naive.
        all_timesteps = all_timesteps.tz_localize(None)

    # Check if the time series has missing timesteps.
    if len(time_series) < len(all_timesteps):
    
        # Calculate the number of missing timesteps.
        timesteps_to_add = len(all_timesteps)-len(time_series)
            
        # Add the missing timesteps.
        time_series = pd.Series(data=time_series, index=all_timesteps)

        print('Added {:d} missing timesteps.'.format(timesteps_to_add))
    
    return time_series


def sanitize_time_series(time_series, start, end, linearly_interpolate=True, add_all_missing_timesteps=True):
    '''
    Sanitize the time series retrieved from ENTSO-E.
    
    Parameters
    ----------
    time_series : pandas.Series
        Time series to sanitize
    start : pandas.Timestamp
        Start date of the period of interest
    end : pandas.Timestamp
        End date of the period of interest
    add_all_missing_timesteps : bool
        True if all the timesteps in the period of interest are added to the time series
    
    Returns
    -------
    time_series : pandas.Series
        Sanitized time series
    '''

    # If the generation time series has more than 60% of the values that are NaN, zero, or mising, raise an error.
    check_data_availability(time_series, start, end)

    # Check if the time series has missing timesteps and add them.
    time_series = add_missing_timesteps(time_series, start, end, add_all_missing_timesteps=add_all_missing_timesteps)
    
    if linearly_interpolate:
        # Linearly interpolate only where there is an isolated missing value.
        time_series = general_utilities.linearly_interpolate(time_series, consecutive_missing_values=1)

        # Linearly interpolate only where there are two consecutive missing values.
        time_series = general_utilities.linearly_interpolate(time_series, consecutive_missing_values=2)

    # If the time series still has NaN values, set them to zero.
    nan_values = time_series.isnull().sum()
    if nan_values > 0:
        time_series = time_series.fillna(0)
        print('Set {:d} NaN values to zero.'.format(nan_values))

    return time_series


def resample_to_hourly(time_series):
    '''
    Resample the time series to hourly resolution.

    Parameters
    ----------
    time_series : pandas.Series
        Time series to resample
    
    Returns
    -------
    time_series : pandas.Series
        Resampled time series
    '''

    # Get the start and end dates of the time series.
    time_series_start = time_series.index[0]
    time_series_end = time_series.index[-1]

    if len(time_series) > len(pd.date_range(time_series_start, time_series_end, freq='h')):

        # The resampling is done by taking the mean of the values in the bins. The offset is set to -0.5H so that the bins are centered on the hour. The bin labels are set to the left bin edge.
        time_series = time_series.resample('1h', offset='-0.5h').mean()[:-1]

        # Set the index of the generation time series to the correct hourly time series.
        time_series.index = pd.date_range(time_series_start, time_series_end, freq='h')

        print('Resampled to hourly resolution.')
    
    return time_series


def adjust_time_series_ends(time_series, year, start_previous_period, start_year, end_year, end_following_period):
    '''
    Adjust the ends of the time series.
    
    Parameters
    ----------
    time_series : pandas.Series
        Time series to adjust
    year : int
        Year of interest
    start_previous_period : pandas.Timestamp
        Start date of the previous period
    start_year : pandas.Timestamp
        Start date of the year of interest
    end_year : pandas.Timestamp
        End date of the year of interest
    end_following_period : pandas.Timestamp
        End date of the following period
    
    Returns
    -------
    time_series : pandas.Series
        Adjusted time series
    '''

    # If more than one values are present in the previous year, keep only the last one.
    # If no values are present in the previous year, use the last values of the year of interest.
    timesteps_in_previous_year = len(time_series[time_series.index.year==year-1])
    if timesteps_in_previous_year > 1:
        time_series = time_series[(timesteps_in_previous_year-1):]
    elif timesteps_in_previous_year == 0:
        timesteps_in_previous_period = pd.date_range(start_previous_period, start_year, freq='W').tz_convert(None)
        time_series_in_previous_period = time_series[time_series.index.year==year][-len(timesteps_in_previous_period):]
        time_series_in_previous_period.index = timesteps_in_previous_period
        time_series_in_previous_period = time_series_in_previous_period[-1:]
        time_series = pd.concat([time_series_in_previous_period, time_series])

    # If more than one values are present in the following year, keep only the first one.
    # If no values are present in the following year, use the first values of the year of interest.
    timesteps_in_following_year = len(time_series[time_series.index.year==year+1])
    if timesteps_in_following_year > 1:
        time_series = time_series[:-(timesteps_in_following_year-1)]
    elif timesteps_in_following_year == 0:
        # If the last day of the time series is December 24 (which means that December 31 is missing), add the first day of the current year.
        if time_series.index[-1].month == 12 and time_series.index[-1].day == 24:
            time_series_at_december_31 = time_series[time_series.index.year==year][:1]
            time_series_at_december_31.index = [pd.Timestamp(str(year)+'-12-31 ' + str(time_series_at_december_31.index[0].hour) + ':00:00')]
            time_series = pd.concat([time_series, time_series_at_december_31])

            timesteps_in_following_period = pd.date_range(end_year, end_following_period, freq='W').tz_convert(None)
            time_series_in_following_period = time_series[time_series.index.year==year][1:(len(timesteps_in_following_period)+1)]
        else:
            timesteps_in_following_period = pd.date_range(end_year, end_following_period, freq='W').tz_convert(None)
            time_series_in_following_period = time_series[time_series.index.year==year][:len(timesteps_in_following_period)]
        time_series_in_following_period.index = timesteps_in_following_period
        time_series_in_following_period = time_series_in_following_period[:1]
        time_series = pd.concat([time_series, time_series_in_following_period])
    
    return time_series
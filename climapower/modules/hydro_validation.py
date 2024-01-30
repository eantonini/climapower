import numpy as np
import pandas as pd
import xarray as xr

import settings
import modules.directories as directories
import modules.geometry as geometry
import modules.validation_utilities as validation_utilities
import modules.energy_supply_data as energy_supply_data
import modules.basic_figures as figures


def calibrate_hydropower_inflow_time_series(simulated_weekly_hydropower_inflow_time_series, actual_weekly_hydropower_inflow_time_series):
    '''
    Calculate the retain factor (actual inflow / simulated inflow) for each month of the year.

    Source: https://doi.org/10.1016/j.isci.2021.102999

    Parameters
    ----------
    simulated_weekly_hydropower_inflow_time_series : pandas.Series
        Time series of the simulated hydropower inflow
    actual_weekly_hydropower_inflow_time_series : pandas.Series
        Time series of the actual hydropower inflow

    Returns
    -------
    calibrated_weekly_hydropower_inflow_time_series : pandas.Series
        Time series of the calibrated hydropower inflow
    retain_factors : pandas.Series
        Series containing the coefficients of the retain factor
    '''

    # Downsample the time series to monthly resolution.
    simulated_monthly_hydropower_inflow_time_series = simulated_weekly_hydropower_inflow_time_series.resample('1M').sum()
    actual_monthly_hydropower_inflow_time_series = actual_weekly_hydropower_inflow_time_series.resample('1M').sum()

    # Calculate the retain factor for each month of the year.
    retain_factors = actual_monthly_hydropower_inflow_time_series/simulated_monthly_hydropower_inflow_time_series

    # Calibrate the simulated hydropower inflow time series.
    mapped_retain_factors = pd.Series(data=retain_factors[simulated_weekly_hydropower_inflow_time_series.index.month-1].values, index=simulated_weekly_hydropower_inflow_time_series.index)
    calibrated_weekly_hydropower_inflow_time_series = simulated_weekly_hydropower_inflow_time_series*mapped_retain_factors

    return calibrated_weekly_hydropower_inflow_time_series, retain_factors


def validate_hydropower_inflow_time_series(country_info):
    '''
    Validate the hydropower inflow time series obtained from climate data.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)
    
    for year in general_utilities.get_years_for_calibration(country_info, 'hydropower'):

        # Calculate the aggregated hydropower inflow time series. This is in unit of kg/h
        # aggregated_simulated_hydropower_inflow_time_series = xr.open_dataarray(directories.get_postprocessed_data_path(country_info, 'hydropower__inflow_time_series__conventional_and_pumped_storage'))
        aggregated_simulated_hydropower_inflow_time_series = xr.open_dataarray(directories.get_postprocessed_data_path(country_info, 'hydropower__inflow_time_series__run_of_river'))

        # Select only the time steps in the year of interest. Add 7 days before and after the year of interest to make sure the resampled time series is complete.
        start = pd.Timestamp(str(year)) - pd.Timedelta(days=7)
        end = pd.Timestamp(str(year+1)) + pd.Timedelta(days=7)
        aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.sel(time=slice(start,end))

        # Resample the time series to weekly resolution.
        aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.to_series().resample('1W').sum()

        # Assume mean hydraulic head of all the hydropower plants in the country.
        # mean_hydraulic_head = 50 # m
        mean_hydraulic_head = 10 # m

        # Convert the time series to unit of GWh.
        j_to_gwh = 1/3.6e12
        aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series*9.81*mean_hydraulic_head*j_to_gwh

        # Calculate the hydropower inflow time series estimated with data retreived from ENTSO-E. This is in unit of GWh.
        # aggregated_actual_hydropower_inflow_time_series = energy_supply_data.get_entsoe_hydropower_inflow(country_info, year)/1e3
        aggregated_actual_hydropower_inflow_time_series = energy_supply_data.get_entsoe_hydropower_inflow(country_info, year, water_reservoir_and_pumped_storage=False)/1e3

        # Select only the time steps in the year of interest.
        aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.loc[aggregated_simulated_hydropower_inflow_time_series.index.year == year]
        aggregated_actual_hydropower_inflow_time_series = aggregated_actual_hydropower_inflow_time_series.loc[aggregated_actual_hydropower_inflow_time_series.index.year == year]

        if settings.calibrate:
            
            # Calibrate the simulated hydropower inflow time series.
            aggregated_calibrated_hydropower_inflow_time_series, retain_factors = calibrate_hydropower_inflow_time_series(aggregated_simulated_hydropower_inflow_time_series, aggregated_actual_hydropower_inflow_time_series)

            # Save the retain factor.
            validation_utilities.save_calibration_coefficients(country_info, year, 'hydropower', retain_factors.values, np.arange(len(retain_factors)), additional_info='__conventional_and_pumped_storage')
            validation_utilities.save_calibration_coefficients(country_info, year, 'hydropower', retain_factors.values, np.arange(len(retain_factors)), additional_info='__run_of_river')
        
        if settings.make_plots:

            # Create a dataframe to compare the simulated and actual capacity factors.
            compare = pd.DataFrame(data=aggregated_actual_hydropower_inflow_time_series.values, index=aggregated_actual_hydropower_inflow_time_series.index.values, columns=['actual'])
            compare = compare.combine_first(pd.DataFrame(data=aggregated_simulated_hydropower_inflow_time_series.values, index=aggregated_simulated_hydropower_inflow_time_series.index, columns=['simulated']))

            # Add the calibrated time series if calculated.
            if settings.calibrate:
                compare = compare.combine_first(pd.DataFrame(data=aggregated_calibrated_hydropower_inflow_time_series.values, index=aggregated_calibrated_hydropower_inflow_time_series.index, columns=['calibrated'])) # type: ignore

            compare = compare.loc[compare.index.year == year]

            # Plot the comparison.
            # figures.plot_comparison_in_year(region_shape, year, 'hydropower___weekly_inflow__conventional_and_pumped_storage', compare)
            figures.plot_comparison_in_year(region_shape, year, 'hydropower___weekly_inflow__run_of_river', compare)
import numpy as np
import pandas as pd
import xarray as xr

import settings
import modules.general_utilities as general_utilities
import modules.geometry as geometry
import modules.geospatial_utilities as geospatial_utilities
import modules.validation_utilities as validation_utilities
import modules.energy_supply_data as energy_supply_data
import modules.hydro_resource as hydro_resource
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
    simulated_monthly_hydropower_inflow_time_series = simulated_weekly_hydropower_inflow_time_series.resample('1ME').sum()
    actual_monthly_hydropower_inflow_time_series = actual_weekly_hydropower_inflow_time_series.resample('1ME').sum()

    # Calculate the retain factor for each month of the year.
    retain_factors = actual_monthly_hydropower_inflow_time_series/simulated_monthly_hydropower_inflow_time_series

    # Calibrate the simulated hydropower inflow time series.
    mapped_retain_factors = pd.Series(data=retain_factors[simulated_weekly_hydropower_inflow_time_series.index.month-1].values, index=simulated_weekly_hydropower_inflow_time_series.index)
    calibrated_weekly_hydropower_inflow_time_series = simulated_weekly_hydropower_inflow_time_series*mapped_retain_factors

    return calibrated_weekly_hydropower_inflow_time_series, retain_factors


def get_weekly_hydropower_inflow_time_series(region_shape, year, basins_of_interests, fraction_of_grid_cell_in_each_basin, coventional_and_pumped_storage=True):
    '''
    Calculate the weekly hydropower inflow time series for the given year and country.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Shape of the region of interest
    year : int
        Year of interest
    basins_of_interests : Basins
        Basins of interests
    fraction_of_grid_cell_in_each_basin : xarray.DataArray
        Fraction of each grid cell that intersects with each basin (number of basins x longitude x latitude)
    coventional_and_pumped_storage : bool
        True if the hydropower inflow is for the conventional and pumped storage plants
        False if the hydropower inflow is for the run-of-river plants
    
    Returns
    -------
    aggregated_simulated_hydropower_inflow_time_series : pandas.Series
        Time series of the weekly simulated hydropower inflow
    '''

    # Calculate the inflow time series for the given year and country.
    aggregated_inflow = hydro_resource.get_inflow_time_series(region_shape, year, basins_of_interests, fraction_of_grid_cell_in_each_basin, coventional_and_pumped_storage)

    # Get the inflow time series in the previous year to make sure the resampled time series is complete.
    try:
        aggregated_inflow_previous_year = hydro_resource.get_inflow_time_series(region_shape, year-1, basins_of_interests, fraction_of_grid_cell_in_each_basin, coventional_and_pumped_storage)
    except FileNotFoundError:
        # Select the last seven days of the current year and assign them to the previous year.
        aggregated_inflow_previous_year = aggregated_inflow.sel(time=slice(pd.Timestamp(str(year+1)) - pd.Timedelta(days=7), pd.Timestamp(str(year+1))))
        # Update the time index to the previous year.
        aggregated_inflow_previous_year['time'] = aggregated_inflow_previous_year['time'].values - pd.Timedelta(hours=len(aggregated_inflow['time']))
    
    # Get the inflow time series in the next year to make sure the resampled time series is complete.
    try:
        aggregated_inflow_next_year = hydro_resource.get_inflow_time_series(region_shape, year+1, basins_of_interests, fraction_of_grid_cell_in_each_basin, coventional_and_pumped_storage)
    except FileNotFoundError:
        # Select the first seven days of the current year and assign them to the next year.
        aggregated_inflow_next_year = aggregated_inflow.sel(time=slice(pd.Timestamp(str(year)), pd.Timestamp(str(year)) + pd.Timedelta(days=7)))
        # Update the time index to the next year.
        aggregated_inflow_next_year['time'] = aggregated_inflow_next_year['time'].values + pd.Timedelta(hours=len(aggregated_inflow['time']))
    
    # Concatenate the inflow time series of the previous year, the current year, and the next year.
    aggregated_simulated_hydropower_inflow_time_series = xr.concat([aggregated_inflow_previous_year, aggregated_inflow, aggregated_inflow_next_year], dim='time')

    # Select only the time steps in the year of interest. Add 7 days before and after the year of interest to make sure the resampled time series is complete.
    aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.sel(time=slice(pd.Timestamp(str(year)) - pd.Timedelta(days=7), pd.Timestamp(str(year+1)) + pd.Timedelta(days=7)))

    # Resample the time series to weekly resolution.
    aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.to_series().resample('1W').sum()

    return aggregated_simulated_hydropower_inflow_time_series


def validate_hydropower_inflow_time_series(country_info, coventional_and_pumped_storage=True):
    '''
    Validate the hydropower inflow time series obtained from climate data.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    coventional_and_pumped_storage : bool
        True if the hydropower inflow is for the conventional and pumped storage plants
        False if the hydropower inflow is for the run-of-river plants
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Get the basins of interests.
    basins_of_interests = hydro_resource.get_basins_of_interests(country_info, conventional_and_pumped_storage=coventional_and_pumped_storage)

    # Determine the fraction of each grid cell that intersects with each basin (longitude x latitude x number of basins).
    fraction_of_grid_cell_in_each_basin = geospatial_utilities.get_fraction_of_grid_cell_in_shape(region_shape, basins_of_interests.shapes)
    
    for year in general_utilities.get_years_for_calibration(country_info, 'hydropower'):

        # Calculate the simulated hydropower inflow time series.
        aggregated_simulated_hydropower_inflow_time_series = get_weekly_hydropower_inflow_time_series(region_shape, year, basins_of_interests, fraction_of_grid_cell_in_each_basin, coventional_and_pumped_storage=coventional_and_pumped_storage)

        # Calculate the hydropower inflow time series estimated with data retreived from ENTSO-E. This is in unit of GWh.
        aggregated_actual_hydropower_inflow_time_series = energy_supply_data.get_entsoe_hydropower_inflow(country_info, year, coventional_and_pumped_storage=coventional_and_pumped_storage)/1e3
        
        # Select only the time steps in the year of interest.
        aggregated_simulated_hydropower_inflow_time_series = aggregated_simulated_hydropower_inflow_time_series.loc[aggregated_simulated_hydropower_inflow_time_series.index.year == year]
        aggregated_actual_hydropower_inflow_time_series = aggregated_actual_hydropower_inflow_time_series.loc[aggregated_actual_hydropower_inflow_time_series.index.year == year]

        if settings.calibrate:
            
            # Calibrate the simulated hydropower inflow time series.
            aggregated_calibrated_hydropower_inflow_time_series, retain_factors = calibrate_hydropower_inflow_time_series(aggregated_simulated_hydropower_inflow_time_series, aggregated_actual_hydropower_inflow_time_series)

            # Save the retain factor.
            validation_utilities.save_calibration_coefficients(country_info, year, 'hydropower', retain_factors.values, np.arange(len(retain_factors)), additional_info=('__conventional_and_pumped_storage' if coventional_and_pumped_storage else '__run_of_river'))
        
        if settings.make_plots:

            # Create a dataframe to compare the simulated and actual capacity factors.
            compare = pd.DataFrame(data=aggregated_actual_hydropower_inflow_time_series.values, index=aggregated_actual_hydropower_inflow_time_series.index.values, columns=['actual'])
            compare = compare.combine_first(pd.DataFrame(data=aggregated_simulated_hydropower_inflow_time_series.values, index=aggregated_simulated_hydropower_inflow_time_series.index, columns=['simulated']))

            # Add the calibrated time series if calculated.
            if settings.calibrate:
                compare = compare.combine_first(pd.DataFrame(data=aggregated_calibrated_hydropower_inflow_time_series.values, index=aggregated_calibrated_hydropower_inflow_time_series.index, columns=['calibrated']))

            compare = compare.loc[compare.index.year == year]

            # Plot the comparison.
            figures.plot_comparison_in_year(region_shape, year, 'hydropower___weekly_inflow'+('__conventional_and_pumped_storage' if coventional_and_pumped_storage else '__run_of_river'), compare)
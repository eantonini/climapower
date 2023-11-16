import numpy as np
import pandas as pd
import scipy

import modules.settings as settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.climate_utilities as climate_utilities
import modules.validation_utilities as validation_utilities
import modules.energy_data as energy_data
import modules.plant_data as plant_data
import modules.solar_resource as solar_resource
import modules.basic_figures as figures


def calibrate_solar_capacity_factor_time_series(country_info, region_shape, year, plant_layout, aggregated_actual_capacity_factor_time_series):
    '''
    Calibrate the simulated solar capacity factor time series to match the actual capacity factor time series.

    The process is based on the following paper: https://doi.org/10.1016/j.energy.2016.08.060

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    plant_layout : xarray.DataArray
        Layout of the solar power plants
    aggregated_simulated_capacity_factor_time_series : xarray.DataArray
        Time series of the simulated (before calibration) aggregated capacity factor for the given year and country
    aggregated_actual_capacity_factor_time_series : xarray.DataArray
        Time series of the actual aggregated capacity factor for the given year and country

    Returns
    -------
    aggregated_calibrated_capacity_factor_time_series : xarray.DataArray
        Time series of the calibrated aggregated capacity factor for the given year and country
    alpha : float
        Calibration coefficient for the solar resource
    beta : float
        Calibration coefficient for the solar resource
    '''
    
    # Set the bounds for the alpha and beta coefficients.
    bounds = ((0, 2), (-0.5, 0.5))
    
    # Define the function to minimize.
    def get_solar_bias(coefficients):

        # Extract the alpha and beta coefficients.
        alpha = coefficients[0]
        beta = coefficients[1]
        
        # Calculate the time series of the capacity factor of the resource of interest for the given year and country.
        simulated_capacity_factor_time_series = solar_resource.get_solar_capacity_factor_time_series(country_info, region_shape, year, alpha=alpha, beta=beta)
        
        # Calculate the aggregated capacity factor.
        aggregated_simulated_capacity_factor_time_series = general_utilities.aggregate_time_series(simulated_capacity_factor_time_series, plant_layout)

        # Calculate the bias between the simulated and actual capacity factors.
        bias = np.abs(aggregated_actual_capacity_factor_time_series.mean() - aggregated_simulated_capacity_factor_time_series.mean().values)
        
        print('Bias: '+str(bias))
        return bias
    
    # Run the optimization to minimize the bias.
    optimized_results = scipy.optimize.minimize(get_solar_bias, x0=[1, 0.0], bounds=bounds, tol=1e-3)
    
    # Get the optimized beta coefficient.
    alpha = optimized_results.x[0]
    beta = optimized_results.x[1]
    
    # Calculate the time series of the capacity factor of the resource of interest for the given year and country.
    calibrated_capacity_factor_time_series = solar_resource.get_solar_capacity_factor_time_series(country_info, region_shape, year, alpha=alpha, beta=beta)
        
    # Calculate the aggregated capacity factor.
    aggregated_calibrated_capacity_factor_time_series = general_utilities.aggregate_time_series(calibrated_capacity_factor_time_series, plant_layout)
    
    return aggregated_calibrated_capacity_factor_time_series, alpha, beta


def validate_solar_capacity_factor_time_series(country_info):
    '''
    Validate the solar capacity factor time series obtained from climate data.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Get the shape of the region of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Create a temporary cutout.
    cutout = climate_utilities.create_temporary_cutout(region_shape)
    
    for year in range(settings.comparison_start_year, settings.comparison_end_year+1):

        # Get the plant layout and convert it t
        plant_database = plant_data.get_opsd_plant_database(country_info, year, 'solar')
        plant_layout = cutout.layout_from_capacity_list(plant_database, col='Capacity (MW)')
        
        # Calculate the time series of the capacity factor of the resource of interest for the given year and country.
        simulated_capacity_factor_time_series = solar_resource.get_solar_capacity_factor_time_series(country_info, region_shape, year)
        
        # Calculate the aggregated capacity factor.
        aggregated_simulated_capacity_factor_time_series = general_utilities.aggregate_time_series(simulated_capacity_factor_time_series, plant_layout)

        # Calculate the time series of the actual capacity factor of the resource of interest for the given year and country.
        aggregated_actual_capacity_factor_time_series = energy_data.get_actual_capacity_factor(country_info, year, 'solar')

        if settings.calibrate:
            
            # Calibrate the simulated capacity factor time series.
            aggregated_calibrated_capacity_factor_time_series, alpha, beta = calibrate_solar_capacity_factor_time_series(country_info, region_shape, year, plant_layout, aggregated_actual_capacity_factor_time_series)
                
            # Save the calibration coefficients.
            validation_utilities.save_calibration_coefficients(country_info, year, 'solar', [alpha, beta], ['alpha', 'beta'])
        
        if settings.make_plots:

            # Create a dataframe to compare the simulated and actual capacity factors.
            compare = pd.DataFrame(data=aggregated_actual_capacity_factor_time_series.values, index=aggregated_actual_capacity_factor_time_series.index.values, columns=['actual'])
            compare = compare.combine_first(pd.DataFrame(data=aggregated_simulated_capacity_factor_time_series.values, index=aggregated_simulated_capacity_factor_time_series['time'], columns=['simulated']))

            # Add the calibrated time series if calculated.
            if settings.calibrate:
                compare = compare.combine_first(pd.DataFrame(data=aggregated_calibrated_capacity_factor_time_series.values, index=aggregated_calibrated_capacity_factor_time_series['time'], columns=['calibrated'])) # type: ignore

            # Plot the comparison.
            figures.plot_installed_capacity(region_shape, year, 'solar___installed_capacity', plant_layout)
            figures.plot_comparison_in_year(region_shape, year, 'solar___weekly_capacity_factor', compare)
            figures.plot_comparison_in_period(region_shape, year, 'solar___hourly_capacity_factor', compare)
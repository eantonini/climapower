import numpy as np
import xarray as xr
import pandas as pd
from scipy.interpolate import CubicSpline
from itertools import accumulate

import modules.directories as directories
import modules.energy_demand_data as energy_demand_data
import modules.energy_supply_data as energy_supply_data


def get_time_series_dataset(country_info, year):

    variable_names = ['wind__capacity_factor_time_series__onshore',
                      'wind__capacity_factor_time_series__offshore',
                      'solar__capacity_factor_time_series',
                      'hydropower__inflow_time_series__conventional_and_pumped_storage',
                      'heating__demand_time_series__residential_space',
                      'heating__demand_time_series__services_space',
                      'cooling__demand_time_series']
    
    dataset = {}

    for variable_name in variable_names:

        variable = xr.open_dataarray(directories.get_postprocessed_data_path(country_info, variable_name, climate_data_source='historical')).loc[pd.date_range(str(year), str(year+1), freq='h')[:-1]]

        dataset[variable.name] = xr.open_dataarray(directories.get_postprocessed_data_path(country_info, variable_name, climate_data_source='historical')).loc[pd.date_range(str(year), str(year+1), freq='h')[:-1]]

    dataset['Electricity demand'] = energy_demand_data.get_entsoe_demand(country_info, year).to_xarray().rename({'index': 'time'})

    dataset['Conventional hydropower generation'] = energy_supply_data.get_entsoe_generation(country_info, year, 'B12', remove_outliers=False).to_xarray().rename({'index': 'time'})
    dataset['Conventional hydropower generation capacity'] = energy_supply_data.get_entsoe_capacity(country_info, year, 'B12')

    dataset['Pumped-storage hydropower generation'] = energy_supply_data.get_entsoe_generation(country_info, year, 'B10', linearly_interpolate=False, remove_outliers=False).to_xarray().rename({'index': 'time'})
    dataset['Pumped storage hydropower generation capacity'] = energy_supply_data.get_entsoe_capacity(country_info, year, 'B10')
    
    dataset['Pumped-storage hydropower consumption'] = energy_supply_data.get_entsoe_generation(country_info, year, 'B10', linearly_interpolate=False, remove_outliers=False, hydro_pumped_storage_consumption=True).to_xarray().rename({'index': 'time'})
    dataset['Pumped storage hydropower consumption capacity'] = 0.8 * dataset['Pumped storage hydropower generation capacity']
    
    dataset['Run-of-river hydropower generation'] = energy_supply_data.get_entsoe_generation(country_info, year, 'B11', remove_outliers=False).to_xarray().rename({'index': 'time'})
    dataset['Run-of-river hydropower generation capacity'] = energy_supply_data.get_entsoe_capacity(country_info, year, 'B11')
    
    # Convert the hydropower inflow time series to unit of MWh.
    mean_hydraulic_head = 50 # m
    j_to_mwh = 1/3.6e9
    dataset['Hydropower inflow'] = dataset['Hydropower inflow']*9.81*mean_hydraulic_head*j_to_mwh
    dataset['Hydropower inflow'] = dataset['Hydropower inflow'] / dataset['Hydropower inflow'].mean() * (dataset['Conventional hydropower generation'].mean() + dataset['Pumped-storage hydropower generation'].mean() - dataset['Pumped-storage hydropower consumption'].mean())
    
    dataset['Original reservoir filling level'] = energy_supply_data.get_entsoe_reservoir_filling_level(country_info, year)

    """ 
    plants = pd.read_csv(settings.energy_data_directory+'/jrc-hydro-power-plant-database.csv')

    plants = plants.loc[plants['country_code'] == country_info['ISO Alpha-2']]

    # Select the type of plants. It can be 'HDAM' (conventional plants), 'HPHS' (pumped storage plants), or 'HROR' (run-of-river plants).
    # Conventional and pumped storage hydro power plants are aggregated together because of the inflow into the reservoirs.
    conventional_plants = plants.loc[plants['type'] == 'HDAM']
    pumped_storage_plants = plants.loc[plants['type'] == 'HPHS']
    run_of_river_plants = plants.loc[plants['type'] == 'HROR']

    generation_capacity = conventional_plants['installed_capacity_MW'].sum() + pumped_storage_plants['installed_capacity_MW'].sum()
    consumption_capacity = pumped_storage_plants['pumping_MW'].sum()
    fixed_generation_capacity = run_of_river_plants['installed_capacity_MW'].sum()

    conventional_storage = conventional_plants['storage_capacity_MWh'].sum()
    pumped_storage_storage = pumped_storage_plants['storage_capacity_MWh'].sum()
    run_of_river_storage = run_of_river_plants['storage_capacity_MWh'].sum()
    """

    return dataset


def get_mix_for_highest_resource_adequacy(mix_values, resource_adequacy):
    '''
    Get the generation mix that maximizes the resource adequacy.
    
    Parameters
    ----------
    mix_values : numpy.ndarray
        Array containing the values of the generation mix.
    resource_adequacy : numpy.ndarray
        Array containing the resource adequacy for each value of the generation mix.
        
    Returns
    -------
    mix_of_max_resource_adequacy : float
        Value of the generation mix that maximizes the resource adequacy.
    '''

    # Upsample the values of the geneneration mix. The original values are equally spaced.
    upsampled_mix_values = np.linspace(mix_values[0], mix_values[-1], num=1001)

    # Create a cubic spline interpolation of the resource adequacy.
    spl = CubicSpline(mix_values, resource_adequacy)

    # Calculate the resource adequacy for the upsampled values of the generation mix.
    upsampled_resource_adequacy = spl(upsampled_mix_values)

    # Get the mix that maximizes the resource adequacy.
    mix_of_max_resource_adequacy = upsampled_mix_values[np.argmax(upsampled_resource_adequacy)]

    return mix_of_max_resource_adequacy


def get_generation_and_filling_level(inflow, unbounded_generation, initial_filling_level, filling_level_lower_bound, filling_level_upper_bound):
    '''
    Calculate the generation and filling level of the reservoirs.
    
    Parameters
    ----------
    inflow : pandas.Series
        Time series of the inflow into the reservoirs.
    unbounded_generation : pandas.Series
        Time series of the residual demand that hydropower generation has to meet, equivalent to the unbounded hydropower generation.
    initial_filling_level : float or list
        Initial filling level of the reservoirs. If it is a list, it contains the initial filling level of the upstream and downstream reservoirs.
    filling_level_lower_bound : float or list
        Lower bound of the filling level of the reservoirs. If it is a list, it contains the lower bound of the upstream and downstream reservoirs.
    filling_level_upper_bound : float or list
        Upper bound of the filling level of the reservoirs. If it is a list, it contains the upper bound of the upstream and downstream reservoirs.
    
    Returns
    -------
    filling_level : pandas.DataFrame
        Time series of the filling level of the reservoirs.
    generation : pandas.Series
        Time series of the hydropower generation.
    '''
    
    # Initialize the generation time series.
    generation = []

    def clip_filling_level(previus_filling_level, current_additions):

        nonlocal generation

        # Extract the inflow and generation/consumption.
        current_inflow = current_additions[0]
        current_generation = current_additions[1]
            
        if isinstance(previus_filling_level, tuple):

            # Add the inflow to the upstream reservoir and limit the filling level to the upper bound.
            current_upstream_filling_level = np.min([previus_filling_level[0] + current_inflow, filling_level_upper_bound[0]])
            
            if current_generation > 0:
                # Limit the generation to the available water in the upstream reservoir.
                current_generation = np.min([current_generation, current_upstream_filling_level - filling_level_lower_bound[0]])
            else:
                # Limit the consumption (negative generation) to the available water in the downstream reservoir or the available volume in the upstream reservoir.
                current_generation = np.max([current_generation, - (previus_filling_level[1] - filling_level_lower_bound[1]), - (filling_level_upper_bound[0] - current_upstream_filling_level)])

            # Subtract the generation from (or add the consumption to) the upstream reservoir.
            current_upstream_filling_level = current_upstream_filling_level - current_generation
            
            # Add the generation to (or subtract the consumption from) the downstream reservoir and limit the filling level to the upper bound.
            current_downstream_filling_level = np.min([previus_filling_level[1] + current_generation, filling_level_upper_bound[1]])

            # Add the current generation to the list.
            generation.append(current_generation)

            # Combine the filling level of the reservoirs.
            current_filling_level = (current_upstream_filling_level, current_downstream_filling_level)
        
        else:

            # Add the inflow to the upstream reservoir and limit the filling level to the upper bound.
            current_filling_level = np.min([previus_filling_level + current_inflow, filling_level_upper_bound])

            # Limit the generation to the available water in the upstream reservoir.
            current_generation = np.min([current_generation, current_filling_level - filling_level_lower_bound])

            # Add the current generation to the list.
            generation.append(current_generation)
            
            # Subtract the generation from the upstream reservoir.
            current_filling_level = current_filling_level - current_generation

        return current_filling_level
    
    # Get the original index of the inflow time series.
    original_index = inflow.index

    # Create a list of tuples with the inflow and generation/consumption.
    additions = list(zip(inflow, unbounded_generation))

    # Convert the initial filling level to a tuple if it is a list.
    if isinstance(initial_filling_level, list):
        initial_filling_level = tuple(initial_filling_level)
    
    # Calculate the filling level of the reservoirs using an accumulate function that clips the filling level to the bounds.
    filling_level = list(accumulate(additions, clip_filling_level, initial=initial_filling_level))[1:]
    
    # Convert the filling level and generation to pandas series.
    filling_level = pd.DataFrame(data=filling_level, index=original_index)
    generation = pd.Series(data=generation, index=original_index)

    return filling_level, generation


def get_hydropower_generation(residual_demand_for_hydropower, dataset, fraction_of_pumped_storage=0, hours_at_full_power_consumption_capacity=8):
    '''
    Calculate the hydropower generation and the filling level of the reservoirs.

    Parameters
    ----------
    residual_demand_for_hydropower : xarray.DataArray
        Time series of the residual demand that hydropower generation has to meet.
    dataset : dict
        Dictionary containing the time series data.
    fraction_of_pumped_storage : float, optional
        Fraction of the hydropower plants that are pumped storage plants.
        0 means that there are no pumped storage plants.
        1 means that the capacity of the pumped storage plants is equal to their current capacity.
        A value greater than 1 means that the capacity of the pumped storage plants is greater than their current capacity.
    hours_at_full_power_consumption_capacity : float, optional
        Number of hours that the pumped storage plants can operate at full power consumption capacity.

    Returns
    -------
    hydropower_generation : pandas.Series
        Time series of the hydropower generation.
    hydropower_upstream_reservoir_filling_level : pandas.Series
        Time series of the filling level of the upstream reservoirs.
    hydropower_downstream_reservoir_filling_level : pandas.Series
        Time series of the filling level of the downstream reservoirs.
    '''

    # Covert the residual demand to a pandas series.
    residual_demand_for_hydropower = residual_demand_for_hydropower.to_pandas()

    # Shif the values of hydropower inflow by one to reflect the fact that the previus timestep is considered in the enrgy balance.
    hydropower_inflow = dataset['Hydropower inflow'].to_pandas().shift(1, fill_value=0)
    
    # Get the total generation and consumption capacity of the hydropower plants.
    total_generation_capacity = dataset['Conventional hydropower generation capacity'] + dataset['Pumped storage hydropower generation capacity']
    total_consumption_capacity = fraction_of_pumped_storage * dataset['Pumped storage hydropower consumption capacity']

    # Limit the total consumption capacity of the pumped storage plants to 80% of the total generation capacity.
    if total_consumption_capacity > 0.8 * total_generation_capacity:
        total_consumption_capacity = 0.8 * total_generation_capacity
        print('The total consumption capacity of the pumped storage plants is limited to 80% of the total generation capacity.')
    
    # Initialize the hydropower generation time series with the residual demand and limit it to the capacity of the plants, both for generation and consumption.
    hydropower_generation = residual_demand_for_hydropower.where(residual_demand_for_hydropower < total_generation_capacity, total_generation_capacity)
    hydropower_generation = hydropower_generation.where(hydropower_generation > - total_consumption_capacity, - total_consumption_capacity)

    # Get the maximum and minimum filling level of the downstream reservoirs of the pumped storage plants.
    max_pumped_storage_downstream_reservoir_filling_level = total_consumption_capacity * hours_at_full_power_consumption_capacity
    min_pumped_storage_downstream_reservoir_filling_level = 0.1 * max_pumped_storage_downstream_reservoir_filling_level

    if fraction_of_pumped_storage > 0:
        # Calculate the filling level of the reservoirs and the generation.
        hydropower_reservoir_filling_level, hydropower_generation = get_generation_and_filling_level(hydropower_inflow, hydropower_generation,
                                                                                                     [dataset['Original reservoir filling level'][0], 0.5 * max_pumped_storage_downstream_reservoir_filling_level],
                                                                                                     [dataset['Original reservoir filling level'].min(), min_pumped_storage_downstream_reservoir_filling_level],
                                                                                                     [dataset['Original reservoir filling level'].max(), max_pumped_storage_downstream_reservoir_filling_level])
        
        # Extract the filling level of the upstream and downstream reservoirs.
        hydropower_upstream_reservoir_filling_level = hydropower_reservoir_filling_level[0].squeeze()
        hydropower_downstream_reservoir_filling_level = hydropower_reservoir_filling_level[1].squeeze()
    else:
        # Calculate the filling level of the reservoirs and the generation without considering the downstream reservoirs of the pumped storage plants.
        hydropower_reservoir_filling_level, hydropower_generation = get_generation_and_filling_level(hydropower_inflow, hydropower_generation,
                                                                                                     dataset['Original reservoir filling level'][0],
                                                                                                     dataset['Original reservoir filling level'].min(),
                                                                                                     dataset['Original reservoir filling level'].max())
        
        # Extract the filling level of the upstream reservoirs.
        hydropower_upstream_reservoir_filling_level = hydropower_reservoir_filling_level.squeeze()
        hydropower_downstream_reservoir_filling_level = 0 * hydropower_upstream_reservoir_filling_level
    
    return hydropower_generation, hydropower_upstream_reservoir_filling_level, hydropower_downstream_reservoir_filling_level


def get_residual_demand(dataset, wind_and_solar_generation_fraction, wind_generation_fraction, use_actual_hydropower_generation=True, fraction_of_pumped_storage=0, hours_at_full_power_consumption_capacity=8):
    '''
    Calculate the residual demand considering wind, solar, and hydropower generation.

    Parameters
    ----------
    dataset : xarray.Dataset
        Dataset containing the time series of the wind and solar capacity factors, the hydropower inflow and generation, and the electricity demand.
    wind_and_solar_generation_fraction : float
        Fraction of the electricity demand that is met in total by the wind and solar generation.
    wind_generation_fraction : float
        Fraction of the wind generation.
    hydropower_data : dict
        Dictionary containing the hydropower data.
    fraction_of_pumped_storage : float, optional
        Fraction of the hydropower plants that are pumped storage plants.
        0 means that there are no pumped storage plants.
        1 means that the capacity of the pumped storage plants is equal to their current capacity.
        A value greater than 1 means that the capacity of the pumped storage plants is greater than their current capacity.
    downstream_reservoir_factor : float, optional
        Factor by which the maximum filling level of the downstream reservoirs of the pumped storage plants is multiplied.
    
    Returns
    -------
    residual_demand : xarray.DataArray
        Time series of the residual demand.
    mean_wind_generation : float
        Mean wind generation.
    mean_solar_generation : float
        Mean solar generation.
    hydropower_generation : xarray.DataArray
        Time series of the hydropower generation.
    '''

    # Calculate the mean demand and the mean wind and solar generation.
    mean_electricity_demand = float(dataset['Electricity demand'].mean().values)

    # Get the actual hydropower generation.
    actual_hydropower_generation = dataset['Conventional hydropower generation'] + dataset['Pumped-storage hydropower generation'] + dataset['Run-of-river hydropower generation'] - dataset['Pumped-storage hydropower consumption']

    # Calculate the mean wind and solar generation by subtracting the mean actual hydropower generation from the mean electricity demand.
    mean_wind_generation = wind_and_solar_generation_fraction * wind_generation_fraction * (mean_electricity_demand - actual_hydropower_generation.mean())
    mean_solar_generation = wind_and_solar_generation_fraction * (1 - wind_generation_fraction) * (mean_electricity_demand - actual_hydropower_generation.mean())
    
    # Calculate the wind and solar generation.
    wind_generation = mean_wind_generation * dataset['Onshore wind capacity factor'] / dataset['Onshore wind capacity factor'].mean()
    solar_generation = mean_solar_generation * dataset['Solar capacity factor'] / dataset['Solar capacity factor'].mean()

    # Calculate the residual demand considering wind and solar.
    residual_demand = dataset['Electricity demand'] - wind_generation - solar_generation

    if use_actual_hydropower_generation:
        # Use the actual hydropower generation.
        hydropower_generation = actual_hydropower_generation
    
    else:
        # Calculate the hydropower generation of the conventional and pumped storage plants.
        hydropower_generation, __, __ = get_hydropower_generation(residual_demand, dataset, fraction_of_pumped_storage=fraction_of_pumped_storage, hours_at_full_power_consumption_capacity=hours_at_full_power_consumption_capacity)

        # Add the run-of-river hydropower generation.
        hydropower_generation = hydropower_generation + dataset['Run-of-river hydropower generation']
    
    # Convert the hydropower generation to a xarray.DataArray.
    if isinstance(hydropower_generation, pd.Series):
        hydropower_generation = hydropower_generation.to_xarray()
        
    # Calculate the residual demand considering wind, solar, and hydropower generation.
    residual_demand = residual_demand - hydropower_generation

    return residual_demand, mean_wind_generation, mean_solar_generation, hydropower_generation


def get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=True, fraction_of_pumped_storage=0, hours_at_full_power_consumption_capacity=8):
    '''
    Calculate the resource adequacy of the power supply given by the wind, solar, and hydropower generation in meeting the electricity demand.

    Parameters
    ----------
    country_info : dict
        Information of the country of interest.
    year : int
        Year of interest.
    dataset : xarray.Dataset
        Dataset containing the time series of the wind and solar capacity factors, the hydropower inflow and generation, and the electricity demand.
    wind_and_solar_generation_fractions : list
        List of the fractions of the electricity demand that are met in total by the wind and solar generation.
    wind_generation_fractions : list
        List of the fractions of the wind generation.
    use_actual_hydropower_generation : bool, optional
        If True, the actual hydropower generation is used. If False, the hydropower inflow is used to calculate the hydropower generation.
    fraction_of_pumped_storage : float, optional
        Fraction of the hydropower plants that are pumped storage plants.
        0 means that there are no pumped storage plants.
        1 means that the capacity of the pumped storage plants is equal to their current capacity.
        A value greater than 1 means that the capacity of the pumped storage plants is greater than their current capacity.
    downstream_reservoir_factor : float, optional
        Factor by which the maximum filling level of the downstream reservoirs of the pumped storage plants is multiplied.
    
    Returns
    -------
    resource_adequacy : numpy.ndarray
        Array containing the resource adequacy for each combination of the wind and solar generation fractions.
    '''

    # Initialize the resource adequacy matrix.
    unmet_demand = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions)))

    for ii, wind_and_solar_generation_fraction in enumerate(wind_and_solar_generation_fractions):
        for jj, wind_generation_fraction in enumerate(wind_generation_fractions):

            # Calculate the residual demand.
            residual_demand, __, __, __ = get_residual_demand(dataset, wind_and_solar_generation_fraction, wind_generation_fraction, use_actual_hydropower_generation=use_actual_hydropower_generation, fraction_of_pumped_storage=fraction_of_pumped_storage, hours_at_full_power_consumption_capacity=hours_at_full_power_consumption_capacity)

            # Calculate the unmet demand.
            unmet_demand[ii, jj] = residual_demand.where(residual_demand > 0, 0).sum()
    
    # Calculate the resource adequacy.
    resource_adequacy = 1 - unmet_demand/dataset['Electricity demand'].sum().values

    return resource_adequacy
import numpy as np
import pandas as pd
import xarray as xr

import atlite

import settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities
import modules.geospatial_utilities as geospatial_utilities
import modules.validation_utilities as validation_utilities
import modules.climate_data as climate_data


def get_runoff_time_series(region_shape, year):
    '''
    Read the climate data of a given year and convert them to the runoff time series for the given country.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Region of interest
    year : int
        Year of interest

    Returns
    -------
    time_series : xarray.DataArray
        Time series (longitude x latitude x time) of the runoff for the given year and country
    '''
    
    # Get the hydro database for the given year and region.
    hydro_database = climate_data.get_hydro_database(year, region_shape)

    # Convert the hydro database to the runoff time series.
    time_series = atlite.convert.convert_runoff(hydro_database, weight_with_height=False)

    return time_series


def compute_aggregated_hydropower_inflow(country_info):
    '''
    Compute and save the aggregated inflow for the given country and for all the years in the time period of interest.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    '''

    # Read the hydro power plants in Europe and select the ones in the country of interest.
    plants = pd.read_csv(settings.energy_data_directory+'/jrc-hydro-power-plant-database.csv')
    plants = plants.loc[plants['country_code'] == country_info['ISO Alpha-2']]

    # Select the type of plants. It can be 'HDAM' (hydro water reservois), 'HPHS' (hydro pumped storage), or 'HROR' (hydro run-of-river).
    # Water reservoirs and pumped storage hydro power plants are aggregated together because of the inflow into the reservoirs.
    plants = plants.loc[np.logical_or(plants['type'] == 'HDAM', plants['type'] == 'HPHS')]
    # plants = plants.loc[plants['type'] == 'HROR']

    # Read the hydro basins in Europe and select the ones that are upstream of the hydro power plants in the country of interest.
    all_basins = settings.energy_data_directory+'/hybas_eu_lev01-12_v1c/hybas_eu_lev08_v1c.shp'
    basins_of_interests = atlite.hydro.determine_basins(plants, all_basins)

    # Get the shape of the country of interest.
    region_shape = geometry.get_geopandas_region(country_info)

    # Determine the fraction of each grid cell that intersects with each basin (longitude x latitude x number of basins).
    fraction_of_grid_cell_in_each_basin = geospatial_utilities.get_fraction_of_grid_cell_in_shape(region_shape, basins_of_interests.shapes)

    for year in range(settings.aggregation_start_year, settings.aggregation_end_year+1):

        # Calculate the time series of the inflow for the given year and country.
        runoff_time_series = get_runoff_time_series(region_shape, year)

        # Aggregate the time series of the runoff for each basin. The result is an xarray DataSet with one time series for each basin.
        aggregated_runoff_per_basin = general_utilities.aggregate_time_series(runoff_time_series, fraction_of_grid_cell_in_each_basin)

        # Convert the aggregated time series of the runoff for each basin to an xarray DataArray.
        aggregated_runoff_per_basin = aggregated_runoff_per_basin.to_array(dim='hid')
        aggregated_runoff_per_basin['hid'] = aggregated_runoff_per_basin['hid'].values.astype('int')
        
        # The runoff is in units of m. It should be multiplied by the water density and the basin area to convert to kg.
        aggregated_runoff_per_basin *= 1000.0*xr.DataArray(basins_of_interests.shapes.to_crs(dict(proj="cea")).area)

        # Aggregate the time series of the runoff for each basin to the belonging power plant. The result is an xarray DataArray with one time series for each plant.
        aggregated_inflow_per_plant = atlite.hydro.shift_and_aggregate_runoff_for_plants(basins_of_interests, aggregated_runoff_per_basin, flowspeed=1)
        
        # Sum the inflow time series of all the plants.
        aggregated_inflow = aggregated_inflow_per_plant.sum(dim='plant')

        if settings.read_hydropower_coefficients: 
            # Read the hydropower calibration coefficients.
            retain_factors = validation_utilities.read_calibration_coefficients(country_info, 'hydropower', additional_info='__conventional_and_pumped_storage')

            # Map the retain factors (one for each month) to the time series of the inflow (one for each time step).
            mapped_retain_factors = pd.Series(data=retain_factors[aggregated_inflow.time.dt.month-1].values, index=aggregated_inflow.time)

            # Calibrate the simulated hydropower inflow time series.
            aggregated_inflow = aggregated_inflow*mapped_retain_factors

        # Add attributes to the aggregated time series.
        aggregated_inflow = aggregated_inflow.rename('Hydropower inflow')
        aggregated_inflow = aggregated_inflow.assign_attrs(units='kg/h', description="Mass flow rate of water into the reservoirs")

        # Save the aggregated inflow.
        general_utilities.save_time_series(aggregated_inflow, country_info, 'hydropower__inflow_time_series__conventional_and_pumped_storage')
        # general_utilities.save_time_series(aggregated_inflow, country_info, 'hydropower__inflow_time_series__run_of_river')
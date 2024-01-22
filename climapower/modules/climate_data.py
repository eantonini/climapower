import numpy as np
import xarray as xr

import atlite

import settings
import modules.directories as directories
import modules.climate_utilities as climate_utilities


def get_wind_database(year, region_shape):
    '''
    Read the wind speed and surface roughness of a given year and region.

    Parameters
    ----------
    year : int
        Year of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest

    Returns
    -------
    ds : xarray.Dataset
        Dataset (longitude x latitude x time) containing the wind speed and surface roughness for each grid cell in the focus region
    '''
    
    if settings.climate_data_source == 'historical':
        
        # Define the name of the variables to load.
        variable_names = ['100m_u_component_of_wind', '100m_v_component_of_wind', 'forecast_surface_roughness']

        # Load the climate data for the given year and region.
        [ds_u100, ds_v100, ds_fsr] = climate_utilities.load_climate_data(year, region_shape, variable_names)
        
        # Merge the datasets.     
        ds = xr.merge([ds_u100, ds_v100, ds_fsr])
        
        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds['wnd100m'] = np.sqrt(ds['u100'] ** 2 + ds['v100'] ** 2).assign_attrs(units=ds['u100'].attrs['units'])
        ds = ds.drop_vars(['u100', 'v100'])

    elif settings.climate_data_source == 'projections':

        # Define the name of the variables to load.
        variable_names = ['10m_wind_speed', 'forecast_surface_roughness']

        # Load the climate data for the given year and region.
        [ds_ws10, ds_r] = climate_utilities.load_climate_data(year, region_shape, variable_names, CORDEX_data=True)
        
        # Harmonize the data to hourly resolution and merge the datasets.
        ds = climate_utilities.harmonize_cordex_data([ds_ws10, ds_r], year, '3 hours')
        
        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds_ws10 = ds_ws10.rename({'10m_wind_speed': 'wnd10m'})
    
    else:
        
        raise AssertionError('The climate data source is not valid.')
    
    # Rename variable to match the atlite convention.
    ds = ds.rename({'fsr': 'roughness'})
    
    return ds


def get_solar_database(year, region_shape):
    '''
    Read the solar radiation and temperature of a given year and region.

    Parameters
    ----------
    year : int
        Year of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest

    Returns
    -------
    ds : xarray.Dataset
        Dataset (longitude x latitude x time) containing the solar radiation and temperature for each grid cell in the focus region
    '''
    
    if settings.climate_data_source == 'historical':

        # Define the name of the variables to load.
        variable_names = ['surface_net_solar_radiation', 'surface_solar_radiation_downwards', 'toa_incident_solar_radiation', 'total_sky_direct_solar_radiation_at_surface', '2m_temperature']

        # Load the climate data for the given year and region.
        [ds_ssr, ds_ssrd, ds_tisr, ds_fdir, ds_t2m] = climate_utilities.load_climate_data(year, region_shape, variable_names)

        # Convert solar energy to power.
        [ds_ssr, ds_ssrd, ds_tisr, ds_fdir] = climate_utilities.convert_solar_energy_to_power([ds_ssr, ds_ssrd, ds_tisr, ds_fdir])

        # Calculate solar energy at the midpoint of the time step.
        ds = climate_utilities.harmonize_era5_solar_data([ds_ssr, ds_ssrd, ds_tisr, ds_fdir], year)

        # Merge the datasets.
        ds = xr.merge([ds, ds_t2m])
        
        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'fdir': 'influx_direct', 'tisr': 'influx_toa', 't2m': 'temperature'})

        # Calculate the albedo.
        ds['albedo'] = ((ds['ssrd'] - ds['ssr']) / ds['ssrd'].where(ds['ssrd'] != 0)).fillna(0.0)
        ds['albedo'] = ds['albedo'].assign_attrs(units='(0 - 1)', long_name='Albedo')
        
        # Calculate the diffuse solar radiation.
        ds['influx_diffuse'] = ds['ssrd'] - ds['influx_direct']
        ds['influx_diffuse'] = ds['influx_diffuse'].assign_attrs(units='J m**-2', long_name='Surface diffuse solar radiation downwards')

        # Drop variables that are not needed.
        ds = ds.drop_vars(['ssrd', 'ssr'])

    elif settings.climate_data_source == 'projections':

        # Define the name of the variables to load.
        variable_names = ['surface_solar_radiation_downwards', 'surface_upwelling_shortwave_radiation', '2m_air_temperature', 'toa_incident_solar_radiation']

        # Load the climate data for the given year and region.
        [ds_rsds, ds_rsus, ds_tas, ds_tisr] = climate_utilities.load_climate_data(year, region_shape, variable_names, CORDEX_data=True)

        # Drop the height coordinate.
        ds_tas = ds_tas.drop('height')

        # Harmonize the data to hourly resolution and merge the datasets.
        ds = climate_utilities.harmonize_cordex_data([ds_rsds, ds_rsus, ds_tas], year, '3 hours')

        # Set the correct time coordinate for the TOA incident solar radiation.
        ds_tisr['time'] = ds['time']

        # Convert solar energy to power.
        [ds_tisr] = climate_utilities.convert_solar_energy_to_power([ds_tisr])

        # Calculate solar energy at the midpoint of the time step and merge with other dataset.
        ds = xr.merge([ds, climate_utilities.harmonize_era5_solar_data([ds_tisr], year)])
        
        # Note: regridded CORDEX variables are zero in the bottom cornerns of the domain. This may cause a warning when dividing by zero.
        
        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'surface_solar_radiation_downwards': 'influx', 'surface_upwelling_shortwave_radiation': 'outflux', 'tisr': 'influx_toa', '2m_air_temperature': 'temperature'})
    
    else:
        
        raise AssertionError('The climate data source is not valid.')
    
    # Unify chuncks
    ds = ds.unify_chunks()

    # Calculate the solar position.
    sp = atlite.pv.solar_position.SolarPosition(ds) # type: ignore
    sp = sp.rename({v: f'solar_{v}' for v in sp.data_vars})
    
    # Merge the solar position dataset with the climate data dataset.
    ds = xr.merge([ds, sp])

    # Unify chuncks
    ds = ds.unify_chunks()
    
    return ds


def get_temperature_database(year, region_shape):
    '''
    Read the temperature of a given year and region.

    Parameters
    ----------
    year : int
        Year of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest

    Returns
    -------
    ds : xarray.Dataset
        Dataset (longitude x latitude x time) containing the temperature for each grid cell in the focus region
    '''

    if settings.climate_data_source == 'historical':

        # Define the name of the variables to load.
        variable_names = ['2m_temperature']

        # Load the climate data for the given year and region.
        [ds] = climate_utilities.load_climate_data(year, region_shape, variable_names)

        # Rename variables and clean coordinates to match the atlite convention.    
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'t2m': 'temperature'})

    elif settings.climate_data_source == 'projections':

        # Define the name of the variables to load.
        variable_names = ['2m_air_temperature']

        # Load the climate data for the given year and region.
        [ds_tas] = climate_utilities.load_climate_data(year, region_shape, variable_names, CORDEX_data=True)
        
        # Drop the height coordinate.
        ds_tas = ds_tas.drop('height')

        # Harmonize the data to hourly resolution.
        ds = climate_utilities.harmonize_cordex_data([ds_tas], year, '3 hours')
        
        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'2m_air_temperature': 'temperature'})
    
    else:
        
        raise AssertionError('The climate data source is not valid.')
    
    return ds


def get_hydro_database(year, region_shape):
    '''
    Read the runoff of a given year and region.

    Parameters
    ----------
    year : int
        Year of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest

    Returns
    -------
    ds : xarray.Dataset
        Dataset (longitude x latitude x time) containing the runoff for each grid cell in the focus region
    '''

    if settings.climate_data_source == 'historical':

        # Define the name of the variables to load.
        variable_names = ['runoff', 'height']

        # Load the climate data for the given year and region.
        [ds_ro, ds_z] = climate_utilities.load_climate_data(year, region_shape, variable_names)
        
        # Merge the datasets.
        ds = xr.merge([ds_ro, ds_z])

        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'ro': 'runoff', 'z': 'height'})

    elif settings.climate_data_source == 'projections':

        # Define the name of the variables to load.
        variable_names = ['total_run_off_flux', 'height']

        # Load the climate data for the given year and region.
        [ds_ro, ds_z] = climate_utilities.load_climate_data(year, region_shape, variable_names, CORDEX_data=True)
        
        # Harmonize the data to hourly resolution and merge the datasets.
        ds = climate_utilities.harmonize_cordex_data([ds_ro, ds_z], year, '6 hours')

        # Rename variables and clean coordinates to match the atlite convention.
        ds = climate_utilities.rename_and_clean_coords(ds)
        ds = ds.rename({'total_run_off_flux': 'runoff', 'z': 'height'})
    
    else:
        
        raise AssertionError('The climate data source is not valid.')
    
    return ds


def get_regional_resource_availability(resource_type):
    '''
    Read resource availability file (e.g., mean wind power density or surface solar radiation)

    Parameters
    ----------
    resource_type : str
        Type of resource of interest ('wind' or 'solar')

    Returns
    -------
    resource_availability : xarray.Dataset
        Dataset (longitude x latitude) containing the resource availability for each grid cell in the focus region
    '''
    
    # Define the targe resource name and the variable of the loaded dataset to rename.
    if resource_type == 'wind':

        resource = '100m_wind_power_density'
        variable_to_rename = '__xarray_dataarray_variable__'

    elif resource_type == 'solar':

        resource = 'surface_solar_radiation_downwards'
        variable_to_rename = 'ssrd'
    
    else:

        raise AssertionError('Resource type not recognized or implemented')
    
    # Read the resource availability path.
    resource_path = directories.get_mean_climate_data_path(resource)
    
    # Read the resource availability dataset.
    resource_availability = xr.open_dataset(resource_path, engine='netcdf4')

    # Rename variables to match the atlite convention and the rest of the code.
    resource_availability = resource_availability.rename({variable_to_rename: 'resource_availability', 'longitude': 'x', 'latitude': 'y'})

    # Reverse the latitude dimension to match the atlite convention. 
    resource_availability = resource_availability.reindex(y=list(reversed(resource_availability.y)))
    
    return resource_availability
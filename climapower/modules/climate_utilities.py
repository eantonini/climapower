import numpy as np
import xarray as xr
import pandas as pd

import atlite

import settings
import modules.directories as directories


def maybe_swap_spatial_dims(ds, namex='x', namey='y'):
    '''
    Swap order of spatial dimensions according to atlite convention.
    Coordinates are swapped if they are in descending order.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray to be swapped
    namex : str, optional
        Name of x coordinate. The default is 'x'
    namey : str, optional
        Name of y coordinate. The default is 'y'

    Returns
    -------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray with swapped coordinates
    '''
    
    # Define the dictionary of dimensions to be swapped.
    swaps = {}

    # Get the left and right index of the x dimension.
    lx, rx = ds.indexes[namex][[0, -1]]

    # Get the lower and upper index of the y dimension.
    ly, uy = ds.indexes[namey][[0, -1]]

    # Check which dimension needs to be swapped and add it to the dictionary.
    if lx > rx:
        swaps[namex] = slice(None, None, -1)
    if uy < ly:
        swaps[namey] = slice(None, None, -1)

    # Apply the swap.
    ds = ds.isel(**swaps) if swaps else ds

    return ds


def rename_and_clean_coords(ds):
    '''
    Rename 'longitude' and 'latitude' coordinates to 'x' and 'y' and fix roundings.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray to be renamed
    
    Returns
    -------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray with renamed coordinates
    '''
    
    # Rename longitude and latitude coordinates to x and y coordinates.
    ds = ds.rename({'longitude': 'x', 'latitude': 'y'})

    # Round coords since original coordinates are float32, which would lead to mismatches.
    ds = ds.assign_coords(x=np.round(ds.x.astype(float), 5), y=np.round(ds.y.astype(float), 5))

    # Swap spatial dimensions if necessary.
    ds = maybe_swap_spatial_dims(ds)

    # Keep original longitude and latitude coordinates.
    ds = ds.assign_coords(lon=ds.coords["x"], lat=ds.coords["y"])

    return ds


def clip_to_region_containing_box(ds, region_shape):
    '''
    Clip dataset extension to region containing box.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray to be clipped
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    
    Returns
    -------
    ds : xarray.Dataset or xarray.DataArray
        Dataset or DataArray clipped to region containing box
    '''
    
    # Calculate the lateral bounds of the region of interest including a buffer layer of one degree.
    region_bounds = region_shape.unary_union.buffer(1).bounds
    
    # Clip the dataset to the region containing box.
    if 'x' in ds.coords and 'y' in ds.coords:
        ds = ds.sel(x=slice(region_bounds[0],region_bounds[2]), y=slice(region_bounds[3], region_bounds[1]))
    
    elif 'longitude' in ds.coords and 'latitude' in ds.coords:
        ds = ds.sel(longitude=slice(region_bounds[0],region_bounds[2]), latitude=slice(region_bounds[3], region_bounds[1]))

    return ds


def create_temporary_cutout(region_shape):
    '''
    Create a temporary cutout for a given region.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest

    Returns
    -------
    cutout : atlite.Cutout
        Cutout for the given region
    '''

    # Calculate the lateral bounds for the cutout based on the lateral bounds of the region of interest including a buffer layer of one degree.
    cutout_bounds = region_shape.unary_union.buffer(1).bounds
    
    # Create the cutout.
    cutout = atlite.Cutout('temporary_cutout_for_'+region_shape.index[0], module='era5', bounds=cutout_bounds, time=slice('2013-01-01', '2013-01-02'))

    return cutout


def harmonize_era5_solar_data(variable_datasets, year):
    '''
    Calculate ERA5 solar data at the midpoint of the time step. This is necessary because the data is given as the integral over the time step with the value at the end of the time step.

    Parameters
    ----------
    variable_datasets : list of xarray.Dataset
        List of datasets containing the variables of interest
    year : int
        Year of interest

    Returns
    -------
    ds : xarray.Dataset
        Dataset containing the harmonized data
    '''
    
    # Define the target time coordinate.
    target_time = pd.date_range(str(year), str(year+1), freq='H')[:-1]
    
    # Define the actual time coordinate of the original data with an additional element at the end.
    actual_time = pd.date_range(str(year), str(year+1), freq='H')[:-1] + pd.to_timedelta('-30 minutes')
    actual_time = actual_time.insert(len(actual_time), actual_time[-1] + pd.to_timedelta('60 minutes'))
    
    # Define the dataset containing the harmonized data.
    ds = xr.Dataset()

    # For each dataset in the list, and for each variable in the dataset, perform the caclulation.
    for variable_dataset in variable_datasets:

        for variable_name in list(variable_dataset.data_vars):

            if 'time' in variable_dataset[variable_name].dims:

                # Create an additional element to be places at the end of the original dataset. This element is equal to the first element of the original dataset.
                extend_right = variable_dataset[variable_name].loc[variable_dataset['time']==variable_dataset['time'][0]]
                extend_right['time'] = np.atleast_1d(variable_dataset['time'][-1] + pd.to_timedelta('60 minutes'))
                
                # Add the additional element to the original dataset. 
                extended_data = xr.combine_by_coords([variable_dataset[variable_name], extend_right])[variable_name]
                extended_data['time'] = actual_time

                # Interpolate values to the target time coordinate.
                ds[variable_name] = extended_data.interp(time=target_time)

            else:

                ds[variable_name] = variable_dataset[variable_name]
    
    return ds


def harmonize_cordex_data(variable_datasets, year, resolution):
    '''
    Upsample CORDEX data from 3- or 6-hourly to hourly resolution by linear interpolation.

    Parameters
    ----------
    variable_datasets : list of xarray.Dataset
        List of datasets containing the variables of interest
    year : int
        Year of interest
    resolution : str
        Resolution of the original data (e.g., '3 hours')

    Returns
    -------
    ds : xarray.Dataset
        Dataset containing the harmonized data
    '''
    
    # Define the target time coordinate.
    target_time = pd.date_range(str(year), str(year+1), freq='H')[:-1]
    
    # Define the dataset containing the harmonized data.
    ds = xr.Dataset()

    # For each dataset in the list, and for each variable in the dataset, perform the caclulation.
    for variable_dataset in variable_datasets:

        for variable_name in variable_dataset.data_vars:

            if 'time' in variable_dataset[variable_name].dims:

                # Create additional elements to be placed at the beginning and end of the original dataset. The elements are equal to the last and first elements of the original dataset.
                extend_left = variable_dataset[variable_name].loc[variable_dataset['time']==variable_dataset['time'][-1]]
                extend_left['time'] = np.atleast_1d(variable_dataset['time'][0] + pd.to_timedelta('-'+resolution))
                extend_right = variable_dataset[variable_name].loc[variable_dataset['time']==variable_dataset['time'][0]]
                extend_right['time'] = np.atleast_1d(variable_dataset['time'][-1] + pd.to_timedelta(resolution))
                
                # Add the additional elements to the original dataset.
                extended_data = xr.combine_by_coords([extend_left, variable_dataset[variable_name], extend_right])[variable_name]

                # Interpolate values to the target time coordinate.
                ds[variable_name] = extended_data.interp(time=target_time)

            else:

                ds[variable_name] = variable_dataset[variable_name]
    
    return ds


def convert_solar_energy_to_power(variable_datasets):
    '''
    Convert solar energy to power by dividing by the length of the time step.

    Parameters
    ----------
    variable_datasets : list of xarray.Dataset
        List of datasets containing the variables of interest

    Returns
    -------
    converted_variable_datasets : list of xarray.Dataset
        List of datasets containing the converted variables of interest
    '''
    
    # Define the list of datasets containing the converted variables of interest.
    converted_variable_datasets = []

    for variable_dataset in variable_datasets:

        for variable_name in variable_dataset.data_vars:

            # Convert the variable of interest to power by dividing by the length of the time step.
            variable_dataset[variable_name] = variable_dataset[variable_name] / (60.0 * 60.0)
            variable_dataset[variable_name].attrs['units'] = 'W m**-2'

        converted_variable_datasets.append(variable_dataset)
    
    return converted_variable_datasets


def load_climate_data(year, region_shape, variable_names, CORDEX_data=False):
    '''
    Load climate data for a given year and region.
    
    Parameters
    ----------
    year : int
        Year of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    variable_names : list of str
        List of variable names of interest
    CORDEX_data : bool, optional
        True if the data is CORDEX data, by default False

    Returns
    -------
    variable_datasets : list of xarray.Dataset
        List of datasets containing the variables of interest
    '''

    # Define the list of datasets containing the variables of interest.
    variable_datasets = []

    # For each variable of interest, load the corresponding dataset.
    for variable_name in variable_names:

        if variable_name == 'toa_incident_solar_radiation' and CORDEX_data:
            variable_dataset = xr.open_dataset(directories.get_tisr_path_for_cordex(year), chunks=settings.chunk_size_lon_lat)
        
        elif variable_name == 'forecast_surface_roughness' and CORDEX_data:
            variable_dataset = xr.open_dataset(directories.get_mean_climate_data_path('forecast_surface_roughness'), chunks=settings.chunk_size_lon_lat)
        
        elif variable_name == 'total_run_off_flux' and CORDEX_data:
            variable_dataset = xr.open_dataset(directories.get_climate_data_path(year, variable_name), chunks=settings.chunk_size_lon_lat, CORDEX_time_resolution='6hourly')
        
        elif variable_name == 'height':
            variable_dataset = xr.open_dataset(settings.climate_data_directory+'/'+'ERA5-geopotential.nc', chunks=settings.chunk_size_lon_lat)
            variable_dataset = variable_dataset/9.80665
        
        else:
            variable_dataset = xr.open_dataset(directories.get_climate_data_path(year, variable_name), chunks=settings.chunk_size_lon_lat)
        
        # Clip the dataset to the region bounding box.
        variable_dataset = clip_to_region_containing_box(variable_dataset, region_shape)

        # Add the dataset to the list.
        variable_datasets.append(variable_dataset)

    return variable_datasets
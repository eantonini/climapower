import numpy as np
import xarray as xr

import atlite

import settings
import modules.geometry as geometry
import modules.exclusion as exclusion
import modules.climate_utilities as climate_utilities
import modules.climate_data as climate_data
import modules.basic_figures as figures


def get_eligible_fraction(region_shape, excluder):
    '''
    Calculate fraction of the total eligible land and plot that on a map.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        GeoDataFrame containing the information of the region of interest
    excluder : atlite.gis.ExclusionContainer
        Exclusion container containing the exclusion areas

    Returns
    -------
    eligible_share : float
        Fraction of eligible land
    '''
    
    # Convert the region to the same coordinate reference system as the excluder.
    region_shape_with_new_crs = region_shape.geometry.to_crs(excluder.crs)

    # Calculate a masked array (True where the region is eligible, False where it is not) and the transform to convert the masked array to the same coordinate reference system as the excluder.
    masked, transform = atlite.gis.shape_availability(region_shape_with_new_crs, excluder)

    # Calculate the eligible share.
    eligible_share = np.float64(masked.sum()) * np.float64(excluder.res**2) / np.float64(region_shape_with_new_crs.geometry.item().area)
    
    # Plot the eligible area.
    if settings.make_plots:
        figures.plot_eligible_fraction(region_shape, region_shape_with_new_crs, masked, transform, eligible_share)
    
    return eligible_share


def get_availability_matrix(region_shape, excluder):
    '''
    Calculate the availability matrix of the region of interest.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        GeoDataFrame containing the information of the region of interest
    excluder : atlite.gis.ExclusionContainer
        Exclusion container containing the exclusion areas

    Returns
    -------
    availability_matrix : xarray.DataArray
        Availability matrix (1 x longitude x latitude) of the region of interest with a value between 0 and 1 for each grid cell
    '''
    
    # Create a temporary cutout to calculate the availability matrix.
    cutout = climate_utilities.create_temporary_cutout(region_shape)

    # Calculate the availability matrix.
    availability_matrix = cutout.availabilitymatrix(region_shape, excluder)
    
    return availability_matrix


def get_fraction_of_grid_cell_in_shape(region_shape, shapes):
    '''
    Calculate the fraction of each grid cell that is in the given shapes.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        GeoDataFrame containing the information of the region of interest
    shapes : geopandas.GeoDataFrame
        GeoDataFrame containing the information of the shapes of interest

    Returns
    -------
    fraction_of_grid_cells_in_shape : xarray.DataArray
        Fraction of each grid cell that is in the given shapes (number of shapes x longitude x latitude)
    '''

    # Create a temporary cutout to have the grid cell of the region of interest.
    cutout = climate_utilities.create_temporary_cutout(region_shape)
    
    # Calculate the fraction of each grid cell that is in the given shapes.
    fraction_of_grid_cells_in_shape = cutout.indicatormatrix(shapes)
    
    # Fix NaN and Inf values to 0.0 to avoid numerical issues.
    fraction_of_grid_cells_in_shape = np.nan_to_num(fraction_of_grid_cells_in_shape / fraction_of_grid_cells_in_shape.sum(axis=1), nan=0.0, posinf=0.0, neginf=0.0)

    # Covert the indicator matrix to an xarray DataSet, with each data variable being a line of the indicator matrix.
    fraction_of_grid_cells_in_shape_np = np.array(fraction_of_grid_cells_in_shape)
    fraction_of_grid_cells_in_shape = xr.Dataset(coords={'x': cutout.data['x'], 'y': cutout.data['y']})
    for ii in range(len(fraction_of_grid_cells_in_shape_np)):
        fraction_of_grid_cells_in_shape[str(shapes.index[ii])] = (('y', 'x'), fraction_of_grid_cells_in_shape_np[ii].reshape(len(cutout.data['y']),len(cutout.data['x'])))
    
    # Multiply by the grid cell areas.
    cell_areas = geometry.get_grid_cell_area()
    fraction_of_grid_cells_in_shape = fraction_of_grid_cells_in_shape * cell_areas
    
    fraction_of_grid_cells_in_shape = fraction_of_grid_cells_in_shape.chunk(settings.chunk_size_x_y)

    return fraction_of_grid_cells_in_shape


def exctact_available_cells_with_best_resource(region_shape, availability_matrix, region_matrix, eligible_fraction, resource_type):
    '''
    Calculate the availability factor of all cells, the cells belonging to region, and the cells wuth best resource.

    Parameters
    ----------
    region : geopandas.GeoDataFrame
        GeoDataFrame containing the information of the region of interest
    availability_matrix : xarray.DataArray
        Availability matrix (1 x longitude x latitude) of the region of interest with a value between 0 and 1 for each grid cell
    region_matrix : xarray.DataArray
        Availability matrix (1 x longitude x latitude) of the region of interest identifying the cells belonging to the region of interest
    eligible_fraction : float
        Fraction of total eligible land
    resource_type : str
        Type of resource ('wind' or 'solar')

    Returns
    -------
    cells_with_availability_factor : xarray.DataArray
        Overall availability factor of all cells (longitude x latitude)
    cells_with_best_resource : xarray.DataArray
        Cells with the best resource (longitude x latitude)
    '''
    
    # Get the resource availability data (mean capacity factor for wind, mean irradiation for solar).
    resource_availability = climate_data.get_regional_resource_availability(resource_type)
    
    # Clean the availability matrixes.
    cells_with_availability_factor = availability_matrix.sel(name=region_shape.index[0]).drop('name').rename('Availability factor')
    cells_belonging_to_region = region_matrix.sel(name=region_shape.index[0]).drop('name').rename('Region')
    
    # Calculate the grid cell areas and clip their spatial extent to the bounding box of the country of interest.
    cell_areas = geometry.get_grid_cell_area()
    regional_cell_areas = cell_areas.sel(x=slice(availability_matrix.x.min(),availability_matrix.x.max()),y=slice(availability_matrix.y.min(),availability_matrix.y.max()))
    
    # Clip the cells with resource availability to the bounding box of the country of interest and set them to zero where the cells do not belong to the region of interest.
    regional_resource_availability = resource_availability.sel(x=slice(availability_matrix.x.min(),availability_matrix.x.max()),y=slice(availability_matrix.y.min(),availability_matrix.y.max()))
    regional_resource_availability = regional_resource_availability.where(cells_belonging_to_region>0)
    
    # Calculate the total surface area of the region of interest.
    total_surface_area = (cells_belonging_to_region*regional_cell_areas).sum().values
    
    # Calculate the cells with best resource that multiplied by the cells with availability factor give a total land fraction of 0.25.
    if eligible_fraction > 0.25:

        # Initialize the fraction of surface available with best resource and the fraction of surface with best resource.
        fraction_of_surface_available_with_best_resource = 0
        fraction_of_surface_with_best_resource = 0.25

        # Increase the fraction of surface with best resource until the fraction of surface available with best resource is equal or larger than 0.25.
        while fraction_of_surface_available_with_best_resource < 0.25:

            # Set to 0 the cells that are not in top 25% best resource in the available land. Then set to 1 the cells that are not 0.
            cells_with_best_resource = regional_resource_availability.resource_availability.where(regional_resource_availability.resource_availability>regional_resource_availability.resource_availability.quantile(1-fraction_of_surface_with_best_resource).values, 0)
            cells_with_best_resource = cells_with_best_resource.where(cells_with_best_resource==0, 1)

            # Calculate the fraction of surface available with best resource.
            fraction_of_surface_available_with_best_resource = ((cells_with_best_resource*cells_with_availability_factor*regional_cell_areas).sum()/total_surface_area).values

            # Increase the fraction of surface with best resource.
            fraction_of_surface_with_best_resource += 0.01
        
    else:

        # If the eligible fraction is smaller than 0.25, all the cells with best resource are the cells belonging to region.
        cells_with_best_resource = cells_belonging_to_region
    
    # Rename the variable.
    cells_with_best_resource = cells_with_best_resource.rename('Index') # type: ignore
    
    # Plot the cells belonging to region, the cells with availability factor, and the cells with best resource.
    if settings.make_plots:
        figures.plot_cells(region_shape, cells_belonging_to_region, 'cells_belonging_to_region', 'Greens')
        figures.plot_cells(region_shape, cells_with_availability_factor, 'cells_with_availability_factor', 'Greens')
        figures.plot_cells(region_shape, cells_with_best_resource, 'cells_with_best_resource', 'Blues')
        
    return cells_with_availability_factor, cells_with_best_resource


def get_cells_of_interest(country_info, resource_type, offshore=False):
    '''
    Get region shape, set exclusion areas, calculate the availability factor of the grid cells, and the cells with best resource.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    resource_type : str
        Type of resource ('wind' or 'solar')
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    cells_with_availability_factor : xarray.DataArray
        Availability factor of all cells (longitude x latitude) in the bounding box of the country of interest
    '''
    
    # Get the region of interest.
    region_shape = geometry.get_geopandas_region(country_info, offshore)

    # Create an exclusion container. The coordinate reference system code 3035 is only valid in Europe.
    excluder = atlite.gis.ExclusionContainer(crs=3035)

    # Add the exclusion areas to the exclusion container depending on the resource type.
    excluder = exclusion.exclude_areas(country_info, excluder, resource_type, offshore)
    
    # Create an inclusion container to identify the region under consideration.
    region_includer = atlite.gis.ExclusionContainer(crs=3035)
    region_includer.add_geometry(geometry.get_containing_geopandas_box(region_shape), invert=True)

    # Calculate the fraction of the total eligible land.
    eligible_fraction = get_eligible_fraction(region_shape, excluder)

    # Calculate the availability matrix considering the exclusion areas.
    availability_matrix = get_availability_matrix(region_shape, excluder)

    # Calculate the availability matrix considering only the region of interest.
    region_matrix = get_availability_matrix(region_shape, region_includer)
    
    # Calculate the overall availability factor of the grid cells and the cells with best resource.
    cells_with_availability_factor, cells_with_best_resource = exctact_available_cells_with_best_resource(region_shape, availability_matrix, region_matrix, eligible_fraction, resource_type)
    
    return cells_with_availability_factor, cells_with_best_resource


def get_weights_for_wind_or_solar_aggregation(country_info, resource_type, offshore=False):
    '''
    Get the weights (longitude x latitude) used to aggregate the time series for wind or solar capacity factor.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    resource_type : str
        Type of resource ('wind' or 'solar')
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    weights : xarray.DataArray
        Weights (longitude x latitude) used to aggregate the time series dataset
    '''
    
    # Get cells with availability factor (longitude x latitude) and cells with best resource (longitude x latitude) in the bounding box of the country of interest.
    # The availability factor is the fraction of the cell available for wind/solar power plants (value from 0 to 1).
    # The cells with the best resource are the cells with the 25% highest wind/solar resource (value of 0 or 1).
    cells_with_availability_factor, cells_with_best_resource = get_cells_of_interest(country_info, resource_type, offshore)

    # Get the cell areas of all grid cells (longitude x latitude) and select the ones in the bounding box of the country of interest.
    cell_areas = geometry.get_grid_cell_area()
    regional_cell_areas = cell_areas.sel(x=slice(cells_with_availability_factor.x.min(),cells_with_availability_factor.x.max()),y=slice(cells_with_availability_factor.y.min(),cells_with_availability_factor.y.max()))

    # Calculate the weights used to aggregate the time series (longitude x latitude).
    weights = cells_with_best_resource*cells_with_availability_factor*regional_cell_areas

    return weights


def get_population_density(country_info):
    '''
    Get the population density of a specific country.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest

    Returns
    -------
    population_density : xarray.DataArray
        Population density (longitude x latitude) of the country of interest
    '''

    # Get the shape of the region of interest and its lateral bounds.
    region_shape = geometry.get_geopandas_region(country_info)
    
    # Read the population density data.
    population_density = xr.open_dataarray(settings.geospatial_data_directory+'/Population_density/GHS_POP_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif', engine='rasterio')

    # Select the population density data in the bounding box of the country of interest.
    population_density = climate_utilities.clip_to_region_containing_box(population_density, region_shape)

    # Swap the spatial dimensions if necessary.
    population_density = climate_utilities.maybe_swap_spatial_dims(population_density)

    # Coarsen the population density data to the same resolution as the climate data. The population density resolution is 30 arc-seconds, while the resource data resolution is 900 arc-seconds (0.25 degrees).
    
    # Define the new coarser resolution.
    x_list = np.linspace(-180, 180, int(360/0.25)+1)
    y_list = np.linspace(-90, 90, int(180/0.25)+1)

    # Calculate the lateral bounds of the region of interest including a buffer layer of one degree.
    region_bounds = region_shape.unary_union.buffer(1).bounds # type: ignore

    # Define the bins where to aggregate the population density data of the finer resolution.
    # The next(...) function in this case calculates the first value that satisfies the specified condition.
    # The resulting bins are the first and last values of the x_list and y_list that are within the bounds of the region of interest.
    x_bins = np.arange(x_list[next(x for x, val in enumerate(x_list) if val > region_bounds[0])]+0.25/2,
                       x_list[next(x for x, val in enumerate(x_list) if val > region_bounds[2])+1]-0.25/2, 0.25)
    y_bins = np.arange(y_list[next(x for x, val in enumerate(y_list) if val > region_bounds[1])]+0.25/2, 
                       y_list[next(x for x, val in enumerate(y_list) if val > region_bounds[3])+1]-0.25/2, 0.25)
    
    # Aggregate the population density data to the new coarser resolution, first in the x direction and then in the y direction.
    population_density = population_density.groupby_bins('x', x_bins).sum()
    population_density = population_density.groupby_bins('y', y_bins).sum()

    # For each coordinate, substitute the bin range with the middle of the bins.
    population_density['x_bins'] = np.arange(x_list[next(x for x, val in enumerate(x_list) if val > region_bounds[0])+1], 
                                             x_list[next(x for x, val in enumerate(x_list) if val > region_bounds[2])], 0.25)
    population_density['y_bins'] = np.arange(y_list[next(x for x, val in enumerate(y_list) if val > region_bounds[1])+1], 
                                             y_list[next(x for x, val in enumerate(y_list) if val > region_bounds[3])], 0.25)
    
    # Rename coordinates and clean the dataset.
    population_density = population_density.rename({'x_bins': 'x', 'y_bins': 'y'})
    population_density = population_density.squeeze('band')
    population_density = population_density.drop(['band', 'spatial_ref']) # type: ignore
    
    return population_density
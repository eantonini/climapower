import numpy as np
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import cartopy.io.shapereader as shpreader

import settings
import modules.basic_figures as figures


def get_geopandas_region(country_info, offshore=False):
    '''
    Get region shape from cartopy, convert it to a geoDataFrame, and plot it.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    offshore : bool
        True if analyzing offshore wind

    Returns
    -------
    region_shape : geopandas.GeoDataFrame
        GeoDataFrame containing the region of interest
    '''
    
    if offshore:
        # Load the shapefile containing the European continental maritime areas.
        region_shapes = settings.geospatial_data_directory+'/European_continental_maritime_areas/EuropeanContinentalMaritimeAreas_Level0_v1.1.shp'

        # Define specific search attributes.
        dataset_attribute = 'ISO_Ter1'
        backup_dataset_attribute = 'Territory1'
    else:
        # Load the shapefile containing the world countries.
        region_shapes = shpreader.natural_earth(resolution='50m', category='cultural', name='admin_0_countries')

        # Define specific search attributes.
        dataset_attribute = 'ISO_A3_EH'
        backup_dataset_attribute = 'NAME'
    
    # Define a reader for the shapefile.
    reader = shpreader.Reader(region_shapes)

    try:

        try:
            # Read the shape of the region of interest by searching for the ISO Alpha-3 code.
            region_shape = [ii for ii in list(reader.records()) if ii.attributes[dataset_attribute] == country_info['ISO Alpha-3']][0]
        except:
            # Read the shape of the region of interest by searching for the country name.
            region_shape = [ii for ii in list(reader.records()) if ii.attributes[backup_dataset_attribute] == country_info['Name']][0]
        
        # Convert the shape to a GeoDataFrame.
        region_shape = pd.Series({'geometry': region_shape.geometry})
        region_shape = gpd.GeoSeries(region_shape)
        region_shape = gpd.GeoDataFrame.from_features(region_shape, crs=4326)

        # Create a GeoDataFrame containing the shape of Europe excluding overseas territories.      
        europe_bounds = gpd.GeoSeries(Polygon([(-22,27), (45,27), (45,72), (-22,72)]))
        europe_bounds = gpd.GeoDataFrame.from_features(europe_bounds, crs=4326)

        # Remove any region outside of Europe.
        region_shape = region_shape.overlay(europe_bounds, how='intersection')
        
        # Add the name of the region and set is as the index.
        region_shape['name'] = country_info['Name']+(' offshore' if offshore else '')
        region_shape = region_shape.set_index('name')
        
        # Plot the shape of the region of interest.
        if settings.make_plots:
            figures.plot_shape(region_shape)
        
    except:

        print(country_info['Name']+' not present')
        region_shape = None
    
    return region_shape


def get_containing_geopandas_box(region_shape):
    '''
    Get the containing box in latitude-longitude coordinates of a specific region.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        GeoDataFrame containing the region of interest

    Returns
    -------
    containing_box : geopandas.GeoDataFrame
        GeoDataFrame containing the containing box in latitude-longitude coordinates of the region of interest
    '''
    
    # Calculate the lateral bounds of the region of interest including a buffer layer of one degree.
    region_bounds = region_shape.unary_union.buffer(1).bounds

    # Create a GeoSeries containing box in latitude-longitude coordinates of the region of interest.
    containing_box = gpd.GeoSeries(Polygon([(region_bounds[0],region_bounds[1]),
                                            (region_bounds[2],region_bounds[1]),
                                            (region_bounds[2],region_bounds[3]),
                                            (region_bounds[0],region_bounds[3])]))
    
    # Convert the containing box to a GeoDataFrame.
    containing_box = gpd.GeoDataFrame.from_features(containing_box, crs=4326)
    
    return containing_box


def get_grid_cell_area():
    '''
    Calculate the area of each cell defined by the lat/lon grid.
    
    https://www.pmel.noaa.gov/maillists/tmap/ferret_users/fu_2004/msg00023.html
    https://en.wikipedia.org/wiki/Spherical_sector

    Returns
    -------
    cell_areas : xarray.DataArray
        DataArray containing the area of each cell defined by the lat/lon grid
    '''
    
    # Define the latitide and longitude values of the grid cell midpoints.
    lon = np.linspace(-180, 180, int(360/0.25)+1)
    lat = np.linspace(-90, 90, int(180/0.25)+1)

    # Define the latitude values of the grid cell boundaries.
    bounds_lat = np.insert(0.5*(lat[1:]+lat[:-1]), 0, lat[0])
    bounds_lat = np.insert(bounds_lat, len(bounds_lat), lat[-1])
    bounds_lat = xr.Dataset(data_vars={'upper_lat': (['y', 'x'], np.tile(bounds_lat[1:].T, (len(lon), 1)).T),
                                       'lower_lat': (['y', 'x'], np.tile(bounds_lat[:-1], (len(lon), 1)).T)},
                            coords={'x': lon, 'y': lat})

    # Define the grid resolution.
    delta_lon = 0.25

    # Define the Earth's radius.
    R_earth = 6.371*10**6

    # Calculate the area of each cell.
    cell_areas = 2*np.pi*R_earth**2*np.absolute(np.sin(bounds_lat['upper_lat']*np.pi/180)-np.sin(bounds_lat['lower_lat']*np.pi/180))*np.absolute(delta_lon)/360
    
    return cell_areas
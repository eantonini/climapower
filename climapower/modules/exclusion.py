import xarray as xr
import rasterio as rio
import geopandas as gpd
from shapely.geometry import shape

import settings
import modules.climate_utilities as climate_utilities


def exclude_regions_based_on_corine(excluder, codes, invert=False, buffer=0, crs=None):
    '''
    Define exclusion regions based on CORINE database for land use.
    
    https://land.copernicus.eu/eagle/files/eagle-related-projects/pt_clc-conversion-to-fao-lccs3_dec2010

    Parameters
    ----------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container
    codes : list of int
        List of CORINE land use codes to exclude
    invert : bool, optional
        True if the exclusion regions should be inverted, by default False
    buffer : int, optional
        Buffer to add around the exclusion regions, by default 0
    crs : int, optional
        Coordinate reference system, by default None
    
    Returns
    -------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container with the new exclusion regions
    '''
    
    # Load CORINE database for land use.
    corine = settings.geospatial_data_directory+'/CORINE_land_cover_database/DATA/U2018_CLC2018_V2020_20u1.tif'

    # Add the exclusion regions.
    excluder.add_raster(corine, codes=codes, invert=invert, buffer=buffer, crs=crs)

    return excluder


def exclude_wdpa_protected_areas(country_info, excluder, invert=False, buffer=0, offshore=False):
    '''
    Define exclusion regions based on the World Database on Protected Areas (WDPA).
    
    Citation: UNEP-WCMC and IUCN (2023), Protected Planet: The World Database on Protected Areas (WDPA) and World Database on Other Effective Area-based Conservation Measures (WD-OECM) [Online], April 2023, Cambridge, UK: UNEP-WCMC and IUCN. Available at: www.protectedplanet.net.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    excluder : atlite.gis.ExclusionContainer
        Exclusion container
    invert : bool, optional
        True if the exclusion regions should be inverted, by default False
    buffer : int, optional
        Buffer to add around the exclusion regions, by default 0
    offshore : bool, optional
        True if analyzing offshore wind, by default False

    Returns
    -------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container with the new exclusion regions
    '''
    
    # Load WDPA database for protected areas
    if offshore:
        wdpa = settings.geospatial_data_directory+'/World_Database_on_Protected_Areas/WDPA_WDOECM_Apr2023_Public_'+country_info['ISO Alpha-2']+'_shp/WDPA_WDOECM_'+country_info['ISO Alpha-2']+'_offshore_shp.shp'
    else:
        wdpa = settings.geospatial_data_directory+'/World_Database_on_Protected_Areas/WDPA_WDOECM_Apr2023_Public_'+country_info['ISO Alpha-2']+'_shp/WDPA_WDOECM_'+country_info['ISO Alpha-2']+'_shp.shp'
    
    # Add the exclusion regions.
    excluder.add_geometry(wdpa, invert=invert, buffer=buffer)
    
    return excluder


def exclude_natura2000_protected_areas(excluder, invert=False, buffer=0):
    '''
    Define exclusion regions based on Natura2000 database for protected areas.

    Parameters
    ----------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container
    invert : bool, optional
        True if the exclusion regions should be inverted, by default False
    buffer : int, optional
        Buffer to add around the exclusion regions, by default 0

    Returns
    -------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container with the new exclusion regions
    '''
    
    # Load Natura2000 database for protected areas.
    natura2000 = settings.geospatial_data_directory+'/Natura2000_database/Natura2000_end2021.gpkg'

    # Add the exclusion regions.
    excluder.add_geometry(natura2000, invert=invert, buffer=buffer)
        
    return excluder


def exclude_areas_with_high_slope(excluder, region_shape, max_slope=10):
    '''
    Define exclusion regions based on terrain slope.

    The terrain slope is calculated from the Global Multi-resolution Terrain Elevation Data (GMTED2010) at 7.5 arc-seconds resolution (about 250 m).

    Data source: https://earthexplorer.usgs.gov

    Parameters
    ----------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    max_slope : float
        Maximum slope in percentage above which areas are excluded

    Returns
    -------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container with the new exclusion regions
    '''
    
    # Define the filename of the slope data.
    slope_filename = settings.geospatial_data_directory+'/Europe__terrain_slope.tif'

    # Load the slope data.
    slope = xr.open_dataarray(slope_filename, engine='rasterio')

    # Clip the slope data to the region of interest.
    slope = climate_utilities.clip_to_region_containing_box(slope, region_shape)

    # Get shapes from the raster data of connected regions with specific slope values.
    regions = rio.features.shapes(xr.where(slope < max_slope, 0, 1).values.astype('int16'), transform=slope.rio.transform())

    # Create a list of shapes by keeping only where the slope is greater than the maximum value.
    unfeasible_regions = [shape(geometry) for geometry, value in regions if value == 1]

    # Convert the list to a GeoDataFrame.
    unfeasible_regions = gpd.GeoDataFrame(geometry=unfeasible_regions, crs='EPSG:4326')

    # Add the exclusion regions.
    excluder.add_geometry(unfeasible_regions)

    return excluder


def exclude_areas(country_info, region_shape, excluder, resource_type, offshore):
    '''
    Add the exclusion areas to the exclusion container depending on the resource type.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    excluder : atlite.gis.ExclusionContainer
        Exclusion container
    resource_type : str
        Type of resource ('wind' or 'solar')
    offshore : bool
        True if the resource of interest is offshore wind

    Returns
    -------
    excluder : atlite.gis.ExclusionContainer
        Exclusion container with the exclusion areas added
    '''

    if resource_type == 'wind':

        if offshore:
            # Add protected areas to the exclusion container.
            excluder = exclude_wdpa_protected_areas(country_info, excluder, offshore=country_info['Offshore wind'])

            # Add the inverse of costal regions (code = 44) up to about 100 km from shore to the exclusion container. 30 km are already included. We add 70 km of buffer.
            excluder = exclude_regions_based_on_corine(excluder, codes=[44], buffer=70000, invert=True)
        else:
            # Add protected areas to the exclusion container.
            excluder = exclude_wdpa_protected_areas(country_info, excluder)

            # Add urban, industrial, and commercial areas to the exclusion container with a buffer of 500 m.
            excluder = exclude_regions_based_on_corine(excluder, codes=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], buffer=500, crs=3035)
    
    elif resource_type == 'solar':

        # Add protected areas to the exclusion container.
        excluder = exclude_wdpa_protected_areas(country_info, excluder)

        # Add areas with a high terrain slope to the exclusion container.
        excluder = exclude_areas_with_high_slope(excluder, region_shape)
    
    return excluder
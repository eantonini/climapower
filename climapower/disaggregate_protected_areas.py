import os
import geopandas as gpd
# import matplotlib.pyplot as plt
import cartopy.io.shapereader as shpreader

import settings
import modules.geometry as geometry
import modules.general_utilities as general_utilities


# Set the working directory
data_path = settings.geospatial_data_directory + '/World_Database_on_Protected_Areas/'

# Load the country names and ISO codes
countries = general_utilities.get_countries()

# Specify the WDPA dataset names
dataset_date = 'Apr2023'
europe_folder_name = 'WDPA_WDOECM_'+dataset_date+'_Public_EU_shp'
wdpa_0_polygons = data_path+europe_folder_name+'_0/'+europe_folder_name+'-polygons.shp'
wdpa_0_points = data_path+europe_folder_name+'_0/'+europe_folder_name+'-points.shp'
wdpa_1_polygons = data_path+europe_folder_name+'_1/'+europe_folder_name+'-polygons.shp'
wdpa_1_points = data_path+europe_folder_name+'_1/'+europe_folder_name+'-points.shp'
wdpa_2_polygons = data_path+europe_folder_name+'_2/'+europe_folder_name+'-polygons.shp'
wdpa_2_points = data_path+europe_folder_name+'_2/'+europe_folder_name+'-points.shp'

# Load the WDPA datasets
protected_areas_polygons = gpd.read_file(wdpa_0_polygons)
protected_areas_polygons = gpd.pd.concat([protected_areas_polygons, gpd.read_file(wdpa_1_polygons)])
protected_areas_polygons = gpd.pd.concat([protected_areas_polygons, gpd.read_file(wdpa_2_polygons)])
# protected_areas_points = gpd.read_file(wdpa_0_points)
# protected_areas_points = gpd.pd.concat([protected_areas_points, gpd.read_file(wdpa_1_points)])
# protected_areas_points = gpd.pd.concat([protected_areas_points, gpd.read_file(wdpa_2_points)])

# For each country, extract the protected areas that are within its containing box and save them to a separate file.
for index, country_info in countries.iterrows():
    # country_info = countries.loc[countries['Name']=='France'].squeeze()
    
    # Create a folder for the country
    regional_folder_name = 'WDPA_WDOECM_'+dataset_date+'_Public_'+country_info['ISO Alpha-2']+'_shp/'
    regional_protected_areas_filename = 'WDPA_WDOECM_'+country_info['ISO Alpha-2']+'_shp.shp'
    if not os.path.isdir(data_path+regional_folder_name):
        os.mkdir(data_path+regional_folder_name)
    
    if not os.path.exists(data_path+regional_folder_name+regional_protected_areas_filename):
        
        region_shapes = shpreader.natural_earth(resolution="50m", category="cultural", name="admin_0_countries")
        dataset_attribute = 'ISO_A3_EH'
        backup_dataset_attribute = 'NAME'
        
        region = geometry.get_geopandas_region(country_info, offshore=False)
        
        containing_box = geometry.get_containing_geopandas_box(region)
    
        regional_protected_areas = protected_areas_polygons.overlay(containing_box, how='intersection')
        # regional_protected_areas_points = protected_areas_points.overlay(containing_box, how='intersection')
        # regional_protected_areas = gpd.pd.concat([regional_protected_areas_polygons, regional_protected_areas_points])
        
        # fig, ax = plt.subplots()
        # regional_protected_areas.plot(ax=ax)
        # region.plot(ax=ax, edgecolor="k", color="None")
        
        regional_protected_areas.to_file(data_path+regional_folder_name+regional_protected_areas_filename)
        
    if country_info['Offshore wind']:
        
        regional_offshore_protected_areas_filename = 'WDPA_WDOECM_'+country_info['ISO Alpha-2']+'_offshore_shp.shp'
        
        if not os.path.exists(data_path+regional_folder_name+regional_offshore_protected_areas_filename):
        
            region_shapes = data_path+'../European_continental_maritime_areas/EuropeanContinentalMaritimeAreas_Level0_v1.1.shp'
            dataset_attribute = "ISO_Ter1"
            backup_dataset_attribute = 'Territory1'
            
            region = geometry.get_geopandas_region(country_info, offshore=True)
            
            containing_box = geometry.get_containing_geopandas_box(region)
            
            regional_offshore_protected_areas = protected_areas_polygons.overlay(containing_box, how='intersection')
            # regional_protected_areas_points = protected_areas_points.overlay(containing_box, how='intersection')
            # regional_protected_areas = gpd.pd.concat([regional_protected_areas_polygons, regional_protected_areas_points])
            
            regional_offshore_protected_areas.to_file(data_path+regional_folder_name+regional_offshore_protected_areas_filename)
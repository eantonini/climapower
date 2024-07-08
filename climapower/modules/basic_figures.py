import numpy as np
import matplotlib.pyplot as plt
from rasterio.plot import show

import settings
import modules.climate_utilities as climate_utilities


def plot_shape(region_shape, offshore):
    '''
    Plot the shape of the region of interest.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    offshore : bool
        True if analyzing offshore wind
    '''
    
    # Define the plot limits based on a buffer layer equal to one degree.
    lateral_bounds = region_shape.unary_union.buffer(1).bounds

    # Initialize the figure, set its dimensions and the font size. The highest value in the dimensions is irrelevant becasue the aspect ration is set in the GeoDataFrame.plot
    fig, ax = plt.subplots(figsize=(7,7)) 
    plt.rc('font', size=16)

    # Plot the shape of the region of interest.
    region_shape.plot(ax=ax)

    # Set the title and the labels of the axes.
    ax.set_title(region_shape.index[0] + (' offshore area' if offshore else ' onshore area'))
    ax.set_xlabel('Longitude [deg]')
    ax.set_ylabel('Latitude [deg]')

    # Set the axis limits.
    ax.set_xlim(lateral_bounds[0], lateral_bounds[2])
    ax.set_ylim(lateral_bounds[1], lateral_bounds[3])

    # Set the name of the country.
    country_name = region_shape.index[0]
    if offshore:
        country_name = country_name + '__offshore_area'
    else:
        country_name = country_name + '__onshore_area'

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+country_name+'__shape.png', bbox_inches = 'tight', dpi = 300)


def plot_eligible_fraction(region_shape_with_new_crs, masked, transform, eligible_share, resource_type, offshore):
    '''
    Plot the eligible area of the region of interest.

    Parameters
    ----------
    region_shape_with_new_crs : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest with a new coordinate reference system
    masked : numpy.ndarray
        Masked array containing the eligible area
    transform : affine.Affine
        Affine transformation
    eligible_share : float
        Share of the total eligible area
    resource_type : str
        Type of resource
    offshore : bool
        True if analyzing offshore wind
    '''

    # Calculate the lenght of a degree of latitude.
    earth_radius = 6371000 # [m]
    earth_circumference = 2*np.pi*earth_radius # [m]
    degree_of_latitude_in_meters = earth_circumference/360

    # Define the plot limits based on a buffer layer equal to one degree of latitude in meters.
    lateral_bounds = region_shape_with_new_crs.buffer(degree_of_latitude_in_meters).bounds.values[0]

    # Initialize the figure, set its dimensions and the font size. The highest value in the dimensions is irrelevant becasue the aspect ration is set in the GeoDataFrame.plot
    fig, ax = plt.subplots(figsize=(7,7))
    plt.rc('font', size=16)

    # Plot the eligible area.
    ax = show(masked, transform=transform, cmap='Greens', ax=ax)

    # Plot the shape of the region of interest.
    region_shape_with_new_crs.plot(ax=ax, edgecolor='k', color='None')

    # Set the title and the labels of the axes.
    ax.set_title(f'Eligible area (green) {eligible_share * 100:2.2f}%')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')

    # Set the axis limits.
    ax.set_xlim([lateral_bounds[0], lateral_bounds[2]])
    ax.set_ylim([lateral_bounds[1], lateral_bounds[3]])

    # Set the name of the country and the resource type.
    country_name_and_resource = region_shape_with_new_crs.index[0]
    if resource_type == 'wind' and offshore:
        country_name_and_resource = country_name_and_resource + '__wind__offshore'
    elif resource_type == 'wind' and not offshore:
        country_name_and_resource = country_name_and_resource + '__wind__onshore'
    elif resource_type == 'solar':
        country_name_and_resource = country_name_and_resource + '__solar'

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+country_name_and_resource+'__eligible_area.png', bbox_inches = 'tight', dpi = 300)


def plot_cells(region_shape, resource_type, offshore, cells_to_plot, variable_name, color_map):
    '''
    Plot the cells of interest, i.e., the cells belonging to the region of interest, the cells with the availability factor, and the cells with the best resource.

    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    resource_type : str
        Type of resource
    offshore : bool
        True if analyzing offshore wind
    cells_to_plot : xarray.DataArray
        DataArray containing the cells to plot
    variable_name : str
        Name of the variable of interest
    color_map : str
        Name of the color map to use
    '''

    # Create a temporary cutout.
    cutout = climate_utilities.create_temporary_cutout(region_shape)
    
    # Initialize the figure, set its dimensions and the font size. The highest value in the dimensions is irrelevant becasue the aspect ration is set in the GeoDataFrame.plot
    fig, ax = plt.subplots(figsize=(7,7))
    plt.rc('font', size=16)

    # Plot the cells belonging to the region of interest.
    cells_to_plot.plot(cmap=color_map, vmin=0, vmax=1)

    # Plot the shape of the region of interest.
    region_shape.plot(ax=ax, edgecolor='k', color='None')

    # Plot the grid.
    cutout.grid.plot(ax=ax, color='None', edgecolor='grey')

    # Set the title and labels of the axes.
    ax.set_title(variable_name.replace('_', ' ').capitalize())
    ax.set_xlabel('Longitude [deg]')
    ax.set_ylabel('Latitude [deg]')

    # Set the name of the country and the resource type.
    country_name_and_resource = region_shape.index[0]
    if resource_type == 'wind' and offshore:
        country_name_and_resource = country_name_and_resource + '__wind__offshore'
    elif resource_type == 'wind' and not offshore:
        country_name_and_resource = country_name_and_resource + '__wind__onshore'
    elif resource_type == 'solar':
        country_name_and_resource = country_name_and_resource + '__solar'

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+country_name_and_resource+'__'+variable_name+'.png', bbox_inches = 'tight', dpi = 300)


def plot_installed_capacity(region_shape, year, variable_name, plant_layout):
    '''
    Plot the installed capacity distribution.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    variable_name : str
        Name of the variable of interest
    plant_layout : xarray.DataArray
        DataArray containing the installed capacity distribution
    '''    

    # Define the plot limits based on a buffer layer equal to one degree.
    lateral_bounds = region_shape.unary_union.buffer(1).bounds

    # Initialize the figure, set its dimensions and the font size. 
    fig, ax = plt.subplots(figsize=(7,6))
    plt.rc('font', size=16)

    # Plot the installed capacity distribution.
    plant_layout.plot(ax=ax, cmap='inferno_r')

    # Plot the shape of the region of interest.
    region_shape.plot(ax=ax, edgecolor='k', color='None')

    # Set the axis limits.
    ax.set_xlim(lateral_bounds[0], lateral_bounds[2])
    ax.set_ylim(lateral_bounds[1], lateral_bounds[3])

    # Set the labels of the axes.
    ax.set_ylabel('Latitude [deg]')
    ax.set_xlabel('Longitude [deg]')

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+region_shape.index[0]+'__'+str(year)+'__'+variable_name+'.png', bbox_inches = 'tight', dpi = 300)


def plot_comparison_in_year(region_shape, year, variable_name, compare):
    '''
    Plot the capacity factor time series in the year of interst.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    variable_name : str
        Name of the variable of interest
    compare : pandas.DataFrame
        Dataframe containing the actual, simulated and calibrated time series
    '''

    # Define the colors for the lines in the plot.
    colors = {'actual': 'tab:orange', 'calibrated': 'tab:green', 'simulated': 'tab:blue'}

    # Initialize the figure, set its dimensions and the font size.
    fig, ax = plt.subplots(figsize=(8,6))
    plt.rc('font', size=16)

    # Keep track of the names to use in the legend.
    legend_names = None

    # Plot the actual time series and its mean.
    ax.plot([compare.index.min(), compare.index.max()], [compare['actual'].mean(), compare['actual'].mean()], color=colors['actual'], linestyle='dashed')
    legend_names = ax.plot(compare.resample('1W').mean().index, compare['actual'].resample('1W').mean(), color=colors['actual'], label=settings.calibration_data_source)
    
    # Plot the calibrated time series and its mean.
    if settings.calibrate:
        ax.plot([compare.index.min(), compare.index.max()], [compare['calibrated'].mean(), compare['calibrated'].mean()], color=colors['calibrated'], linestyle='dashed')
        legend_names += ax.plot(compare.resample('1W').mean().index, compare['calibrated'].resample('1W').mean(), color=colors['calibrated'], label='calibrated (r = {:.2f})'.format(compare.corr()['calibrated']['actual']))
    
    # Check if secondary axis is needed.
    secondary_axis = abs(compare['simulated'].mean() - compare['actual'].mean())/compare['actual'].mean() > 5 or abs(compare['simulated'].mean() - compare['actual'].mean())/compare['simulated'].mean() > 5

    # Plot the simulated time series and its mean. If the mean is too different from the actual mean, plot the simulated time series on a secondary axis.
    if secondary_axis:
        ax_secondary = ax.twinx()
        ax_secondary.plot([compare.index.min(), compare.index.max()], [compare['simulated'].mean(), compare['simulated'].mean()], color=colors['simulated'], linestyle='dashed')
        legend_names += ax_secondary.plot(compare.resample('1W').mean().index, compare['simulated'].resample('1W').mean(), color=colors['simulated'], label='simulated (r = {:.2f})'.format(compare.corr()['simulated']['actual']))
    else:
        ax.plot([compare.index.min(), compare.index.max()], [compare['simulated'].mean(), compare['simulated'].mean()], color=colors['simulated'], linestyle='dashed')
        legend_names += ax.plot(compare.resample('1W').mean().index, compare['simulated'].resample('1W').mean(), color=colors['simulated'], label='simulated (r = {:.2f})'.format(compare.corr()['simulated']['actual']))

    # Set the legend.
    ax.legend(legend_names, [l.get_label() for l in legend_names], loc='upper left')

    # Set the labels of the axes.
    if 'wind' in variable_name or 'solar' in variable_name:
        ax.set_ylabel('Capacity factor')
    elif 'hydro' in variable_name:
        ax.set_ylabel('Inflow [GWh]')
    if secondary_axis:
        if 'wind' in variable_name or 'solar' in variable_name:
            ax_secondary.set_ylabel('Capacity factor')
        elif 'hydro' in variable_name:
            ax_secondary.set_ylabel('Inflow [GWh]')
            ax_secondary.yaxis.label.set_color(colors['simulated'])
    
    # Rotate the xticks.
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
        tick.set_ha('right')

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+region_shape.index[0]+'__'+str(year)+'__'+variable_name+'.png', bbox_inches = 'tight', dpi = 300)


def plot_comparison_in_period(region_shape, year, variable_name, compare):
    '''
    Plot the capacity factor time series in three different months.
    
    Parameters
    ----------
    region_shape : geopandas.GeoDataFrame
        Geopandas dataframe containing the shape of the region of interest
    year : int
        Year of interest
    variable_name : str
        Name of the variable of interest
    compare : pandas.DataFrame
        Dataframe containing the actual, simulated and calibrated time series
    '''

    # Define the colors for the lines in the plot.
    colors = ['tab:orange', 'tab:blue', 'tab:green']

    # Initialize the figure, set its dimensions and the font size.
    fig, ax = plt.subplots(3, sharey=True, figsize=(8,15))
    plt.rc('font', size=16)

    # Rename the variables before plotting.
    compare = compare.rename(columns={'actual': settings.calibration_data_source})

    # Plot the capacity factor time series in three different months.
    compare[str(year)+'-01-01T00:00:00':str(year)+'-01-31T23:00:00'].plot(ax=ax[0], color=colors, x_compat=True)
    compare[str(year)+'-02-01T00:00:00':str(year)+'-02-28T23:00:00'].plot(ax=ax[1], color=colors, x_compat=True)
    compare[str(year)+'-03-01T00:00:00':str(year)+'-03-31T23:00:00'].plot(ax=ax[2], color=colors, x_compat=True)

    # Remove the legend in the second and third subplot.
    ax[1].get_legend().remove()
    ax[2].get_legend().remove()

    # Set the labels of the axes.
    ax[0].set_ylabel('Capacity factor')
    ax[1].set_ylabel('Capacity factor')
    ax[2].set_ylabel('Capacity factor')
    fig.tight_layout()

    # Save the figure.
    if settings.save_plots:
        fig.savefig(settings.figure_folder+'/'+region_shape.index[0]+'__'+str(year)+'__'+variable_name+'.png', bbox_inches = 'tight', dpi = 300)
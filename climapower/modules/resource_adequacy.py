from calendar import c
from turtle import color
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl

import modules.resource_adequacy_utilities as resource_adequacy_utilities


def plot_time_series(dataset):

    variables_to_plot = ['Onshore wind capacity factor',
                         'Offshore wind capacity factor',
                         'Solar capacity factor',
                         'Hydropower inflow',
                         'Conventional hydropower generation',
                         'Pumped-storage hydropower generation',
                         'Pumped-storage hydropower consumption',
                         'Run-of-river hydropower generation',
                         #'Residential space heating demand',
                         #'Services space heating demand',
                         #'Cooling demand',
                         'Electricity demand']

    fig, ax = plt.subplots(len(variables_to_plot), 1, figsize=(6, 12), sharex=True)
    
    for ii, variable_name in enumerate(variables_to_plot):

        ax[ii].plot(dataset[variable_name]['time'], dataset[variable_name])

        ax[ii].set_title(variable_name)

    # Rotate the xticks.
    ax[-1].tick_params(axis='x', labelrotation=45)

    fig.tight_layout()

    fig.savefig('time_series.png', dpi=300, bbox_inches = 'tight')


def plot_unmet_demand(results, mean_wind_generation_array, mean_solar_generation_array, mean_hydropower_generation):

    italy_electricity_generation = 279 # TWh
    milan_electricity_demand = 15.5 # TWh
    daily_electricity_demand_in_milan = milan_electricity_demand/365 # TWh
    daily_electricity_demand_in_milan = daily_electricity_demand_in_milan/italy_electricity_generation*100 # % of annual demand

    fig, ax = plt.subplots(len(mean_wind_generation_array[0]), len(mean_wind_generation_array), figsize=(8, 6), sharex=True, sharey=True)

    max_residual_demand = 0
    lowest_total_generation = mean_wind_generation_array[0,0] + mean_solar_generation_array[0,0] + float(mean_hydropower_generation)

    for ii in range(len(mean_wind_generation_array)):
        for jj in range(len(mean_wind_generation_array[0])):

            data_to_show = results[ii, jj, :, :]
            mean_wind_generation = mean_wind_generation_array[ii, jj]
            mean_solar_generation = mean_solar_generation_array[ii, jj]

            max_residual_demand_new = np.max(data_to_show)

            if max_residual_demand_new > max_residual_demand:
                max_residual_demand = max_residual_demand_new
                im = ax[jj, ii].imshow(data_to_show, origin='lower', aspect='auto')
            else:
                ax[jj, ii].imshow(data_to_show, origin='lower', aspect='auto')

            if jj == 2:
                ax[jj, ii].set_xlabel('Day of the year')
            if ii == 0:
                ax[jj, ii].set_ylabel('Hour of the day')

            axx = ax[jj, ii].inset_axes([0.2, 1.1, .6, .4],) # inset_axes([0.3, 1.1, .6, .4],)
            total_generation = mean_wind_generation + mean_solar_generation + float(mean_hydropower_generation)
            lowest_total_generation = min(lowest_total_generation, total_generation)
            axx.pie([mean_hydropower_generation, mean_wind_generation, mean_solar_generation], radius=(total_generation / lowest_total_generation)**0.5, colors=['tab:green', 'tab:blue', 'gold'])
            if ii == 0 and jj == 0:
                axx.annotate('Supply mix', xy=(0, 0), xytext=(-1.3, 0.5), xycoords='axes fraction', textcoords='axes fraction', ha='center', va='center')
            if jj == 0:
                axx.annotate('{:d}% of\nannual demand'.format(int(total_generation / lowest_total_generation * 100)), xy=(0, 0), xytext=(1.3, 0.5), xycoords='axes fraction', textcoords='axes fraction', ha='left', va='center')
            if ii == 0 and jj == 1:
                axx.annotate('Wind', xy=(0, 0), xytext=(-0.1, 0.8), xycoords='axes fraction', textcoords='axes fraction', ha='right', va='center', color='tab:blue')
                axx.annotate('Solar', xy=(0, 0), xytext=(1.1, 0.2), xycoords='axes fraction', textcoords='axes fraction', ha='left', va='center', color='gold')
                axx.annotate('Hydropower', xy=(0, 0), xytext=(1.1, 0.8), xycoords='axes fraction', textcoords='axes fraction', ha='left', va='center', color='tab:green')
    
    rounded_max_residual_demand = np.ceil(max_residual_demand*500.0)/500.0
    cmap = mpl.cm.viridis
    bounds = np.linspace(0, rounded_max_residual_demand, int(rounded_max_residual_demand*1000+1))
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([1.0, 0.15, 0.02, 0.7])
    # fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap='viridis'), cax=cbar_ax)
    fig.colorbar(im, cax=cbar_ax)
    cbar_ax.set_ylabel('Unmet demand [% of annual demand]', labelpad=10)
    
    fig.tight_layout()

    fig.savefig('unmet_demand.png', dpi=300, bbox_inches = 'tight')


def plot_resource_adequacy(data_to_show, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_lowest_unmet_demand, colormap, line_color, title, plot_annotation, total_or_difference):

    X, Y = np.meshgrid(wind_and_solar_generation_fractions, wind_generation_fractions)

    x_points_to_show = np.linspace(wind_and_solar_generation_fractions[0], wind_and_solar_generation_fractions[-1], 5)
    y_points_to_show = np.linspace(wind_generation_fractions[0], wind_generation_fractions[-1], 5)
    x_labels = ['{:d}%'.format(int(x*100)) for x in x_points_to_show]
    y_labels = ['{:d}% Wind\n{:d}% Solar'.format(int(x*100), int((1-x)*100)) for x in y_points_to_show]

    if isinstance(data_to_show, list):

        first_max_resource_adequacy = 100
        first_min_resource_adequacy = np.min(data_to_show[0])
        first_min_resource_adequacy = np.floor(first_min_resource_adequacy/2)*2
        first_levels = np.linspace(first_min_resource_adequacy, first_max_resource_adequacy, int((first_max_resource_adequacy-first_min_resource_adequacy)/4+1))

        second_max_resource_adequacy = 0
        for ii in range(1, len(data_to_show)):
            second_max_resource_adequacy = np.max([second_max_resource_adequacy, np.max(data_to_show[ii] - data_to_show[0])])
        second_max_resource_adequacy = np.ceil(second_max_resource_adequacy)
        second_levels = np.linspace(0, second_max_resource_adequacy, int(second_max_resource_adequacy+1))

        fig, ax = plt.subplots(1, len(data_to_show), figsize=(12, 5), sharex=True, sharey=True)

        for ii in range(len(data_to_show)):

            if ii == 0:

                im_contour = ax[ii].contour(X, Y, data_to_show[ii], linewidths=0.5, colors='k', levels=first_levels)
                im_contourf = ax[ii].contourf(X, Y, data_to_show[ii], cmap=colormap[ii], levels=first_levels)
                ax[ii].clabel(im_contour, inline=True)

                ax[ii].plot(wind_and_solar_generation_fractions, mix_with_lowest_unmet_demand, '--', color=line_color)
                ax[ii].annotate('Mix that maximizes\nresource adequacy', xy=(0, 0), xytext=(0.68, 0.70), xycoords='axes fraction', textcoords='axes fraction', ha='center', va='center', color='m')
                
                ax[ii].set_ylabel('Wind and solar supply mix', labelpad=10)
                
                cbar = plt.colorbar(im_contourf, ax=ax[ii], location='top', pad=0.15)
                cbar.ax.set_xlabel('Resource adequacy\n[% of annual demand met]')
            
            else:

                im_contour = ax[ii].contour(X, Y, data_to_show[ii] - data_to_show[0], linewidths=0.5, colors='k', levels=second_levels)
                im_contourf = ax[ii].contourf(X, Y, data_to_show[ii] - data_to_show[0], cmap=colormap[ii], levels=second_levels)
                ax[ii].clabel(im_contour, inline=True)

                cbar = plt.colorbar(im_contourf, ax=ax[ii], location='top', pad=0.15)
                cbar.ax.set_xlabel('Increase in resource adequacy\n[% of annual demand met]')
                if ii != 2:
                    cbar.ax.axes.set_visible(False)
            
            ax[ii].set_xticks(x_points_to_show, labels=x_labels)
            ax[ii].set_yticks(y_points_to_show, labels=y_labels)
            ax[ii].set_xticklabels(x_labels, rotation=60, ha='right')
        
        fig.supxlabel('Wind and solar generation relative to\nannual electricity demand net of\nannual hydropower generation')
        fig.tight_layout()

        fig.savefig('resource_adequacy.png', dpi=300, bbox_inches = 'tight')

    else:

        fig, ax = plt.subplots(figsize=(5, 4))
        
        im_contour = ax.contour(X, Y, data_to_show, linewidths=0.5, colors='k')
        im_contourf = ax.contourf(X, Y, data_to_show, cmap=colormap)
        
        if plot_annotation:
            ax.plot(wind_and_solar_generation_fractions, mix_with_lowest_unmet_demand, '--', color=line_color)
            ax.annotate('Mix that maximizes\nresource adequacy', xy=(0, 0), xytext=(0.76, 0.75), xycoords='axes fraction', textcoords='axes fraction', ha='center', va='center', color='m')
        
        ax.set_xticks(x_points_to_show, labels=x_labels)
        ax.set_yticks(y_points_to_show, labels=y_labels)
        ax.set_xticklabels(x_labels, rotation=60, ha='right')
        ax.set_xlabel('Wind and solar generation relative to\nannual electricity demand net of\nannual hydropower generation', labelpad=10)
        ax.set_ylabel('Wind and solar supply mix', labelpad=10)
        ax.set_title(title, y=1.05)

        ax.clabel(im_contour, inline=True)
        cbar = plt.colorbar(im_contourf)
        if total_or_difference == 'total':
            cbar.ax.set_ylabel('Resource adequacy\n[% of annual demand met]')
        elif total_or_difference == 'difference':
            cbar.ax.set_ylabel('Increase in resource adequacy\n[% of annual demand met]')
        
        fig.savefig(('resource_adequacy_with_{}.png'.format(title.replace(' ', '_').replace(',', ''))).lower(), dpi=300, bbox_inches = 'tight')


def run_example_of_unmet_demand_analysis(country_info, entsoe_dataset):

    # Define the year for the reanalysis data.
    reanalysis_year = 2019
    
    # Load the datasets.
    reanalysis_dataset = resource_adequacy_utilities.get_time_series_dataset(country_info, reanalysis_year, climate_data_source='reanalysis')

    plot_time_series({**reanalysis_dataset, **entsoe_dataset})
    
    # Calculate the mean demand.
    mean_electricity_demand = float(entsoe_dataset['Electricity demand'].mean().values)

    # Get the hydropower generation.
    hydropower_generation = entsoe_dataset['Conventional hydropower generation'] + entsoe_dataset['Pumped-storage hydropower generation'] + entsoe_dataset['Run-of-river hydropower generation'] - entsoe_dataset['Pumped-storage hydropower consumption']
    mean_hydropower_generation = float(hydropower_generation.mean().values)

    # This is to account that the total wind and solar generation share is relative to the residual demamnd.
    additional_fraction = mean_electricity_demand/(mean_electricity_demand - mean_hydropower_generation)

    # Define 6 cases with different wind and solar generation fractions and wind generation fractions.
    wind_and_solar_generation_fractions = [1, 1+additional_fraction]
    wind_generation_fractions = [0.25, 0.5, 0.75]

    # Initialize the arrays to store the results.
    unmet_demand_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions), 24, 365))
    mean_wind_generation_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions)))
    mean_solar_generation_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions)))

    # Loop over the cases.
    for ii, wind_and_solar_generation_fraction in enumerate(wind_and_solar_generation_fractions):
        for jj, wind_generation_fraction in enumerate(wind_generation_fractions):

            # Calculate the residual demand and the mean wind and solar generation.
            residual_demand, local_mean_wind_generation, local_mean_solar_generation, __ = resource_adequacy_utilities.get_residual_demand({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fraction=wind_and_solar_generation_fraction, wind_generation_fraction=wind_generation_fraction)

            unmet_demand_array[ii, jj, :, :] = residual_demand.where(residual_demand > 0, 0).values.reshape(365, 24).T/float(entsoe_dataset['Electricity demand'].sum().values)*100
            mean_wind_generation_array[ii, jj] = local_mean_wind_generation
            mean_solar_generation_array[ii, jj] = local_mean_solar_generation

    plot_unmet_demand(unmet_demand_array,  mean_wind_generation_array, mean_solar_generation_array, mean_hydropower_generation)


def run_example_of_resource_adequacy_analysis(country_info, entsoe_dataset):

    # Define the year for the reanalysis and the ENTSO-E data.
    reanalysis_year = 2019
    
    # Load the datasets.
    reanalysis_dataset = resource_adequacy_utilities.get_time_series_dataset(country_info, reanalysis_year, climate_data_source='reanalysis')

    # Adjust the hydropower inflow to match the hydropower generation without run-of-river for consistency between the case with actual hydropower generation and the case with flexible hydropower generation.
    mean_hydropower_generation_without_run_of_river = float((entsoe_dataset['Conventional hydropower generation'] + entsoe_dataset['Pumped-storage hydropower generation'] - entsoe_dataset['Pumped-storage hydropower consumption']).mean().values)
    reanalysis_dataset['Hydropower inflow'] = reanalysis_dataset['Hydropower inflow'] / reanalysis_dataset['Hydropower inflow'].mean() * (mean_hydropower_generation_without_run_of_river)

    # Define the wind and solar generation fractions and the wind generation fractions.
    wind_and_solar_generation_fractions = np.arange(1, 3.1, 0.1)
    wind_generation_fractions = np.arange(0, 1.05, 0.05)

    # Calculate the resource adequacy for 4 cases.
    resource_adequacy_with_actual_hydropower = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=True)
    resource_adequacy_with_only_conventional_hydropower = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False)
    # resource_adequacy_with_0_5_current_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=0.5)
    resource_adequacy_with_current_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=1)
    resource_adequacy_with_expanded_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=2)
    # resource_adequacy_with_expanded_downstream_reservoir = resource_adequacy_utilities.get_resource_adequacy({**reanalysis_dataset, **entsoe_dataset}, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=1, hours_at_full_power_consumption_capacity=24)

    # Calculate the mix that maximizes the resource adequacy.
    mix_with_highest_resource_adequacy = [resource_adequacy_utilities.get_mix_for_highest_resource_adequacy(wind_generation_fractions, resource_adequacy_with_actual_hydropower[ii, :]) for ii in range(len(wind_and_solar_generation_fractions))]

    # Combine the data to show in a list.
    data_to_show = [resource_adequacy_with_actual_hydropower.T*100,
                    resource_adequacy_with_only_conventional_hydropower.T*100,
                    resource_adequacy_with_current_pumped_storage_hydropower.T*100,
                    resource_adequacy_with_expanded_pumped_storage_hydropower.T*100]
    
    # Define the colormaps and the titles.
    colormap = ['viridis', 'plasma', 'plasma', 'plasma']
    title = ['resource_adequacy_with_actual_hydropower',
             'resource_adequacy_with_only_conventional_hydropower',
             'resource_adequacy_with_current_pumped_storage_hydropower',
             'resource_adequacy_with_expanded_pumped_storage_hydropower']
    
    plot_resource_adequacy(data_to_show, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, colormap, 'm', title, True, 'total')

    # plot_resource_adequacy(resource_adequacy_with_actual_hydropower.T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'viridis', 'm', 'Current hydropower generation', True, 'total')

    # plot_resource_adequacy(resource_adequacy_with_only_conventional_hydropower.T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'viridis', 'm', 'Only conventional hydropower', True, 'total')

    # plot_resource_adequacy((resource_adequacy_with_only_conventional_hydropower - resource_adequacy_with_actual_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Only conventional hydropower', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_0_5_current_pumped_storage_hydropower - resource_adequacy_with_only_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', '50% of hydropower is pumped storage', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_current_pumped_storage_hydropower - resource_adequacy_with_only_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Current pumped storage hydropower capacity', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_expanded_pumped_storage_hydropower - resource_adequacy_with_only_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Expanded pumped storage hydropower', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_expanded_downstream_reservoir - resource_adequacy_with_only_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Expanded pumped storage hydropower', False, 'difference')


def run_example_of_resource_adequacy_over_years(country_info, entsoe_dataset):    

    # Define the reference year for the projections data.
    reference_year = 2010

    # Load the datasets.
    reference_projections_dataset = resource_adequacy_utilities.get_time_series_dataset(country_info, reference_year, climate_data_source='projections')

    # Define the wind and solar generation fractions and the wind generation fractions to keep constant across the years.
    wind_and_solar_generation_fraction = 1.5
    wind_generation_fraction = 0.5

    # Calculate the mean electricity demand to keep constant across the years.
    mean_electricity_demand = float(entsoe_dataset['Electricity demand'].mean().values)

    # Convert the hydropower inflow from GWh to MWh.
    reference_projections_dataset['Hydropower inflow'] = reference_projections_dataset['Hydropower inflow']*1e3

    # Calculate the mean hydropower generation in the reference year.
    mean_hydropower_generation = float(reference_projections_dataset['Hydropower inflow'].mean().values) + float(entsoe_dataset['Run-of-river hydropower generation'].mean().values)

    # Calculate the mean wind and solar generation in the reference year.
    reference_mean_wind_generation = wind_and_solar_generation_fraction * wind_generation_fraction * (mean_electricity_demand - mean_hydropower_generation)
    reference_mean_solar_generation = wind_and_solar_generation_fraction * (1 - wind_generation_fraction) * (mean_electricity_demand - mean_hydropower_generation)

    # Calculate the wind and solar capacities to keep constant across the years.
    wind_capacity = reference_mean_wind_generation / reference_projections_dataset['Onshore wind capacity factor'].mean().values
    solar_capacity = reference_mean_solar_generation / reference_projections_dataset['Solar capacity factor'].mean().values

    # Initialize the arrays to store the results.
    resource_adequacy_list = []
    mean_wind_generation_list = []
    mean_solar_generation_list = []
    mean_hydropower_generation_list = []

    for year in range(2019,2100,2):

        # Load the datasets.
        projections_dataset = resource_adequacy_utilities.get_time_series_dataset(country_info, year, climate_data_source='projections')

        # Convert the hydropower inflow from GWh to MWh.
        projections_dataset['Hydropower inflow'] = projections_dataset['Hydropower inflow']*1e3

        # Calculate the residual demand, the mean wind generation, the mean solar generation, and the mean hydropower generation.
        residual_demand, mean_wind_generation, mean_solar_generation, hydropower_generation = resource_adequacy_utilities.get_residual_demand({**projections_dataset, **entsoe_dataset}, wind_capacity=wind_capacity, solar_capacity=solar_capacity, use_actual_hydropower_generation=False)

        # Calculate the unmet demand.
        unmet_demand = residual_demand.where(residual_demand > 0, 0).sum()

        # Store the results.
        resource_adequacy_list.append(float(1 - unmet_demand/entsoe_dataset['Electricity demand'].sum().values)*100)
        mean_wind_generation_list.append(mean_wind_generation)
        mean_solar_generation_list.append(mean_solar_generation)
        mean_hydropower_generation_list.append(float(hydropower_generation.mean().values))
    
    variables_to_plot = [np.array(resource_adequacy_list), np.array(mean_wind_generation_list)*8760*1e-6, np.array(mean_solar_generation_list)*8760*1e-6, np.array(mean_hydropower_generation_list)*8760*1e-6]
    variable_names = ['Resource adequacy', 'Wind generation', 'Solar generation', 'Hydropower generation']
    y_axis_labels = ['[% of annual demand met]', '[TWh]', '[TWh]', '[TWh]']
    time = np.arange(2019,2100,2)
    colors = ['m', 'tab:blue', 'gold', 'tab:green']

    fig = plt.figure(figsize=(8, 7), layout="constrained")
    spec = fig.add_gridspec(5, 6)

    for ii, variable_to_plot in enumerate(variables_to_plot):
        if ii == 0:
            ax = fig.add_subplot(spec[0:3, 1:5])
            xytext=(0.8, 0.9)
        else:
            ax = fig.add_subplot(spec[3:5, (ii-1)*2:(ii-1)*2+2])
            xytext=(0.7, 0.85)

        ax.plot(time, variable_to_plot, color=colors[ii], alpha=0.5)
        slope, intercept, r_value, p_value, std_err = stats.linregress(time, variable_to_plot)
        ax.plot(time, slope*np.array(time) + intercept, '--', color=colors[ii])
        ax.annotate('Slope: {:.3f}\nR-value: {:.2f}\np-value: {:.3f}'.format(slope, r_value, p_value), xy=(0, 0), xytext=xytext, xycoords='axes fraction', textcoords='axes fraction', ha='center', va='center', color='k')
        ax.set_ylabel(variable_names[ii]+' '+y_axis_labels[ii], weight='bold')
        ax.set_xlabel('Year')
    
    fig.tight_layout()

    fig.savefig('resource_adequacy_over_years.png', dpi=300, bbox_inches = 'tight')
    
     

def compute_resource_adequacy(country_info):

    entsoe_year = 2019
    entsoe_dataset = resource_adequacy_utilities.get_entsoe_time_series_dataset(country_info, entsoe_year)
    
    run_example_of_unmet_demand_analysis(country_info, entsoe_dataset)

    run_example_of_resource_adequacy_analysis(country_info, entsoe_dataset)
    
    run_example_of_resource_adequacy_over_years(country_info, entsoe_dataset)


    # fig, ax = plt.subplots()

    # dataset['Electricity demand'].plot(ax=ax, label='Electricity demand')
    # (electrified_space_heating_demand_in_residential_sector * tj_to_mwh * dataset['Residential space heating demand']).plot(ax=ax, label='Electrified residential space heating demand')
    # (electrified_space_heating_demand_in_services_sector * tj_to_mwh * dataset['Services space heating demand']).plot(ax=ax, label='Electrified services space heating demand')
    # (cooling_demand * tj_to_mwh * dataset['Cooling demand']).plot(ax=ax, label='Cooling demand')
    # (space_heating_demand_in_residential_sector * tj_to_mwh * dataset['Residential space heating demand']).plot(ax=ax, label='Residential space heating demand')
    # (space_heating_demand_in_services_sector * tj_to_mwh * dataset['Services space heating demand']).plot(ax=ax, label='Services space heating demand')

    # ax.legend()
import numpy as np
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

        max_resource_adequacy = 0
        for ii in range(1, len(data_to_show)):
            max_resource_adequacy = np.max([max_resource_adequacy, np.max(data_to_show[ii] - data_to_show[0])])
        max_resource_adequacy = np.ceil(max_resource_adequacy)
        levels = np.linspace(0, max_resource_adequacy, int(max_resource_adequacy+1))

        fig, ax = plt.subplots(1, len(data_to_show), figsize=(12, 5), sharex=True, sharey=True)

        for ii in range(len(data_to_show)):

            if ii == 0:

                im_contour = ax[ii].contour(X, Y, data_to_show[ii], linewidths=0.5, colors='k')
                im_contourf = ax[ii].contourf(X, Y, data_to_show[ii], cmap=colormap[ii])
                ax[ii].clabel(im_contour, inline=True)

                ax[ii].plot(wind_and_solar_generation_fractions, mix_with_lowest_unmet_demand, '--', color=line_color)
                ax[ii].annotate('Mix that maximizes\nresource adequacy', xy=(0, 0), xytext=(0.68, 0.70), xycoords='axes fraction', textcoords='axes fraction', ha='center', va='center', color='m')
                
                ax[ii].set_ylabel('Wind and solar supply mix', labelpad=10)
                
                cbar = plt.colorbar(im_contourf, ax=ax[ii], location='top', pad=0.15)
                cbar.ax.set_xlabel('Resource adequacy\n[% of annual demand met]')
            
            else:

                im_contour = ax[ii].contour(X, Y, data_to_show[ii] - data_to_show[0], linewidths=0.5, colors='k', levels=levels)
                im_contourf = ax[ii].contourf(X, Y, data_to_show[ii] - data_to_show[0], cmap=colormap[ii], levels=levels)
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


def compute_resource_adequacy(country_info):
    

    year = 2019
    
    dataset = resource_adequacy_utilities.get_time_series_dataset(country_info, year)

    plot_time_series(dataset)
    


    wind_and_solar_generation_fractions = [1, 2]
    wind_generation_fractions = [0.25, 0.5, 0.75]

    unmet_demand_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions), 24, 365))
    mean_wind_generation_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions)))
    mean_solar_generation_array = np.zeros((len(wind_and_solar_generation_fractions), len(wind_generation_fractions)))

    for ii, wind_and_solar_generation_fraction in enumerate(wind_and_solar_generation_fractions):
        for jj, wind_generation_fraction in enumerate(wind_generation_fractions):

            residual_demand, local_mean_wind_generation, local_mean_solar_generation, __ = resource_adequacy_utilities.get_residual_demand(dataset, wind_and_solar_generation_fraction, wind_generation_fraction)

            unmet_demand_array[ii, jj, :, :] = residual_demand.where(residual_demand > 0, 0).values.reshape(365, 24).T/float(dataset['Electricity demand'].sum().values)*100
            mean_wind_generation_array[ii, jj] = local_mean_wind_generation
            mean_solar_generation_array[ii, jj] = local_mean_solar_generation
    
    mean_hydropower_generation = (dataset['Conventional hydropower generation'] + dataset['Pumped-storage hydropower generation'] + dataset['Run-of-river hydropower generation'] - dataset['Pumped-storage hydropower consumption']).mean()
    plot_unmet_demand(unmet_demand_array,  mean_wind_generation_array, mean_solar_generation_array, mean_hydropower_generation)


    wind_and_solar_generation_fractions = np.arange(1, 3.1, 0.1)
    wind_generation_fractions = np.arange(0, 1.05, 0.05)
    

    resource_adequacy_with_actual_hydropower = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=True)
    resource_adequacy_with_only_conventional_hydropower = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False)
    resource_adequacy_with_0_5_current_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=0.5)
    resource_adequacy_with_current_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=1)
    resource_adequacy_with_expanded_pumped_storage_hydropower = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=2)
    resource_adequacy_with_expanded_downstream_reservoir = resource_adequacy_utilities.get_resource_adequacy(dataset, wind_and_solar_generation_fractions, wind_generation_fractions, use_actual_hydropower_generation=False, fraction_of_pumped_storage=1, hours_at_full_power_consumption_capacity=24)


    mix_with_highest_resource_adequacy = [resource_adequacy_utilities.get_mix_for_highest_resource_adequacy(wind_generation_fractions, resource_adequacy_with_actual_hydropower[ii, :]) for ii in range(len(wind_and_solar_generation_fractions))]


    data_to_show = [resource_adequacy_with_actual_hydropower.T*100,
                    resource_adequacy_with_only_conventional_hydropower.T*100,
                    resource_adequacy_with_current_pumped_storage_hydropower.T*100,
                    resource_adequacy_with_expanded_pumped_storage_hydropower.T*100]
    
    colormap = ['viridis', 'plasma', 'plasma', 'plasma']

    title = ['resource_adequacy_with_actual_hydropower',
             'resource_adequacy_with_only_conventional_hydropower',
             'resource_adequacy_with_current_pumped_storage_hydropower',
             'resource_adequacy_with_expanded_pumped_storage_hydropower']

    
    
    plot_resource_adequacy(data_to_show, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, colormap, 'm', title, True, 'total')

    # plot_resource_adequacy(resource_adequacy_with_actual_hydropower.T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'viridis', 'm', 'Current hydropower generation', True, 'total')

    # plot_resource_adequacy(resource_adequacy_with_conventional_hydropower.T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'viridis', 'm', 'Only conventional hydropower', True, 'total')

    # plot_resource_adequacy((resource_adequacy_with_conventional_hydropower - resource_adequacy_with_actual_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Only conventional hydropower', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_0_5_pumped_storage_hydropower - resource_adequacy_with_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', '50% of hydropower is pumped storage', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_1_0_pumped_storage_hydropower - resource_adequacy_with_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Current pumped storage hydropower capacity', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_expanded_pumped_storage_hydropower - resource_adequacy_with_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Expanded pumped storage hydropower', False, 'difference')
    
    # plot_resource_adequacy((resource_adequacy_with_expanded_reservoir_pumped_storage_hydropower - resource_adequacy_with_conventional_hydropower).T*100, wind_and_solar_generation_fractions, wind_generation_fractions, mix_with_highest_resource_adequacy, 'plasma', 'w', 'Expanded pumped storage hydropower', False, 'difference')








    # fig, ax = plt.subplots()

    # dataset['Electricity demand'].plot(ax=ax, label='Electricity demand')
    # (electrified_space_heating_demand_in_residential_sector * tj_to_mwh * dataset['Residential space heating demand']).plot(ax=ax, label='Electrified residential space heating demand')
    # (electrified_space_heating_demand_in_services_sector * tj_to_mwh * dataset['Services space heating demand']).plot(ax=ax, label='Electrified services space heating demand')
    # (cooling_demand * tj_to_mwh * dataset['Cooling demand']).plot(ax=ax, label='Cooling demand')
    # (space_heating_demand_in_residential_sector * tj_to_mwh * dataset['Residential space heating demand']).plot(ax=ax, label='Residential space heating demand')
    # (space_heating_demand_in_services_sector * tj_to_mwh * dataset['Services space heating demand']).plot(ax=ax, label='Services space heating demand')

    # ax.legend()
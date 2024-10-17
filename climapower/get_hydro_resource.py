import os
import pandas as pd

import modules.directories as directories
import modules.general_utilities as general_utilities
import modules.hydro_resource as hydro_resource


def main():
    '''
    Compute and save the aggregated hydropower inflow for a given country and for all the years in the time period of interest.
    '''

    conventional_and_pumped_storage = False

    if conventional_and_pumped_storage == True:
        hydropower_tech = 'Conventional and pumped-storage hydropower'
        variable_name = 'hydropower__inflow_time_series__conventional_and_pumped_storage'
    else:
        hydropower_tech = 'Run-of-river hydropower'
        variable_name = 'hydropower__inflow_time_series__run_of_river'

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated hydropower inflow.
    if isinstance(country_info, pd.Series):

        if not os.path.exists(directories.get_postprocessed_data_path(country_info, variable_name)) and country_info[hydropower_tech]:
            hydro_resource.compute_aggregated_hydropower_inflow(country_info, conventional_and_pumped_storage=conventional_and_pumped_storage)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if not os.path.exists(directories.get_postprocessed_data_path(country_info_series, variable_name)) and country_info_series[hydropower_tech]:
                hydro_resource.compute_aggregated_hydropower_inflow(country_info_series, conventional_and_pumped_storage=conventional_and_pumped_storage)


if __name__ == "__main__":

    main()
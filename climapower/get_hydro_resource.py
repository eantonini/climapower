import os
import pandas as pd

import modules.directories as directories
import modules.general_utilities as general_utilities
import modules.hydro_resource as hydro_resource


def main():
    '''
    Compute and save the aggregated hydropower inflow for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated hydropower inflow.
    if isinstance(country_info, pd.Series):

        if not os.path.exists(directories.get_postprocessed_data_path(country_info, 'hydropower__inflow_time_series__conventional_and_pumped_storage')) and country_info['Hydropower']:
            hydro_resource.compute_aggregated_hydropower_inflow(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if not os.path.exists(directories.get_postprocessed_data_path(country_info_series, 'hydropower__inflow_time_series__conventional_and_pumped_storage')) and country_info_series['Hydropower']:
                hydro_resource.compute_aggregated_hydropower_inflow(country_info_series)


if __name__ == "__main__":

    main()
import os
import pandas as pd

import modules.directories as directories
import modules.general_utilities as general_utilities
import modules.solar_resource as solar_resource


def main():
    '''
    Compute and save the aggregated solar capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    if isinstance(country_info, pd.Series):

        if not os.path.exists(directories.get_postprocessed_data_path(country_info, 'solar__capacity_factor_time_series')):
            solar_resource.compute_aggregated_solar_capacity_factor(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if not os.path.exists(directories.get_postprocessed_data_path(country_info_series, 'solar__capacity_factor_time_series')):
                solar_resource.compute_aggregated_solar_capacity_factor(country_info_series)


if __name__ == "__main__":

    main()
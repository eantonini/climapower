import os
import pandas as pd

import modules.directories as directories
import modules.general_utilities as general_utilities
import modules.temperature as temperature


def main():
    '''
    Compute and save the aggregated solar capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    if isinstance(country_info, pd.Series):

        if not os.path.exists(directories.get_postprocessed_data_path(country_info, 'temperature__time_series')):
            temperature.compute_aggregated_temperature(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if not os.path.exists(directories.get_postprocessed_data_path(country_info_series, 'temperature__time_series')):
                temperature.compute_aggregated_temperature(country_info_series)


if __name__ == "__main__":

    main()
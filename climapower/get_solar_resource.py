import pandas as pd

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

        solar_resource.compute_aggregated_solar_capacity_factor(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            solar_resource.compute_aggregated_solar_capacity_factor(country_info_series)


if __name__ == "__main__":

    main()
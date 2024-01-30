import pandas as pd

import modules.general_utilities as general_utilities
import modules.wind_resource as wind_resource


def main():
    '''
    Compute and save the aggregated wind capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated capacity factor for the onshore and offshore wind resource.
    if isinstance(country_info, pd.Series):

        wind_resource.compute_aggregated_wind_capacity_factor(country_info, offshore=False)

        if country_info['Offshore wind']:
            wind_resource.compute_aggregated_wind_capacity_factor(country_info, offshore=True)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            wind_resource.compute_aggregated_wind_capacity_factor(country_info_series, offshore=False)

            if country_info_series['Offshore wind']:
                wind_resource.compute_aggregated_wind_capacity_factor(country_info_series, offshore=True)


if __name__ == "__main__":

    main()
import pandas as pd

import modules.general_utilities as general_utilities
import modules.heating_demand as heating_demand


def main():
    '''
    Compute and save the aggregated heating demand for a given country, for all the years in the time period of interest, and for all sectors.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    if isinstance(country_info, pd.Series):

        heating_demand.compute_aggregated_heating_demand(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            heating_demand.compute_aggregated_heating_demand(country_info_series)


if __name__ == "__main__":

    main()
import modules.general_utilities as general_utilities
import modules.cooling_demand as cooling_demand


def main():
    '''
    Compute and save the aggregated cooling demand for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    if isinstance(country_info, pd.Series):

        cooling_demand.compute_aggregated_cooling_demand(country)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            cooling_demand.compute_aggregated_cooling_demand(country_info_series)


if __name__ == "__main__":

    main()
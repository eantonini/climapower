import modules.general_utilities as general_utilities
import modules.heating_demand as heating_demand


def main():
    '''
    Compute and save the aggregated heating demand for a given country, for all the years in the time period of interest, and for all sectors.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    heating_demand.compute_aggregated_heating_demand(country)


if __name__ == "__main__":

    main()
import modules.general_utilities as general_utilities
import modules.cooling_demand as cooling_demand


def main():
    '''
    Compute and save the aggregated cooling demand for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    cooling_demand.compute_aggregated_cooling_demand(country)


if __name__ == "__main__":

    main()
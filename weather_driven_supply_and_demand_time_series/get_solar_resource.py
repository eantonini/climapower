import modules.general_utilities as general_utilities
import modules.solar_resource as solar_resource


def main():
    '''
    Compute and save the aggregated wind capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    solar_resource.compute_aggregated_solar_capacity_factor(country)


if __name__ == "__main__":

    main()
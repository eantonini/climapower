import modules.general_utilities as general_utilities
import modules.hydro_resource as hydro_resource


def main():
    '''
    Compute and save the aggregated hydropower inflow for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    hydro_resource.compute_aggregated_hydropower_inflow(country)


if __name__ == "__main__":

    main()
import modules.general_utilities as general_utilities
import modules.hydro_validation as hydro_validation


def main():
    '''
    Calibrate the aggregated hydropower inflow for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    hydro_validation.validate_hydropower_inflow_time_series(country_info)


if __name__ == "__main__":

    main()
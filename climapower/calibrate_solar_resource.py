import modules.general_utilities as general_utilities
import modules.solar_validation as solar_validation


def main():
    '''
    Calibrate the aggregated wind capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Compute the aggregated capacity factor for the onshore wind resource.
    solar_validation.validate_solar_capacity_factor_time_series(country_info)


if __name__ == "__main__":

    main()
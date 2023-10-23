import modules.general_utilities as general_utilities
import modules.wind_resource as wind_resource


def main():
    '''
    Compute and save the aggregated wind capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated capacity factor for the onshore and offshore wind resource.
    wind_resource.compute_aggregated_wind_capacity_factor(country, offshore=False)
    if country['Offshore']:
        wind_resource.compute_aggregated_wind_capacity_factor(country, offshore=True)


if __name__ == "__main__":

    main()
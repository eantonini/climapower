import modules.general_utilities as general_utilities
import modules.resource_adequacy as resource_adequacy


def main():
    '''
    Compute the resource adequacy of the power system of the given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country = general_utilities.read_command_line_arguments()

    # Compute the aggregated solar capacity factor.
    resource_adequacy.compute_resource_adequacy(country)


if __name__ == "__main__":

    main()
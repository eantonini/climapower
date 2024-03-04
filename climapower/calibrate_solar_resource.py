import pandas as pd

import modules.general_utilities as general_utilities
import modules.solar_validation as solar_validation


def main():
    '''
    Calibrate the aggregated solar capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Calibrate the aggregated capacity factor for the solar resource.
    if isinstance(country_info, pd.Series):

        if general_utilities.get_years_for_calibration(country_info, 'solar'):

            solar_validation.validate_solar_capacity_factor_time_series(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if general_utilities.get_years_for_calibration(country_info_series, 'solar'):

                solar_validation.validate_solar_capacity_factor_time_series(country_info_series)


if __name__ == "__main__":

    main()
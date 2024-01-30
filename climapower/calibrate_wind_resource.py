import math

import modules.general_utilities as general_utilities
import modules.wind_validation as wind_validation


def main():
    '''
    Calibrate the aggregated wind capacity factor for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Calibrate the aggregated capacity factor for the onshore wind resource.
    if isinstance(country_info, pd.Series):

        if general_utilities.get_years_for_calibration(country_info, 'wind'):

            wind_validation.validate_wind_capacity_factor_time_series(country_info, offshore=False)
        
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if general_utilities.get_years_for_calibration(country_info, 'wind'):

                wind_validation.validate_wind_capacity_factor_time_series(country_info_series, offshore=False)


if __name__ == "__main__":

    main()
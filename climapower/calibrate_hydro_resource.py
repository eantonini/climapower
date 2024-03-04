import pandas as pd

import modules.general_utilities as general_utilities
import modules.hydro_validation as hydro_validation


def main():
    '''
    Calibrate the aggregated hydropower inflow for a given country and for all the years in the time period of interest.
    '''

    # Get the country of interest.
    country_info = general_utilities.read_command_line_arguments()

    # Calibrate the hydropower inflow.
    if isinstance(country_info, pd.Series):

        if general_utilities.get_years_for_calibration(country_info, 'hydropower'):

            hydro_validation.validate_hydropower_inflow_time_series(country_info)
    
    else:

        for country_name in country_info['Name']:

            country_info_series = country_info.loc[country_info['Name']==country_name].squeeze()

            if general_utilities.get_years_for_calibration(country_info_series, 'hydropower'):

                hydro_validation.validate_hydropower_inflow_time_series(country_info_series)


if __name__ == "__main__":

    main()
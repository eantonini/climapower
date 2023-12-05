import pandas as pd

from entsoe.exceptions import NoMatchingDataError
from modules.exceptions import NotEnoughDataError

import settings
import modules.general_utilities as general_utilities
import modules.energy_data as energy_data


def main():

    log_file = 'check_energy_data'
    
    country_list = general_utilities.get_countries()
  
    dataframe = pd.DataFrame(columns=['country',
                                      'year',
                                      'offshore',
                                      'entsoe_offshore_wind_generation',
                                      'entsoe_offshore_wind_installed_capacity',
                                      'opsd_offshore_wind_generation',
                                      'opsd_offshore_wind_installed_capacity',
                                      'entsoe_onshore_wind_generation',
                                      'entsoe_onshore_wind_installed_capacity',
                                      'opsd_onshore_wind_generation',
                                      'opsd_onshore_wind_installed_capacity',
                                      'ei_wind_installed_capacity',
                                      'entsoe_solar_generation',
                                      'entsoe_solar_installed_capacity',
                                      'opsd_solar_generation',
                                      'opsd_solar_installed_capacity',
                                      'ei_solar_installed_capacity',
                                      'entsoe_reservoir_filling_level',
                                      'entsoe_hydropower_inflow'])
    
    general_utilities.write_to_log_file(log_file, 'Starting to check energy data\n\n', new_file=True, write_time=True)
    
    for country_name in country_list['Name']:

        country_info = country_list.loc[country_list['Name']==country_name].squeeze()

        general_utilities.write_to_log_file(log_file, 'Processing ' + country_info['Name'] + '.\n\n')
        print('Processing ' + country_info['Name'] + '.\n')

        if country_info['Offshore']:
            general_utilities.write_to_log_file(log_file, '- ' + country_info['Name'] + ' has offshore wind.\n\n')
        else:
            general_utilities.write_to_log_file(log_file, '- ' + country_info['Name'] + ' does not have offshore wind.\n\n')

        for year in range(settings.comparison_start_year, settings.comparison_end_year+1):

            print(' - ' + str(year) + '\n')

            if country_info['Offshore']:

                general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E offshore wind generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
                try:
                    entsoe_offshore_wind_generation_time_series = energy_data.get_entsoe_generation(country_info, year, 'B18')
                    entsoe_offshore_wind_generation = entsoe_offshore_wind_generation_time_series.max()
                except (NoMatchingDataError, NotEnoughDataError):
                    entsoe_offshore_wind_generation = None
                    general_utilities.write_to_log_file(log_file, '  ** No data\n')
                
                general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E offshore wind capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
                try:
                    entsoe_offshore_wind_total_installed_capacity = energy_data.get_entsoe_capacity(country_info, year, 'B18')
                except (NoMatchingDataError, NotEnoughDataError):
                    entsoe_offshore_wind_total_installed_capacity = None
                    general_utilities.write_to_log_file(log_file, '  ** No data\n')

                general_utilities.write_to_log_file(log_file, '- Getting OPSD offshore wind generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
                opsd_offshore_wind_generation_time_series, opsd_offshore_wind_total_installed_capacity = energy_data.get_opsd_generation_and_capacity(country_info, year, 'wind', offshore=True)
                try:
                    opsd_offshore_wind_generation = opsd_offshore_wind_generation_time_series.max()
                except AttributeError:
                    opsd_offshore_wind_generation = None
                    general_utilities.write_to_log_file(log_file, '  ** No data\n')

                general_utilities.write_to_log_file(log_file, '- Getting OPSD offshore wind capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
                try:
                    opsd_offshore_wind_total_installed_capacity = opsd_offshore_wind_total_installed_capacity.max()
                except AttributeError:
                    opsd_offshore_wind_total_installed_capacity = None
                    general_utilities.write_to_log_file(log_file, '  ** No data\n')
            
            else:

                entsoe_offshore_wind_generation = None
                entsoe_offshore_wind_total_installed_capacity = None
                opsd_offshore_wind_generation = None
                opsd_offshore_wind_total_installed_capacity = None

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E onshore wind generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_onshore_wind_generation_time_series = energy_data.get_entsoe_generation(country_info, year, 'B19')
                entsoe_onshore_wind_generation = entsoe_onshore_wind_generation_time_series.max()
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_onshore_wind_generation = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E onshore wind capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_onshore_wind_total_installed_capacity = energy_data.get_entsoe_capacity(country_info, year, 'B19')
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_onshore_wind_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting OPSD onshore wind generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            opsd_onshore_wind_generation_time_series, opsd_onshore_wind_total_installed_capacity = energy_data.get_opsd_generation_and_capacity(country_info, year, 'wind', offshore=False)
            try:
                opsd_onshore_wind_generation = opsd_onshore_wind_generation_time_series.max()
            except AttributeError:
                opsd_onshore_wind_generation = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')
            
            general_utilities.write_to_log_file(log_file, '- Getting OPSD onshore wind capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                opsd_onshore_wind_total_installed_capacity = opsd_onshore_wind_total_installed_capacity.max()
            except AttributeError:
                opsd_onshore_wind_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting EI wind capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                ei_wind_total_installed_capacity = energy_data.get_ei_capacity(country_info, year, 'wind')
            except IndexError:
                ei_wind_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E solar generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_solar_generation_time_series = energy_data.get_entsoe_generation(country_info, year, 'B16')
                entsoe_solar_generation = entsoe_solar_generation_time_series.max()
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_solar_generation = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E solar capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_solar_total_installed_capacity = energy_data.get_entsoe_capacity(country_info, year, 'B16')
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_solar_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting OPSD solar generation data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            opsd_solar_generation_time_series, opsd_solar_total_installed_capacity = energy_data.get_opsd_generation_and_capacity(country_info, year, 'solar')
            try:
                opsd_solar_generation = opsd_solar_generation_time_series.max()
            except AttributeError:
                opsd_solar_generation = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')
            
            general_utilities.write_to_log_file(log_file, '- Getting OPSD solar capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                opsd_solar_total_installed_capacity = opsd_solar_total_installed_capacity.max()
            except AttributeError:
                opsd_solar_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting EI solar capacity data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                ei_solar_total_installed_capacity = energy_data.get_ei_capacity(country_info, year, 'solar')
            except IndexError:
                ei_solar_total_installed_capacity = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E reservoir filling level data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_reservoir_filling_level = energy_data.get_entsoe_reservoir_filling_level(country_info, year)
                entsoe_reservoir_filling_level = entsoe_reservoir_filling_level.max()
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_reservoir_filling_level = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')

            general_utilities.write_to_log_file(log_file, '- Getting ENTSO-E hydropower inflow data for ' + country_info['Name'] + ' in ' + str(year) + '.\n')
            try:
                entsoe_hydropower_inflow = energy_data.get_entsoe_hydropower_inflow(country_info, year)
                entsoe_hydropower_inflow = entsoe_hydropower_inflow.max()
            except (NoMatchingDataError, NotEnoughDataError):
                entsoe_hydropower_inflow = None
                general_utilities.write_to_log_file(log_file, '  ** No data\n')
            
            general_utilities.write_to_log_file(log_file, '\n')

            new_line = pd.DataFrame(data={'country': country_info['Name'],
                                          'year': year,
                                          'offshore': country_info['Offshore'].astype(str),
                                          'entsoe_offshore_wind_generation': entsoe_offshore_wind_generation,
                                          'entsoe_offshore_wind_installed_capacity': entsoe_offshore_wind_total_installed_capacity,
                                          'opsd_offshore_wind_generation': opsd_offshore_wind_generation,
                                          'opsd_offshore_wind_installed_capacity': opsd_offshore_wind_total_installed_capacity,
                                          'entsoe_onshore_wind_generation': entsoe_onshore_wind_generation,
                                          'entsoe_onshore_wind_installed_capacity': entsoe_onshore_wind_total_installed_capacity,
                                          'opsd_onshore_wind_generation': opsd_onshore_wind_generation,
                                          'opsd_onshore_wind_installed_capacity': opsd_onshore_wind_total_installed_capacity,
                                          'ei_wind_installed_capacity': ei_wind_total_installed_capacity,
                                          'entsoe_solar_generation': entsoe_solar_generation,
                                          'entsoe_solar_installed_capacity': entsoe_solar_total_installed_capacity,
                                          'opsd_solar_generation': opsd_solar_generation,
                                          'opsd_solar_installed_capacity': opsd_solar_total_installed_capacity,
                                          'ei_solar_installed_capacity': ei_solar_total_installed_capacity,
                                          'entsoe_reservoir_filling_level': entsoe_reservoir_filling_level,
                                          'entsoe_hydropower_inflow': entsoe_hydropower_inflow},
                                          index=[0])

            dataframe = pd.concat([dataframe, new_line], ignore_index=True)

            print('')
    
    dataframe.to_csv('check_energy_data.csv', index=False)


if __name__ == "__main__":

    main()
import os
import glob
import difflib
import pandas as pd

import settings
import modules.general_utilities as general_utilities
import modules.directories as directories
import modules.energy_supply_data as energy_supply_data


def save_calibration_coefficients(country_info, year, resource_type, coefficients, index, additional_info = ''):
    '''
    Save the calibration coefficients for the wind resource.
    
    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    year : int
        Year of interest
    resource_type : str
        Type of resource of interest
    coefficients : list of floats or numpy.ndarray
        List of calibration coefficients
    index : list of indices or numpy.ndarray
        List of indices of the calibration coefficients
    offshore : bool, optional
        True if the resource of interest is offshore wind
    additional_info : str, optional
        Additional information to add at the end of the filename
    '''
    
    # Get the full data path of the wind calibration coefficients.
    coefficients_filename = directories.get_calibration_coefficients_data_path(country_info, resource_type, additional_info=additional_info)
        
    # Check if the coefficients have already been calculated.
    if os.path.exists(coefficients_filename):

        dataframe = pd.read_csv(coefficients_filename, index_col=0)

        try:
            __ = dataframe[str(year)]
            already_calculated = True
        except:
            already_calculated = False
    
    else:

        dataframe = pd.DataFrame()
        already_calculated = False
    
    if not already_calculated:
        # Append the new coefficient to the dataframe.
        new_dataframe = pd.DataFrame(data=coefficients, index=index, columns=[year])
        dataframe = dataframe.combine_first(new_dataframe)

        # Save the dataframe.
        dataframe.to_csv(coefficients_filename)


def get_weighted_averaged_coefficients(coefficients_filename, country_info, resource_type, years_of_interest):
    '''
    Get the weighted average of the calibration coefficients across all the years, where the weights are the installed capacity in each year.
    
    Parameters
    ----------
    coefficients_filename : str
        Full data path of the calibration coefficients filename
    country_info : pandas.Series
        Series containing the information of the country of interest
    resource_type : str
        Type of resource of interest
    years_of_interest : list of str
        List of years of interest

    Returns
    -------
    weighted_coefficients : pandas.Series
        Series containing the weighted average of the calibration coefficients
    '''

    # Read the dataframe from csv files.
    dataframe = pd.read_csv(coefficients_filename, index_col=0)

    # Get the installed capacity of the resource of interest in the country and years of interest.
    # For wind, it is assumed that all wind capacity in the EI database is onshore.
    installed_capacity = [energy_supply_data.get_ei_capacity(country_info, int(year), resource_type) for year in years_of_interest]
    installed_capacity = pd.Series(installed_capacity, index=years_of_interest)

    # Calculate the weighted average of the calibration coefficients across all the years where the weights are the installed capacity in each year.
    weighted_coefficients =  (dataframe[years_of_interest]*installed_capacity).sum(axis=1) / installed_capacity.sum()

    return weighted_coefficients


def read_calibration_coefficients(country_info, resource_type, offshore=False):
    '''
    Read the calibration coefficients. If the coefficient of the country are not available, calculate them as the weighted average of the coefficients of the other countries.

    Parameters
    ----------
    country_info : pandas.Series
        Series containing the information of the country of interest
    resource_type : str
        Type of resource of interest
    offshore : bool, optional
        True if the resource of interest is offshore wind

    Returns
    -------
    coefficients : pandas.Series
        Series containing the calibration coefficients
    '''
    
    # Set additional information to add to the filename in case of wind.
    if resource_type == 'wind':
        additional_info = ('__offshore' if offshore else '__onshore')
    else:
        additional_info = ''
    
    # Get the full data path of the wind calibration coefficients.
    coefficients_filename = directories.get_calibration_coefficients_data_path(country_info, resource_type, additional_info=additional_info)

    if os.path.exists(coefficients_filename):

        # Get the list of years of interest.
        years_of_interest = [str(year) for year in general_utilities.get_years_for_calibration(country_info, resource_type, offshore=offshore)]
    
        # Calculate the weighted average of the calibration coefficients across all the years, where the weights are the installed capacity in each year.
        coefficients =  get_weighted_averaged_coefficients(coefficients_filename, country_info, resource_type, years_of_interest)

    else:
        
        # Get the filename of the calibration coefficients of the other countries.
        coefficients_filename = coefficients_filename.replace(country_info['ISO Alpha-2'], '*')
        coefficients_filename_list = glob.glob(coefficients_filename)

        # Initialize the dataframe of the calibration coefficients and the series of the installed capacity in the last year of interest.
        coefficients = pd.DataFrame(dtype=float)
        installed_capacity = pd.Series(dtype=float)

        # Get the list of countries and their information.
        country_info_list = general_utilities.get_countries()

        for other_coefficients_filename in coefficients_filename_list:

            # Get the ISO code of the other country.
            letters_of_other_country_ISO_code = [li[-1] for li in difflib.ndiff(coefficients_filename, other_coefficients_filename) if li[0] == '+' and li[-1].isalpha()]
            other_country_ISO_code = ''.join(letters_of_other_country_ISO_code)

            # Get the info of the other country.
            other_country_info = country_info_list.loc[country_info_list['ISO Alpha-2']==other_country_ISO_code].squeeze()

            # Get the list of years of interest.
            years_of_interest = [str(year) for year in general_utilities.get_years_for_calibration(other_country_info, resource_type, offshore=offshore)]

            # Calculate the weighted average of the calibration coefficients across all the years, where the weights are the installed capacity in each year.
            coefficients[other_country_info['Name']] =  get_weighted_averaged_coefficients(other_coefficients_filename, other_country_info, resource_type, years_of_interest)

            # Get the installed capacity of the resource of interest in the country and in the last year of interest.
            installed_capacity[other_country_info['Name']] = energy_supply_data.get_ei_capacity(other_country_info, int(years_of_interest[-1]), resource_type)
        
        # Calculate the weighted average of the calibration coefficients across all the countries, where the weights are the installed capacity in each country.
        coefficients =  (coefficients*installed_capacity).sum(axis=1) / installed_capacity.sum()

    return coefficients
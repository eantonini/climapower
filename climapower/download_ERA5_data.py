import cdsapi
import os

import modules.directories as directories


# Create a new CDS API session.
c = cdsapi.Client()

# Define the ERA5 variable to download.
# ERA5_variable_name = '2m_temperature'
# ERA5_variable_name = 'surface_pressure'
# ERA5_variable_name = '100m_u_component_of_wind'
# ERA5_variable_name = '100m_v_component_of_wind'
# ERA5_variable_name = 'forecast_surface_roughness'
# ERA5_variable_name = 'total_sky_direct_solar_radiation_at_surface'
# ERA5_variable_name = 'surface_net_solar_radiation'
# ERA5_variable_name = 'surface_solar_radiation_downwards'
# ERA5_variable_name = 'toa_incident_solar_radiation'
ERA5_variable_name = 'runoff'

# Download the ERA5 data.
# for year in range(1940,1971):
# for year in range(1971,2001):
for year in range(2001,2023):

    data_folder = directories.get_climate_data_path(year, ERA5_variable_name, climate_data_source='historical', return_folder=True)

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    data_file = directories.get_climate_data_path(year, ERA5_variable_name)
    
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': ERA5_variable_name,
            'year': str(int(year)),
            'month': [str(int(x)) for x in range(1,13)],
            'day': [str(int(x)) for x in range(1,32)],
            'time': [str(int(x))+':00' if x>=10 else '0'+str(int(x))+':00' for x in range(0,24)],
            'format': 'netcdf',
            'area': [72, -22, 27, 45],
        },
        data_file)
import cdsapi
import os

import modules.directories as directories


# Create a new CDS API session.
c = cdsapi.Client()

# Define the ERA5 variable to download.
ERA5_variables = ['2m_temperature',
                  'surface_pressure',
                  '100m_u_component_of_wind',
                  '100m_v_component_of_wind',
                  'forecast_surface_roughness',
                  'total_sky_direct_solar_radiation_at_surface',
                  'surface_net_solar_radiation',
                  'surface_solar_radiation_downwards',
                  'toa_incident_solar_radiation',
                  'runoff',
                  ]

# Define the years for the data download.
start_year = 1940
end_year = 2023

# Download the ERA5 data.
for ERA5_variable_name in ERA5_variables:
    
    for year in range(start_year,end_year+1):

        data_folder = directories.get_climate_data_path(year, ERA5_variable_name, climate_data_source='reanalysis', return_folder=True)

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
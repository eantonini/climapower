import cdsapi
import os

import modules.settings as settings


# Create a new CDS API session
c = cdsapi.Client()

# Define the ERA5 data to download

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
custom_variable_name = 'hourly_'+ERA5_variable_name

# Download the ERA5 data

# for ii in range(1940,1971):
# for ii in range(1971,2001):
for ii in range(2005,2023):
# for ii in range(2001,2023):

    data_folder = settings.climate_data_directory+'/ERA5-Europe-'+ERA5_variable_name

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    data_file = data_folder+'/ERA5-{:d}-gridded_'.format(ii)+custom_variable_name+'.nc'
    
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': ERA5_variable_name,
            'year': str(int(ii)),
            'month': [str(int(x)) for x in range(1,13)],
            'day': [str(int(x)) for x in range(1,32)],
            'time': [str(int(x))+':00' if x>=10 else '0'+str(int(x))+':00' for x in range(0,24)],
            'format': 'netcdf',
            'area': [72, -22, 27, 45],
        },
        data_file)
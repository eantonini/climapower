import cdsapi
import os

import modules.directories as directories


# Create a new CDS API session.
c = cdsapi.Client()

# Define the CMIP6 variable to download.
CMIP6_variables = ['near_surface_air_temperature',
                   'near_surface_wind_speed',
                   'surface_downwelling_longwave_radiation',
                   'surface_downwelling_shortwave_radiation',
                   'surface_upwelling_longwave_radiation',
                   'surface_upwelling_shortwave_radiation',
                   'toa_incident_shortwave_radiation',
                   'total_runoff',
                   ]

# Define the CMIP6 models.
models = ['mpi_esm1_2_lr', 'cmcc_esm2', 'cesm2', 'hadgem3_gc31_ll', 'bcc_csm2_mr']

# Define the CMIP6 experiments.
ssps = ['ssp1_2_6', 'ssp2_4_5', 'ssp5_8_5']

# Define the years for the data download.
start_year = 2015
end_year = 2100

# Download the CORDEX data.
for CMIP6_variable_name in CMIP6_variables:

    # It is better to have the wind speed at dayly resolution.
    if CMIP6_variable_name == 'near_surface_wind_speed':
        temporal_resolution = 'daily'
    else:
        temporal_resolution = 'monthly'
    
    for model in models:
        
        for ssp in ssps:

            data_folder = directories.get_climate_data_path(2100, CMIP6_variable_name, return_folder=True, time_resolution=temporal_resolution, climate_data_source='CMIP6_projections', focus_region='World',
                                                            shared_socioeconomic_pathway=ssp, climate_model=model)

            if not os.path.exists(data_folder):
                os.makedirs(data_folder)

            data_file = directories.get_climate_data_path(2100, CMIP6_variable_name, time_resolution=temporal_resolution, climate_data_source='CMIP6_projections', focus_region='World',
                                                            shared_socioeconomic_pathway=ssp, climate_model=model).replace('.nc', '.zip').replace('2100',str(start_year)+'_'+str(end_year))
            
            if not os.path.exists(data_file):

                if temporal_resolution == 'daily':

                    c.retrieve(
                    'projections-cmip6',
                    {
                        'format': 'zip',
                        'experiment': ssp,
                        'temporal_resolution': temporal_resolution,
                        'variable': CMIP6_variable_name,
                        'model': model,
                        'year': [str(int(year)) for year in range(start_year,end_year+1)],
                        'month': [str(int(x)) for x in range(1,13)],
                        'day': [str(int(x)) for x in range(1,32)]
                    },
                    data_file)
                
                else:

                    c.retrieve(
                    'projections-cmip6',
                    {
                        'format': 'zip',
                        'experiment': ssp,
                        'temporal_resolution': temporal_resolution,
                        'variable': CMIP6_variable_name,
                        'model': model,
                        'year': [str(int(year)) for year in range(start_year,end_year+1)],
                        'month': [str(int(x)) for x in range(1,13)]
                    },
                    data_file)
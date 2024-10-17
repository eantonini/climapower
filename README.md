# Climapower

This repository contains scripts to generate weather- and climate-driven power supply and demand time series for power and energy system analyses.

The methodology is described in the following paper:

> **Title**: "Climapower: A Python package for generating weather- and climate-driven power supply and demand time series for power and energy system analyses

## Installation

To install the package, clone the repository and install the Python packages available in the yaml files in the `environments` folder:

```bash
git clone
cd climapower
conda env create -f environments/environment_for_retrieving_climate_data.yml
conda deactivate
conda env create -f environments/environment_for_converting_climate_data_to_energy.yml
conda deactivate
```

## Usage

### Retrieve meteorological data

To retrieve meteorological data, you need to have a [CDS API key](https://cds.climate.copernicus.eu/api-how-to) and actvate the environment for retrieving meteorological data:

```bash
conda activate retrieve_climate_data
```

Then, you can run the script to retrieve the data:

```bash
python download_ERA5_data.py
```

or

```bash
python download_CORDEX_data.py
```

### Convert meteorological data to energy time series

To convert meteorological data to energy time series, you need to activate the environment for converting meteorological data to energy:

```bash
conda activate climate_to_energy_conversion
```

Then, you can run the script to convert the data:

```bash
python get_wind_resource.py
```

or

```bash
python get_solar_resource.py
```

or

```bash
python get_hydro_resource.py
```

or

```bash
python get_heating_demand.py
```

or

```bash
python get_cooling_demand.py
```

These scripts will generate time series for wind power, solar power, hydro power, heating demand, and cooling demand for all European countries. Alternatively, you can specify the country name as an argument to generate the time series for a specific country:

```bash
python get_wind_resource.py "Germany"
```

### Calibrate energy time series

To calibrate the energy time series, you need to activate the environment for calibrating energy time series:

```bash
conda activate climate_to_energy_conversion
```

Then, you can run the script to calibrate the data:

```bash
python calibrate_wind_resource.py
```

or

```bash
python calibrate_solar_resource.py
```

or

```bash
python calibrate_hydro_resource.py
```
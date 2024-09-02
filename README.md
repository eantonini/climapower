# Climapower

This repository contains scripts to generate weather- and climate-driven power supply and demand time series for power and energy system analyses.

## Installation

To install the package, clone the repository and install the Python packages available in the yaml files in the `environments` folder

```bash
git clone
cd climapower
conda env create -f environments/environment_for_retrieving_climate_data.yml
conda deactivate
conda env create -f environments/environment_for_converting_climate_data_to_energy.yml
```

## Usage

### Retrieve meteorological data

To retrieve meteorological data, you need to have a [CDS API key](https://cds.climate.copernicus.eu/api-how-to) and actvate the environment for retrieving climate data:

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
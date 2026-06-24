✔ What data  
✔ Where data comes from
✔ how to collect data --> automated, easy access 
✔ How to download (login info, API)
✔ Formats?
✔ potential warnings about availability, etc...
✔ sample datasets

# Data documentation

SwarmDF enables easy access to a variety of ionospheric and thermospheric datasets through automatic data retrieval and preprocessing. The user only needs to provide a start and end time; the SwarmDF data manager handles the downloading, preprocessing, and loading of the required daily data files for all supported datasets. This allows users to focus on scientific analysis rather than data acquisition and formatting.

The simplest way to download data is through the graphical user interface. Simply select an analysis interval, a Swarm satellite, and the datasets of interests. 

Outside the GUI, just do:

```python
datahandler = DataManager(start_time, end_time, datasets2download)
datasets = datahandler.datasets
```

## Supported datasets 

| Dataset | Measurement type | Source |
|----------|----------|----------|
| Swarm EFI | Convection | ESA Swarm mission |
| Swarm FAC | Space magnetic perturbations | ESA Swarm mission |
| SuperDARN | Convection | SuperDARN radar network |
| SuperMAG | Ground magnetic perturbations | SuperMAG magnetometer network |
| Iridium AMPERE | Space magnetic perturbations | AMPERE project |
| DMSP SSIES | Convection | DMSP SSIES instrument |


The sections below provide a brief description of each supported dataset, its data source, and important considerations for its use within SwarmDF.

### Swarm 

Description: Swarm blabla + add link to mission website 

Source: ESA Swarm Level-2 products (link)

Data used by SwarmDF:
- EFI - Cross-track ion drift velocity
- FAC? 

### SuperDARN

SuperDARN is a global network of high-frequency radars that measures the line-of-sight velocity of ionospheric plasma. These observations provide information about large-scale ionospheric convection.

#### Data source: 
... 

#### Data used by SwarmDF:
- Line-of-sight plasma velocity
SuperDARN observations are ingested as convection measurements and constrain the electric field and plasma drift in the Lompe inversion.

#### Important caveats:
- Measures only the velocity component along the radar beam.
- Coverage is limited and strongly depends on radar location.
- Data gaps are common.

## SuperMAG 

SuperMAG is... 

Data used by SwarmDF:
- Ground magnetic perturbations

## Iridium/AMPERE

## DMSP/SSIES

<!-- potentially show user how to add their own datafile and how to make it a lompe data object -->

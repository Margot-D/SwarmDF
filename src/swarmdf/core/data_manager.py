"""
SwarmDF — Data collection module

Retrieves multi-source datasets for data assimilation 
and reconstruction of ionospheric electrodynamics.

"""

import pandas as pd
import os
from pathlib import Path
from lompe.data_tools import dataloader, datadownloader

# TODO how to deal with user id? does the user have to log into each database? 

class DataManager:
    """
    Handle downloading, loading, and combining daily datasets.

    Parameters
    ----------
    start_time : datetime-like
        Start of the user-defined time interval.
    end_time : datetime-like
        End of the user-defined time interval.
    data_path : str
    selected_sources : list
        List of dataset names to download.
    demo : bool, optional
     If True, uses built-in sample datasets for the example event (2014-12-15).
    """
        
    def __init__(self, start_time, end_time, selected_sources, demo=False):

        package_root = Path(__file__).resolve().parents[1]

        if demo: 
            self.data_path = str(package_root / "data" / "sample_datasets") + "/"
        else:
            self.data_path = str(package_root / "data") + "/"
        
        print(self.data_path)
        
        # List of dates covering the full time interval
        self.event_dates = pd.date_range(start=start_time, end=end_time, freq="D")
        self.event_dates = [d.strftime("%Y%m%d") for d in self.event_dates]

        # self.event_date = start_time.strftime("%Y%m%d") #TODO change to next line when Fasil has final version of datadownloader 
        # # self.event_date = start_time.strftime("%Y-%m-%d")

        self.datasets = {}

        # Loop over each day
        for event_date in self.event_dates:

            # download/collect data files for this specific day
            self.fetch_data(event_date, selected_sources)
            daily_data = self.load_data(event_date, selected_sources)

            # store data per dataset type
            for key, df in daily_data.items():
                if key not in self.datasets:
                    self.datasets[key] = []
                self.datasets[key].append(df)

        # Combine datasets across all days
        for key in self.datasets:
            self.datasets[key] = (pd.concat(self.datasets[key]).sort_index())

    def fetch_data(self, event_date, selected_sources):
        """ Check if data files for selected sources already exist in the user data folder; download them if needed"""

        required_sources = {''}  # always needed
        sources_to_fetch = set(selected_sources) | required_sources

        for source in sources_to_fetch:
            try: 
                if source == 'swarm_mag':
                    datadownloader.download_swarmB(event_date, tempfile_path=self.data_path)

                if source == 'swarm_efield':
                    datadownloader.download_swarmE(event_date, tempfile_path=self.data_path)

                if source == 'superdarn':
                    datadownloader.download_sdarn(event_date, tempfile_path=self.data_path)

                if source == 'supermag': #TODO fix userid
                    datadownloader.download_smag(event_date, userid='mdecotte', tempfile_path=self.data_path) 

                if source == 'iridium_ampere':
                    iridium_file = datadownloader.download_iridium(event_date, tempfile_path=self.data_path) # download .nc file
                    dataloader.read_iridium(event_date, file_name=iridium_file, basepath=self.data_path, tempfile_path=self.data_path) # creates .h5 file

                if source in ('dmsp_ssies17', 'dmsp_ssies18'):
                    madrigal_kwargs = {'user_fullname': 'First','user_email': 'name@host.com', 'user_affiliation': 'University'}
                    datadownloader.download_dmsp_ssies(event_date, sat=source[-2:], tempfile_path=self.data_path, **madrigal_kwargs)

            except Exception as e:
                print(f"Failed to download {source}:", e)

    def load_data(self, event_date, selected_sources):
        """ Load available datasets for a given date and return them as a dictionary of DataFrames."""
       
        # File paths for all supported datasets
        paths = {'swarm_mag': os.path.join(self.data_path, f'{event_date}_swarmB.h5'),
                'swarm_efield': os.path.join(self.data_path, f'{event_date}_swarmE.h5'),
                'superdarn': os.path.join(self.data_path, f'{event_date}_superdarn_grdmap.h5'),
                'supermag': os.path.join(self.data_path, f'{event_date}_supermag.h5'),
                'iridium_ampere': os.path.join(self.data_path, f'{event_date}_iridium.h5'), 
                'dmsp_ssies17': os.path.join(self.data_path, f'{event_date}_ssies_f17.h5'),
                'dmsp_ssies18': os.path.join(self.data_path, f'{event_date}_ssies_f18.h5'),
                }

        datasets = {}
        required_sources = {''}
        sources_to_load = set(selected_sources) | required_sources

        if not selected_sources:
            print("No sources selected.")

        for key, filepath in paths.items():

            # Skip datasets not selected by the user
            if key not in sources_to_load:
                continue

            # Skip if file does not exist
            if not os.path.exists(filepath):
                print(f"No file found for {key}")
                continue

            try:
                df = pd.read_hdf(filepath)

                # Basic sanity checks
                if df.empty:
                    print(f"⚠️ {key}: dataset is empty")
                else:
                    all_nan_cols = [c for c in df.columns if df[c].isna().all()]
                    if all_nan_cols:
                        print(f"⚠️ {key}: columns with only NaNs: {all_nan_cols}")

                datasets[key] = df

            except Exception as e:
                print(f"Failed to load {key} data: {e}")
                
        return datasets

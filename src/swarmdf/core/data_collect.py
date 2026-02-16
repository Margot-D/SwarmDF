"""
SwarmDF Toolbox — Data collection module

This script handles the retrieval of contextual data around the Swarm satellite 
for use in the assimilation process that reconstructs 2D ionospheric electrodynamics. 
The time and location of interest are user-defined (SwarmDF_GUI).

mention that it downloads data for the whole day. 

"""

# TODO how to deal with user id? does the user have to log into each database? 
# TODO fix documentation

#%%

import pandas as pd
import numpy as np
import os
from lompe.data_tools import dataloader, datadownloader


class DataManager:
    def __init__(self, start_time, data_path, selected_sources):
        
        self.event_date = start_time.strftime("%Y%m%d")
        self.data_path = data_path

        self.fetch_data(selected_sources)
        self.datasets = self.load_data(selected_sources)

    def fetch_data(self, selected_sources):
        """ Download data files for selected sources, if they don't already exist in the user data folder"""

        required_sources = {'swarm'}  # always needed
        sources_to_fetch = set(selected_sources) | required_sources

        print("Fetching data...")

        for source in sources_to_fetch:
            try: 
                if source == 'swarm':
                    datadownloader.download_swarmB(self.event_date, tempfile_path=self.data_path)
                    # print("Swarm trajectory download checked/completed.") #TODO put these message somewhere else (in datadownloader)

                if source == 'swarm_mag':
                    datadownloader.download_swarmB(self.event_date, tempfile_path=self.data_path)
                    # print("Swarm magnetic field download checked/completed.")

                if source == 'swarm_efield':
                    datadownloader.download_swarmE(self.event_date, tempfile_path=self.data_path)
                    # print("Swarm electric field download checked/completed.")

                if source == 'superdarn':
                    datadownloader.download_sdarn(self.event_date, tempfile_path=self.data_path)
                    # print("SuperDARN download checked/completed.")

                if source == 'supermag': #TODO fix userid
                    datadownloader.download_smag(self.event_date, userid='mdecotte', tempfile_path=self.data_path) 
                    # print("SuperMAG download checked/completed.")

                if source == 'iridium_ampere':
                    iridium_file = datadownloader.download_iridium(self.event_date, tempfile_path=self.data_path) # download .nc file
                    dataloader.read_iridium(self.event_date, file_name=iridium_file, basepath=self.data_path, tempfile_path=self.data_path) # creates .h5 file
                    # print("Iridium/AMPERE download checked/completed.")

                if source in ('dmsp_ssies17', 'dmsp_ssies18'): #TODO check that
                    madrigal_kwargs = {'user_fullname': 'First','user_email': 'name@host.com', 'user_affiliation': 'University'}
                    datadownloader.download_dmsp_ssies(self.event_date, sat=source[-2:], tempfile_path=self.data_path, **madrigal_kwargs)
                    # print(f"DMSP/SSIES{source[-2:]} download checked/completed.")

            except Exception as e:
                print(f"Failed to download {source}:", e)


    def load_data(self, selected_sources):
        """ Load available datasets from disk, only those selected by user """

        date_str = str(int(self.event_date))

        paths = {
            'swarm': os.path.join(self.data_path, f'{date_str}_swarmB.h5'),
            'swarm_mag': os.path.join(self.data_path, f'{date_str}_swarmB.h5'),
            'swarm_efield': os.path.join(self.data_path, f'{date_str}_swarmE.h5'),
            'superdarn': os.path.join(self.data_path, f'{date_str}_superdarn_grdmap.h5'),
            'supermag': os.path.join(self.data_path, f'{date_str}_supermag.h5'),
            'iridium_ampere': os.path.join(self.data_path, f'{date_str}_iridium.h5'), 
            'dmsp_ssies17': os.path.join(self.data_path, f'{date_str}_ssies_f17.h5'),
            'dmsp_ssies18': os.path.join(self.data_path, f'{date_str}_ssies_f18_hairston.h5'),
        }

        self.datasets = {}

        required_sources = {'swarm'}
        sources_to_load = set(selected_sources) | required_sources

        if not selected_sources:
            print("No sources selected.")
            pass

        # Load selected datasets:
        print('Loading data...')
        for key, filepath in paths.items():

            if key not in sources_to_load:
                continue  # skip unselected sources

            if not os.path.exists(filepath):
                print(f"No file found for {key}, skipping.")
                continue

            try:
                df = pd.read_hdf(filepath)

                if df.empty:
                    print(f"⚠️  {key}: file loaded but dataset is EMPTY (0 rows)")
                else:
                    all_nan_cols = [c for c in df.columns if df[c].isna().all()]
                    if all_nan_cols:
                        print(
                            f"⚠️  {key}: columns present but contain only NaNs: "
                            f"{all_nan_cols}"
                        )

                    print(f"Loaded {key} data from disk.")

                self.datasets[key] = df

            except Exception as e:
                print(f"Failed to load {key} data: {e}")
                
        return self.datasets

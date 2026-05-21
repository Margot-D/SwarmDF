#TODO add small docu here 

from dataclasses import dataclass
from datetime import datetime

@dataclass
class SwarmDFConfig:
    """
    Central configuration object controlling a full SwarmDF run.

    This includes data selection, grid setup, physics parameters,
    plotting options, and execution flags.
    """

    # Swarm satellite
    sat_id: str

    # time interval
    start_time: datetime
    end_time: datetime
    timestep: float

    # datasets to retrieve
    datasets2download: list

    # analysis grid
    grid_params: dict

    # lompe
    run_lompe_flag: bool
    conductance_method: str
    conductance_params: dict
    regularization_l1: float
    regularization_l2: float

    # lompeOSSE/validation
    run_validation_flag: bool
    time_offset: int #
    snapshot: int

    # python script 
    generate_script_flag: bool

    # demo mode
    demo_flag: bool

    # plotting
    gif_speed: int
    figw: float
    figh: float

    # plot options
    mag_coords_flag: bool
    show_all_data_flag: bool
#TODO add small docu here 

from dataclasses import dataclass
from datetime import datetime

@dataclass
class SwarmDFConfig:

    # satellite
    sat_id: str

    # time interval
    start_time: datetime
    end_time: datetime
    timestep: float

    # datasets
    datasets2download: list

    # conductance
    conductance_method: str
    conductance_params: dict

    # grid
    grid_params: dict

    # lompe
    run_lompe_flag: bool

    # regularization
    l1: float
    l2: float

    # plotting
    gif_speed: int
    figw: float
    figh: float

    # plot options
    mag: bool
    show_data: bool

    # validation
    run_validation_flag: bool
    timeoff: int
    snapshot: int

    # python script 
    generate_script_flag: bool

    # demo mode
    demo_flag: bool
from dataclasses import dataclass
import datetime

@dataclass
class SwarmDFConfig:
    """
    Central configuration object controlling a full SwarmDF run.

    This includes data selection, grid setup, lompe and lompeOSSE parameters,
    vizualization settings, and execution control flags.
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
    time_offset: int
    snapshot: int

    @classmethod
    def default(cls):
        return cls(sat_id='Swarm A',
                   start_time=datetime.datetime(2014, 12, 15, 1, 18),
                   end_time=datetime.datetime(2014, 12, 15, 1, 19),
                   timestep=30.0,
                   datasets2download=['swarm_mag', 'superdarn', 'supermag', 'iridium_ampere', 'dmsp_ssies17', 'dmsp_ssies18'],
                   conductance_method='Zhang & Paxton model',
                   conductance_params={'kp': 4, 'f107': 100.0, 'background': 2.0},
                   grid_params={'L': 2000.0, 'W': 1500.0, 'Lres': 200.0, 'Wres': 200.0, 'wshift': 0.0},
                   run_lompe_flag=True,
                   regularization_l1=1.0,
                   regularization_l2=1.0,
                   run_validation_flag=False,
                   time_offset=0,
                   snapshot=0)

@dataclass
class SwarmDFPlotSettings:
    generate_input_plots: bool
    mag_coords_flag: bool
    show_all_data_flag: bool
    figh: float
    generate_gifs: bool
    gif_speed: int

    @classmethod
    def default(cls):
        return cls(generate_input_plots = True,
                  mag_coords_flag = True,
                  show_all_data_flag = True,
                  figh = 9.0,
                  generate_gifs = False,
                  gif_speed = 550)
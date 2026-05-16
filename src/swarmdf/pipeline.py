#TODO docu
# 

from dataclasses import dataclass
from swarmdf import *

@dataclass
class SwarmDFInput: #TODO how do I know what type everything is?
    grids: list
    analysis_times: list
    data_objects_per_grid: list
    input_PILframes: list

@dataclass
class SwarmDFOutput:
    lompe_models: list | None
    output_PILframes: list | None

@dataclass
class SwarmDFValidation:
    lompeosse_PILframes: list | None
    gamera_PILframes: list | None
    
@dataclass
class SwarmDFResults:
    input: SwarmDFInput
    output: SwarmDFOutput | None
    validation: SwarmDFValidation | None


def run_swarmdf_pipeline(config):  # TODO useful at all? not used in gui.py

    # Collect data
    datasets = get_data(config)
  
    # Input to Lompe
    input_results = compute_swarmdf_input(config, datasets)

    output_results = None
    validation_results = None

    # Lompe output
    if config.run_lompe_flag:
        output_results = compute_swarmdf_output(config, input_results)

    # LompeOSSE validation
    if config.run_validation_flag and output_results is not None:
        validation_results = compute_swarmdf_validation(config, output_results)

    return SwarmDFResults(input=input_results, output=output_results, validation=validation_results)


def get_data(config):

    datahandler = DataManager(config.start_time, config.end_time, config.datasets2download, config.demo_flag)
    datasets = datahandler.datasets
    
    return datasets


def compute_swarmdf_input(config, datasets):

    lompe_input = LompeInput(config.sat_id, config.start_time, config.end_time, datasets, config.mag)
    grids, analysis_times = lompe_input.build_grids_around_swarm(config.timestep, config.grid_params)
    data_objects_per_grid = lompe_input.prepare_lompe_input(grids, analysis_times)
    input_PILframes = lompe_input.plot_lompe_input(grids, analysis_times, data_objects_per_grid, config.figh, config.figw, config.gif_speed, config.show_data)

    return SwarmDFInput(grids, analysis_times, data_objects_per_grid, input_PILframes)


def compute_swarmdf_output(config, input_data: SwarmDFInput):

    SHs, SPs = compute_conductances(config.conductance_method, config.conductance_params, input_data.analysis_times, input_data.grids)
    lompe_models = run_lompe(input_data.analysis_times, input_data.grids, input_data.data_objects_per_grid, SHs, SPs, config.l1, config.l2)
    output_PILframes = plot_lompe_output(lompe_models, config.sat_id, config.figh, config.gif_speed)

    return SwarmDFOutput(lompe_models, output_PILframes)


def compute_swarmdf_validation(config, lompe_results : SwarmDFOutput):

    lompe_models = lompe_results.lompe_models
    lompeosse_models, gamera_output = run_lompeOSSE(lompe_models, config.timeoff, config.snapshot)
    lompeosse_PILframes, gamera_PILframes = plot_lompeOSSE_output(lompeosse_models, gamera_output, config.figh, config.gif_speed)
        
    return SwarmDFValidation(lompeosse_PILframes, gamera_PILframes)
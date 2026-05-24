from dataclasses import dataclass, replace
from swarmdf import *

@dataclass
class SwarmDFInput:
    grids: list
    analysis_times: list
    data_objects_per_grid: list

@dataclass
class SwarmDFOutput:
    lompe_models: list

@dataclass
class SwarmDFValidation:
    lompeosse_PILframes: list
    gamera_PILframes: list
    
@dataclass
class SwarmDFPlots:
    input_frames: list | None = None
    output_frames: list | None = None
    validation_frames: list | None = None

@dataclass
class SwarmDFResults:
    input: SwarmDFInput
    output: SwarmDFOutput | None
    validation: SwarmDFValidation | None
    plots: SwarmDFPlots


def run_swarmdf_pipeline(config):

    # Collect data
    datasets = get_data(config)
  
    # Input to Lompe
    input_results = compute_swarmdf_input(config, datasets)
    input_frames = render_swarmdf_input(config, datasets, input_results)

    plots = SwarmDFPlots(input_frames=input_frames)

    output_results = None
    validation_results = None

    # Lompe output
    if config.run_lompe_flag:
        output_results = compute_swarmdf_output(config, input_results)
        output_frames = render_swarmdf_output(config, output_results)
        plots = replace(plots, output_frames=output_frames)

    # LompeOSSE validation
    if config.run_validation_flag and output_results is not None:
        validation_results = compute_swarmdf_validation(config, output_results)
        validation_frames = render_swarmdf_validation(validation_results)
        plots = replace(plots, validation_frames=validation_frames)

    return SwarmDFResults(input=input_results, output=output_results, validation=validation_results, plots=plots)


def get_data(config):

    datahandler = DataManager(config.start_time, config.end_time, config.datasets2download, config.demo_flag)
    datasets = datahandler.datasets
    
    return datasets

def compute_swarmdf_input(config, datasets):

    lompe_ctx = LompeInput(config.sat_id, config.start_time, config.end_time, datasets, config.mag_coords_flag)
    grids, analysis_times = lompe_ctx.build_grids_around_swarm(config.timestep, config.grid_params)
    data_objects_per_grid = lompe_ctx.prepare_lompe_input(grids, analysis_times)

    return SwarmDFInput(grids, analysis_times, data_objects_per_grid)

def render_swarmdf_input(config, datasets, swarmdf_input: SwarmDFInput):
    
    lompe_ctx = LompeInput(config.sat_id, config.start_time, config.end_time, datasets, config.mag_coords_flag)
    input_pil_frames = lompe_ctx.plot_lompe_input(swarmdf_input.grids, swarmdf_input.analysis_times, swarmdf_input.data_objects_per_grid, config.figh, config.figw, config.gif_speed, config.show_all_data_flag)
    
    return input_pil_frames

def compute_swarmdf_output(config, swarmdf_input: SwarmDFInput):

    SHs, SPs = compute_conductances(config.conductance_method, config.conductance_params, swarmdf_input.analysis_times, swarmdf_input.grids)
    lompe_models = run_lompe(swarmdf_input.analysis_times, swarmdf_input.grids, swarmdf_input.data_objects_per_grid, SHs, SPs, config.regularization_l1, config.regularization_l2)

    return SwarmDFOutput(lompe_models)

def render_swarmdf_output(config, swarmdf_output: SwarmDFOutput):
    
    output_pil_frames = plot_lompe_output(swarmdf_output.lompe_models, config.sat_id, config.figh, config.gif_speed)
    
    return output_pil_frames

def compute_swarmdf_validation(config, swarmdf_output : SwarmDFOutput):

    lompeosse_models, gamera_output = run_lompeOSSE(swarmdf_output.lompe_models, config.time_offset, config.snapshot)
        
    return SwarmDFValidation(lompeosse_models, gamera_output)

def render_swarmdf_validation(config, swarmdf_validation: SwarmDFValidation):
    
    lompeosse_PILframes, gamera_PILframes = plot_lompeOSSE_output(swarmdf_validation.lompeosse_PILframes, swarmdf_validation.gamera_PILframes, config.figh, config.gif_speed)
    
    return lompeosse_PILframes, gamera_PILframes
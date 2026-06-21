from dataclasses import dataclass, replace
from swarmdf import *

@dataclass
class SwarmDFInput:
    raw_data: list
    swarm_passes: list
    grids: list
    analysis_times: list
    data_objects_per_grid: list

@dataclass
class SwarmDFOutput:
    lompe_models: list
    sat_id: str

@dataclass
class SwarmDFValidation:
    lompeosse_models: list
    gamera_output: list
    
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


def run_swarmdf_pipeline(config, plot_settings, use_sample_data=False):

    # Collect data
    datasets = get_data(config, use_sample_data)

    plots = SwarmDFPlots()

    # Input to Lompe
    input_results = compute_swarmdf_input(datasets, config)
    if plot_settings.generate_input_plots:
        plots.input_frames = render_swarmdf_input(input_results, plot_settings)

    output_results = None
    # Lompe output
    if config.run_lompe_flag:
        output_results = compute_swarmdf_output(input_results, config) 
        plots.output_frames = render_swarmdf_output(output_results, plot_settings)

    validation_results = None
    # LompeOSSE validation
    if config.run_validation_flag and output_results is not None: 
        validation_results = compute_swarmdf_validation(output_results, config)
        plots.validation_frames = render_swarmdf_validation(validation_results, plot_settings)

    return SwarmDFResults(input=input_results, output=output_results, validation=validation_results, plots=plots)


def get_data(config, use_sample_data):

    datahandler = DataManager(config.start_time, config.end_time, config.datasets2download, use_sample_data)
    datasets = datahandler.datasets
    
    return datasets

def compute_swarmdf_input(datasets, config):

    input_builder = LompeInputBuilder(config.sat_id, config.start_time, config.end_time, config.timestep, datasets)
    swarm_passes, grids, analysis_times = input_builder.build_grids_around_swarm(config.grid_params)
    data_objects_per_grid = input_builder.prepare_lompe_input(grids, analysis_times)

    return SwarmDFInput(datasets, swarm_passes, grids, analysis_times, data_objects_per_grid)

def render_swarmdf_input(swarmdf_input: SwarmDFInput, plot_settings):
    
    input_plotter = LompeInputPlotter()
    input_pngs = input_plotter.plot_lompe_input(swarmdf_input.swarm_passes, swarmdf_input.grids, swarmdf_input.analysis_times, swarmdf_input.data_objects_per_grid, swarmdf_input.raw_data, plot_settings)
    
    return input_pngs

def compute_swarmdf_output(swarmdf_input: SwarmDFInput, config):

    SHs, SPs = compute_conductances(config.conductance_method, config.conductance_params, swarmdf_input.analysis_times, swarmdf_input.grids)
    lompe_models = run_lompe(swarmdf_input.grids, swarmdf_input.analysis_times, swarmdf_input.data_objects_per_grid, SHs, SPs, config.regularization_l1, config.regularization_l2)

    return SwarmDFOutput(lompe_models, config.sat_id)

def render_swarmdf_output(swarmdf_output: SwarmDFOutput, plot_settings):

    output_pngs = plot_lompe_output(swarmdf_output.lompe_models, swarmdf_output.sat_id, plot_settings)
    
    return output_pngs

def compute_swarmdf_validation(swarmdf_output : SwarmDFOutput, config):

    lompeosse_models, gamera_output = run_lompeOSSE(swarmdf_output.lompe_models, config.time_offset, config.snapshot)
        
    return SwarmDFValidation(lompeosse_models, gamera_output)

def render_swarmdf_validation(swarmdf_validation: SwarmDFValidation, plot_settings):
    
    lompeosse_pngs, gamera_pngs = plot_lompeOSSE_output(swarmdf_validation.lompeosse_models, swarmdf_validation.gamera_output, plot_settings)
    
    return lompeosse_pngs, gamera_pngs
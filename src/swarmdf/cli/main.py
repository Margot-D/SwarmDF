"""
SwarmDF command-line entry point.

Run the full SwarmDF pipeline from a terminal or script without
launching the graphical interface.

A SwarmDFConfig object is required. The pipeline can be executed 
using either:
- a YAML configuration file (see `examples/config.yaml`): 
    python run_swarmdf.py --config config.yaml
- demo mode:
    python run_swarmdf.py --demo

Returns
-------
SwarmDFResults
    Container holding input data products, Lompe inversion results, optional
    validation results, and generated visualization frames (PIL images and GIFs).
"""

from swarmdf.config import SwarmDFConfig, SwarmDFPlotSettings
from swarmdf.pipeline import run_swarmdf_pipeline
import yaml
import argparse
import datetime

import cloudpickle as pickle

def save_results(results, path):
    with open(path, "wb") as f:
        pickle.dump(results, f)

def load_config(path):
    """
    Load a YAML configuration file into a SwarmDFConfig object.
    User-defined parameters override the default configuration,
    while unspecified parameters retain their default values.
    """

    with open(path, "r") as f:
        user_cfg = yaml.safe_load(f)

    # default configuration
    config = SwarmDFConfig.default()

    for key, value in user_cfg.items():

        # Datetime conversion
        if key in ["start_time", "end_time"]:
            value = datetime.datetime.fromisoformat(value)

        if not hasattr(config, key):
            raise ValueError(f"Unknown configuration parameter: {key}")

        current = getattr(config, key)

        # Override default values with user-provided values
        if isinstance(current, dict) and isinstance(value, dict): # Merge nested dicts (conductance and grid params)
            current.update(value)
        else:
            setattr(config, key, value)

    return config 

def load_plot_settings(path):
    """
    Load a YAML configuration file into a SwarmDFPlotSettings object.
    User-defined parameters override the default configuration,
    while unspecified parameters retain their default values.
    """
   
    with open(path, "r") as f:
        user_cfg = yaml.safe_load(f)

    # default plot settings
    settings = SwarmDFPlotSettings.default()

    # Override default values with user-provided values
    for key, value in user_cfg.items():
        setattr(settings, key, value)

    return settings

def main():
    parser = argparse.ArgumentParser()

    execution_group = parser.add_argument_group("Execution options")

    group = execution_group.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=str, metavar="config.yaml", default=None, help="Path to analysis configuration YAML file")
    group.add_argument("--demo", action="store_true", help="Run demo (uses sample datasets and demo configuration settings)")

    output_group = parser.add_argument_group("Output options")

    output_group.add_argument("--plot-config", type=str, metavar="plot_settings.yaml", default=None, help="Optional: path to plot settings YAML file")
    output_group.add_argument("--no-input-plots", action="store_true", help="Disable input plot generation (faster execution).")
    output_group.add_argument("--gifs", action="store_true", help="Enable GIFs")

    args = parser.parse_args()

    if args.demo:
        config = SwarmDFConfig.default()
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("You must provide --config or --demo")

    if args.plot_config:
        plot_settings = load_plot_settings(args.plot_config)
    else:
        plot_settings = SwarmDFPlotSettings()

    if args.no_input_plots:
        plot_settings.generate_input_plots = False
    if args.gifs:
        plot_settings.generate_gifs = True

    run_swarmdf_pipeline(config=config, plot_settings=plot_settings, use_sample_data=args.demo)
    # save_results(results, "swarmdf_results.pkl")


if __name__ == "__main__":
    main()
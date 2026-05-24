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

from swarmdf.config import SwarmDFConfig
from swarmdf.pipeline import run_swarmdf_pipeline
import yaml
import argparse
import datetime

def load_config(path):
    """
    Load a YAML configuration file into a SwarmDFConfig object.
    Missing parameters are filled using SwarmDFConfig.default().
    """

    with open(path, "r") as f:
        user_cfg = yaml.safe_load(f)

    config = SwarmDFConfig.default()

    for key, value in user_cfg.items():

        # Datetime conversion
        if key in ["start_time", "end_time"]:
            value = datetime.datetime.fromisoformat(value)

        current = getattr(config, key)

        # Merge nested dicts (conductance/grid params)
        if isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
        else:
            setattr(config, key, value)

    return config


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--config", type=str, default=None)
    group.add_argument("--demo", action="store_true")

    args = parser.parse_args()

    if args.config is not None:
        config = load_config(args.config)
    elif args.demo:
        config = SwarmDFConfig.demo()
    else:
        raise ValueError("You must provide --config or --demo")

    run_swarmdf_pipeline(config)


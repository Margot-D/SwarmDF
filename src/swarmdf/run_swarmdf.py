"""
SwarmDF command-line entrypoint (allows SwarmDF to be executed from a terminal or scripts
without launching the graphical interface).

Runs the full SwarmDF pipeline outside the GUI.

Configuration TODO NO
-------------
A fully defined SwarmDFConfig object is required.

It can be created in one of two ways:
- manually in Python:
    config = SwarmDFConfig(...)
- using a YAML file (see config.yaml for an example)

Alternatively, a built-in demonstration configuration can be used:
    config = SwarmDFConfig.demo()

Command-line usage
------------------

Run with a YAML configuration:
    python run_swarmdf.py --config config.yaml

Or run demo mode:
    python run_swarmdf.py --demo

Outputs
-------
SwarmDFResults
    Structured container holding:
    - input data products
    - Lompe inversion results
    - optional LompeOSSE validation results
    - generated visualization frames (PIL images / GIFs)
"""

from swarmdf.config import SwarmDFConfig
from swarmdf.pipeline import run_swarmdf_pipeline
import yaml
import argparse
import datetime

def load_config(path):
    "" ""

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


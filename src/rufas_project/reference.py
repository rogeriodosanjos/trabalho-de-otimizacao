import json
from pathlib import Path

from .models import SimulationConfig, simulation_config_from_dict


def load_reference_scenario(path: str | Path = "/workspace/configs/reference_scenario.json") -> SimulationConfig:
    with Path(path).open(encoding="utf-8") as stream:
        data = json.load(stream)
    return simulation_config_from_dict(data)


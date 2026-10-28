import json
from pathlib import Path

import pytest

from rufas_project.models import simulation_config_from_dict
from rufas_project.validation import ConfigurationError, validate_simulation_config


ROOT = Path(__file__).parents[1]


def reference_config():
    data = json.loads((ROOT / "configs/reference_scenario.json").read_text())
    return simulation_config_from_dict(data)


def test_reference_scenario_is_valid():
    validate_simulation_config(reference_config())


def test_parity_fractions_must_sum_to_one():
    config = reference_config()
    config.herd.parity_fractions.parity_1 = 0.90
    with pytest.raises(ConfigurationError, match="paridade"):
        validate_simulation_config(config)

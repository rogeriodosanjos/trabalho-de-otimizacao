import json
from pathlib import Path

from rufas_project.inputs import prepare_run_inputs
from rufas_project.models import simulation_config_from_dict


ROOT = Path(__file__).parents[1]


def test_prepare_inputs_from_official_examples(tmp_path):
    data = json.loads((ROOT / "configs/reference_scenario.json").read_text())
    config = simulation_config_from_dict(data)
    manager = prepare_run_inputs(tmp_path, ROOT / "RuFaS", config)

    animal = json.loads((tmp_path / "input/animal.json").read_text())
    feed = json.loads((tmp_path / "input/feed.json").read_text())
    prices = json.loads((tmp_path / "feed_prices.json").read_text())

    assert manager.exists()
    assert animal["herd_information"]["cow_num"] == 20
    assert animal["ration"]["user_input"] is True
    lactating = next(
        ration for ration in feed["rations"] if ration["animal_combination"] == "lac_cow"
    )
    assert sum(item["ration_percentage"] for item in lactating["feeds"]) == 100
    assert prices["44"] == 0.5

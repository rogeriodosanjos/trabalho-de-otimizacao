import json
import math
from pathlib import Path
from typing import Any

from .models import SimulationConfig
from .validation import ConfigurationError, validate_simulation_config


FILTER_CONTENT = """.*(num_lactating_cows|num_dry_cows|num_cows_total)$
.*(daily_milk_production|milking_cow_num|dry_cow_num|avg_days_in_milk)$
.*ration_daily_feed_totals_for_pen_3_LAC_COW$
"""


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _patch_feed(reference: dict[str, Any], config: SimulationConfig) -> dict[str, Any]:
    feed_by_id = {int(item["feed_type"]): item for item in reference["feeds"]}
    if config.diet.ingredients:
        requested_ids = {item.feed_type for item in config.diet.ingredients}
        unknown = requested_ids - set(feed_by_id)
        if unknown:
            raise ConfigurationError(
                f"A dieta contém feed_type ausente no exemplo oficial: {sorted(unknown)}"
            )
        for ingredient in config.diet.ingredients:
            feed_by_id[ingredient.feed_type]["purchased_feed_cost"] = (
                ingredient.purchased_feed_cost_usd_per_kg_dm
            )
        lactating = next(
            ration for ration in reference["rations"] if ration["animal_combination"] == "lac_cow"
        )
        lactating["feeds"] = [
            {
                "feed_type": ingredient.feed_type,
                "ration_percentage": ingredient.ration_percentage,
            }
            for ingredient in config.diet.ingredients
            if ingredient.ration_percentage > 0
        ]
    return reference


def prepare_run_inputs(run_dir: Path, rufas_root: Path, config: SimulationConfig) -> Path:
    """Prepara entradas isoladas e retorna o metadata usado por ``main.py``."""
    validate_simulation_config(config)
    input_dir = run_dir / "input"
    output_dir = run_dir / "output"
    filters_dir = run_dir / "filters"
    for directory in [input_dir, output_dir, filters_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    general = read_json(rufas_root / "input/data/config/example_animals_only_config.json")
    general.update(
        {
            "start_date": "2013:1",
            "end_date": f"2013:{config.simulation_days}",
            "set_seed": True,
            "simulation_type": "animals_only",
            "nutrient_standard": "NASEM",
            "include_detailed_values": False,
        }
    )
    general_path = input_dir / "config.json"
    write_json(general_path, general)

    animal = read_json(rufas_root / "input/data/animal/example_freestall_animal.json")
    herd = animal["herd_information"]
    herd.update(
        {
            "cow_num": config.herd.cow_num,
            "herd_num": config.herd.cow_num,
            "herd_size_sell_threshold": config.herd.cow_num + 1,
            "herd_size_buy_threshold": max(0, config.herd.cow_num - 1),
            "breed": config.herd.breed,
            "parity_fractions": config.herd.parity_fractions.as_rufas_dict(),
            "milking_cow_fraction": config.herd.milking_cow_fraction,
            "annual_milk_yield": None,
        }
    )
    animal["animal_config"]["management_decisions"].update(
        {
            "milk_fat_percent": config.milk.fat_percent,
            "milk_protein_percent": config.milk.protein_percent,
        }
    )
    animal["animal_config"]["farm_level"]["bodyweight"]["mature_body_weight_avg"] = (
        config.milk.mature_body_weight_kg
    )
    animal["ration"]["user_input"] = config.diet.mode == "fixed"
    animal["ration"]["formulation_interval"] = config.diet.formulation_interval_days

    for pen in animal["pen_information"]:
        density = float(pen.get("max_stocking_density", 1.0))
        if pen["animal_combination"] == "LAC_COW":
            needed = math.ceil(config.herd.cow_num * config.herd.milking_cow_fraction / density)
            pen["number_of_stalls"] = max(int(pen["number_of_stalls"]), needed)
        elif pen["animal_combination"] == "CLOSE_UP":
            dry = config.herd.cow_num * (1 - config.herd.milking_cow_fraction)
            needed = math.ceil((dry + herd["heiferIII_num_springers"]) / density)
            pen["number_of_stalls"] = max(int(pen["number_of_stalls"]), needed)

    animal_path = input_dir / "animal.json"
    write_json(animal_path, animal)

    feed = _patch_feed(
        read_json(rufas_root / "input/data/feed/example_Midwest_feed.json"), config
    )
    feed_path = input_dir / "feed.json"
    write_json(feed_path, feed)
    write_json(
        run_dir / "feed_prices.json",
        {
            str(item["feed_type"]): float(item["purchased_feed_cost"])
            for item in feed["feeds"]
        },
    )

    scenario = read_json(rufas_root / "input/metadata/example_animals_only_metadata.json")
    scenario["files"]["config"]["path"] = str(general_path)
    scenario["files"]["animal"]["path"] = str(animal_path)
    scenario["files"]["feed"]["path"] = str(feed_path)
    scenario_path = input_dir / "scenario_metadata.json"
    write_json(scenario_path, scenario)

    (filters_dir / "csv_notebook_lactation.txt").write_text(FILTER_CONTENT, encoding="utf-8")
    task = {
        "parallel_workers": 1,
        "tasks": [
            {
                "task_type": "SIMULATION_SINGLE_RUN",
                "metadata_file_path": str(scenario_path),
                "output_prefix": config.name,
                "log_verbosity": "warnings",
                "random_seeds": [config.random_seed],
                "exclude_info_maps": False,
                "filters_directory": str(filters_dir),
                "csv_output_directory": str(output_dir / "csv"),
                "json_output_directory": str(output_dir / "json"),
                "graphics_directory": str(output_dir / "graphics"),
                "report_directory": str(output_dir / "reports"),
                "logs_directory": str(output_dir / "logs"),
                "cross_validation_file_paths": [
                    "input/metadata/cross_validation/animal_cross_validation.json",
                    "input/metadata/cross_validation/weather_cross_validation.json",
                ],
            }
        ],
    }
    task_path = input_dir / "task.json"
    write_json(task_path, task)
    manager = {
        "files": {
            "tasks": {
                "title": "Notebook task manager data",
                "description": "Tarefa isolada criada pelos módulos do projeto.",
                "path": str(task_path),
                "type": "json",
                "properties": "tasks_properties",
            }
        }
    }
    manager_path = input_dir / "task_manager_metadata.json"
    write_json(manager_path, manager)
    write_json(run_dir / "resolved_config.json", config.to_dict())
    return manager_path


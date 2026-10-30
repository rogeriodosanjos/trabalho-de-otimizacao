import json

import pandas as pd

from rufas_project.results import parse_rufas_results


def test_parse_initial_population_generated_by_seed(tmp_path):
    output_dir = tmp_path / "output/csv"
    output_dir.mkdir(parents=True)
    frame = pd.DataFrame(
        {
            "initial_breed": ["{'Holstein'}", None],
            "initial_number_of_cows": [20, None],
            "initial_number_of_lactating_cows": [16, None],
            "initial_number_of_dry_cows": [4, None],
            "initial_average_cow_body_weight": [651.25, None],
            "initial_average_cow_days_in_milk": [118.5, None],
            "initial_average_cow_parity": [2.1, None],
            "initial_number_of_parity_1_cows": [8, None],
            "initial_number_of_parity_2_cows": [5, None],
            "initial_number_of_parity_3_cows": [4, None],
            "initial_number_of_parity_4_cows": [2, None],
            "initial_number_of_parity_5_cows": [1, None],
            "initial_number_of_parity_6_or_more_cows": [0, None],
            "num_lactating_cows": [16, 17],
            "num_dry_cows": [4, 4],
            "num_cows_total": [20, 21],
            "daily_milk_production": [500, 530],
            "avg_days_in_milk": [118.5, 119.5],
        }
    )
    frame.to_csv(output_dir / "result.csv", index=False)
    (tmp_path / "resolved_config.json").write_text(json.dumps({"random_seed": 42}))

    result = parse_rufas_results(tmp_path)

    population = result["initial_population"]
    assert population["random_seed"] == 42
    assert population["breed"] == "Holstein"
    assert population["number_of_cows"] == 20
    assert population["average_cow_body_weight_kg"] == 651.25
    assert population["parity_distribution"] == {
        "1": 8,
        "2": 5,
        "3": 4,
        "4": 2,
        "5": 1,
        "6_or_more": 0,
    }

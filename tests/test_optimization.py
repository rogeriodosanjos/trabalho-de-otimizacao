from rufas_project.models import DietConfig, DietIngredient, SimulationConfig
from rufas_project.optimization import (
    build_min_cost_scenario,
    describe_min_cost_problem,
    summarize_lactating_ration,
)


def scenario():
    config = SimulationConfig()
    config.diet = DietConfig(
        mode="fixed",
        ingredients=[DietIngredient(44, 40, 0.50, "Milho"), DietIngredient(50, 60, 0.10, "Silagem")],
    )
    return config


def test_build_min_cost_scenario_does_not_change_reference():
    reference = scenario()
    optimized = build_min_cost_scenario(reference)
    assert reference.diet.mode == "fixed"
    assert optimized.diet.mode == "rufas_min_cost"
    assert "Σ pᵢ × xᵢ" in describe_min_cost_problem(optimized).iloc[1]["Definição"]


def test_summarize_ration_converts_pen_totals_to_per_cow_values():
    result = {
        "feed_costs_usd_per_kg_dm": {"44": 0.50, "50": 0.10},
        "series": [
            {
                "lactating_cows": 10,
                "lactating_feed_kg_dm": {"44": 40, "50": 60},
            }
        ],
    }
    frame, totals = summarize_lactating_ration(result, scenario())
    assert totals["average_kg_dm_per_cow_day"] == 10
    assert totals["average_cost_usd_per_cow_day"] == 2.6
    assert frame["percentage_dm"].sum() == 100

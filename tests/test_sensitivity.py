from rufas_project.models import DietConfig, DietIngredient, SimulationConfig
from rufas_project.sensitivity import (
    build_composition_matrix,
    generate_price_sensitivity_cases,
    summarize_price_sensitivity,
)


def scenario():
    config = SimulationConfig()
    config.diet = DietConfig(
        mode="fixed",
        ingredients=[
            DietIngredient(44, 40, 0.50, "Milho"),
            DietIngredient(50, 60, 0.10, "Silagem"),
        ],
    )
    return config


def fake_result(cost_44=0.50, cost_50=0.10):
    return {
        "feed_costs_usd_per_kg_dm": {"44": cost_44, "50": cost_50},
        "metrics": {"total_milk_kg": 100},
        "series": [
            {
                "day": 1,
                "lactating_cows": 10,
                "milk_kg": 100,
                "lactating_feed_kg_dm": {"44": 40, "50": 60},
            }
        ],
    }


def test_generate_cases_varies_one_price_without_mutating_reference():
    reference = scenario()
    cases = generate_price_sensitivity_cases(reference)
    assert len(cases) == 5
    assert cases[0].key == "baseline"
    assert reference.diet.mode == "fixed"
    assert reference.diet.ingredients[0].purchased_feed_cost_usd_per_kg_dm == 0.50
    changed = cases[1].config.diet.ingredients[0].purchased_feed_cost_usd_per_kg_dm
    assert changed == 0.40


def test_sensitivity_summary_uses_baseline_for_percentage_changes():
    cases = generate_price_sensitivity_cases(scenario(), multipliers=(0.8,))
    results = {case.key: fake_result() for case in cases}
    summary = summarize_price_sensitivity(cases, results)
    assert summary.loc[summary["key"] == "baseline", "margin_usd_change_pct"].iloc[0] == 0
    assert len(summary) == 3
    composition = build_composition_matrix(cases, results)
    assert composition.index[0] == "baseline"
    assert composition.loc["baseline", "44"] == 40

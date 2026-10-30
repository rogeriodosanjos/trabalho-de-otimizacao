from pathlib import Path

from rufas_project.models import DietConfig, DietIngredient, SimulationConfig
from rufas_project.prices import apply_price_snapshot, describe_price_snapshot, load_price_snapshot


ROOT = Path(__file__).resolve().parents[1]


def test_market_price_snapshot_is_applied_without_mutating_reference():
    snapshot = load_price_snapshot(ROOT / "configs/market_price_snapshot.json")
    reference = SimulationConfig()
    reference.diet = DietConfig(
        ingredients=[
            DietIngredient(23, 50.0, 0.10, "Blood meal"),
            DietIngredient(44, 50.0, 0.50, "Corn grain"),
        ]
    )
    priced = apply_price_snapshot(reference, snapshot)

    assert reference.diet.ingredients[0].purchased_feed_cost_usd_per_kg_dm == 0.10
    assert priced.diet.ingredients[0].purchased_feed_cost_usd_per_kg_dm == 1.814156
    assert priced.diet.ingredients[1].purchased_feed_cost_usd_per_kg_dm == 0.27297661
    assert priced.economics.milk_price_unit == "per_kg"
    assert abs(priced.economics.milk_price - 0.43431066) < 1e-9
    assert snapshot["exchange_rate"]["brl_per_usd"] == 5.3744
    assert snapshot["selection_rule"].startswith("Ponto médio")
    assert len(describe_price_snapshot(snapshot)) == 7

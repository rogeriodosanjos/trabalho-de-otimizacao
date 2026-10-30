import pytest

from rufas_project.economics import calculate_economics
from rufas_project.models import SimulationConfig


def test_economics_uses_resolved_feed_prices():
    config = SimulationConfig()
    config.economics.milk_price = 0.5
    result = {
        "feed_costs_usd_per_kg_dm": {"44": 0.25},
        "series": [
            {"day": 1, "milk_kg": 100, "lactating_feed_kg_dm": {"44": 20}}
        ],
    }
    economics = calculate_economics(result, config)

    assert economics["total_milk_revenue"] == 50
    assert economics["total_lactating_feed_cost"] == 5
    assert economics["margin_over_lactating_feed_cost"] == 45


def test_economics_converts_price_per_liter_to_price_per_kg():
    config = SimulationConfig()
    config.economics.milk_price = 2.50
    config.economics.milk_price_unit = "per_liter"
    config.economics.milk_density_kg_per_liter = 1.03
    result = {
        "feed_costs_usd_per_kg_dm": {},
        "series": [
            {"day": 1, "milk_kg": 103, "lactating_feed_kg_dm": {}}
        ],
    }

    economics = calculate_economics(result, config)

    assert economics["milk_price_input"] == 2.50
    assert economics["milk_price_input_unit"] == "per_liter"
    assert economics["milk_price_per_kg"] == pytest.approx(2.50 / 1.03)
    assert economics["total_milk_liters_equivalent"] == pytest.approx(100)
    assert economics["total_milk_revenue"] == pytest.approx(250)

from rufas_project.economics import calculate_economics
from rufas_project.models import SimulationConfig


def test_economics_uses_resolved_feed_prices():
    config = SimulationConfig()
    config.economics.milk_price_usd_per_kg = 0.5
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

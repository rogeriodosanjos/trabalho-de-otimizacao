from typing import Any

from .models import SimulationConfig


def calculate_economics(result: dict[str, Any], config: SimulationConfig) -> dict[str, Any]:
    """Calcula receita e margem sobre alimentação fora do RuFaS."""
    cost_by_feed = {
        str(feed_id): float(cost)
        for feed_id, cost in result.get("feed_costs_usd_per_kg_dm", {}).items()
    }
    cost_by_feed.update({
        str(item.feed_type): item.purchased_feed_cost_usd_per_kg_dm
        for item in config.diet.ingredients
    })
    daily = []
    for row in result["series"]:
        feed_cost = sum(
            float(amount) * cost_by_feed.get(str(feed_id), 0.0)
            for feed_id, amount in row.get("lactating_feed_kg_dm", {}).items()
        )
        milk_revenue = float(row.get("milk_kg") or 0) * config.economics.milk_price_usd_per_kg
        daily.append(
            {
                "day": row["day"],
                "milk_revenue": milk_revenue,
                "lactating_feed_cost": feed_cost,
                "margin_over_lactating_feed_cost": milk_revenue - feed_cost,
            }
        )
    total_revenue = sum(row["milk_revenue"] for row in daily)
    total_feed_cost = sum(row["lactating_feed_cost"] for row in daily)
    return {
        "source": "Calculado pelo projeto, não pelo RuFaS",
        "currency": config.economics.currency,
        "milk_price_per_kg": config.economics.milk_price_usd_per_kg,
        "milk_price_source": config.economics.milk_price_source,
        "total_milk_revenue": total_revenue,
        "total_lactating_feed_cost": total_feed_cost,
        "margin_over_lactating_feed_cost": total_revenue - total_feed_cost,
        "daily": daily,
    }


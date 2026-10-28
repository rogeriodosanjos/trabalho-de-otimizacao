from typing import Any

import pandas as pd


def compare_scenarios(
    scenarios: dict[str, tuple[dict[str, Any], dict[str, Any]]],
) -> pd.DataFrame:
    rows = []
    for name, (result, economics) in scenarios.items():
        rows.append(
            {
                "scenario": name,
                "milk_kg": result["metrics"]["total_milk_kg"],
                "average_daily_milk_kg": result["metrics"]["average_daily_milk_kg"],
                "feed_cost": economics["total_lactating_feed_cost"],
                "milk_revenue": economics["total_milk_revenue"],
                "margin_over_feed_cost": economics["margin_over_lactating_feed_cost"],
            }
        )
    return pd.DataFrame(rows).set_index("scenario")


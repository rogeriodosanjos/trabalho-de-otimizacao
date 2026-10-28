from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

from .economics import calculate_economics
from .models import SimulationConfig
from .optimization import build_min_cost_scenario, summarize_lactating_ration


@dataclass
class SensitivityCase:
    key: str
    label: str
    config: SimulationConfig
    varied_feed_type: int | None
    multiplier: float
    base_price: float | None
    varied_price: float | None


def generate_price_sensitivity_cases(
    reference: SimulationConfig,
    multipliers: Iterable[float] = (0.8, 1.2),
) -> list[SensitivityCase]:
    """Gera cenário-base e variações OAT dos preços dos ingredientes."""
    multiplier_values = tuple(float(value) for value in multipliers)
    if not multiplier_values or any(value <= 0 or value == 1 for value in multiplier_values):
        raise ValueError("os multiplicadores devem ser positivos, diferentes de 1 e não vazios")

    baseline = build_min_cost_scenario(reference, name="fase3_base_otimizada")
    cases = [
        SensitivityCase(
            key="baseline",
            label="Cenário-base",
            config=baseline,
            varied_feed_type=None,
            multiplier=1.0,
            base_price=None,
            varied_price=None,
        )
    ]
    for ingredient in reference.diet.ingredients:
        for multiplier in multiplier_values:
            percentage = round((multiplier - 1) * 100)
            direction = "mais" if percentage > 0 else "menos"
            key = f"feed_{ingredient.feed_type}_{int(round(multiplier * 100))}"
            config = build_min_cost_scenario(reference, name=f"fase3_{key}")
            varied = next(item for item in config.diet.ingredients if item.feed_type == ingredient.feed_type)
            varied.purchased_feed_cost_usd_per_kg_dm *= multiplier
            cases.append(
                SensitivityCase(
                    key=key,
                    label=f"Ingrediente {ingredient.feed_type}: {abs(percentage)}% {direction}",
                    config=config,
                    varied_feed_type=ingredient.feed_type,
                    multiplier=multiplier,
                    base_price=ingredient.purchased_feed_cost_usd_per_kg_dm,
                    varied_price=varied.purchased_feed_cost_usd_per_kg_dm,
                )
            )
    return cases


def summarize_price_sensitivity(
    cases: list[SensitivityCase],
    results: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Consolida resultados produtivos, econômicos e de inclusão para cada caso."""
    rows = []
    for case in cases:
        if case.key not in results:
            raise KeyError(f"resultado ausente para o caso {case.key}")
        result = results[case.key]
        economics = calculate_economics(result, case.config)
        ration, totals = summarize_lactating_ration(result, case.config)
        inclusion = 0.0
        if case.varied_feed_type is not None:
            matched = ration.loc[ration["feed_type"] == case.varied_feed_type, "percentage_dm"]
            inclusion = float(matched.iloc[0]) if not matched.empty else 0.0
        rows.append(
            {
                "key": case.key,
                "label": case.label,
                "varied_feed_type": case.varied_feed_type,
                "multiplier": case.multiplier,
                "base_price": case.base_price,
                "varied_price": case.varied_price,
                "varied_feed_inclusion_pct": inclusion,
                "average_dmi_kg_per_cow_day": totals["average_kg_dm_per_cow_day"],
                "average_ration_cost_usd_per_cow_day": totals["average_cost_usd_per_cow_day"],
                "total_milk_kg": result["metrics"]["total_milk_kg"],
                "total_feed_cost_usd": economics["total_lactating_feed_cost"],
                "margin_usd": economics["margin_over_lactating_feed_cost"],
            }
        )
    frame = pd.DataFrame(rows)
    baseline = frame.loc[frame["key"] == "baseline"].iloc[0]
    for column in ["total_milk_kg", "total_feed_cost_usd", "margin_usd"]:
        frame[f"{column}_change_pct"] = (frame[column] / baseline[column] - 1) * 100
    return frame


def build_composition_matrix(
    cases: list[SensitivityCase],
    results: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Monta uma matriz cenário × ingrediente com percentuais de matéria seca."""
    rows: list[dict[str, Any]] = []
    for case in cases:
        ration, _ = summarize_lactating_ration(results[case.key], case.config)
        row: dict[str, Any] = {"key": case.key, "label": case.label}
        row.update(
            {
                str(int(item["feed_type"])): float(item["percentage_dm"])
                for _, item in ration.iterrows()
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).fillna(0).set_index("key")

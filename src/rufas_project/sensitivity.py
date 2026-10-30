import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .economics import calculate_economics
from .models import SimulationConfig
from .optimization import (
    CustomOptimizationResult,
    MainDietRequirements,
    build_fixed_scenario_from_solution,
    build_min_cost_scenario,
    evaluate_ration_against_main_requirements,
    solve_custom_min_cost,
    summarize_lactating_ration,
)


@dataclass
class SensitivityCase:
    key: str
    label: str
    config: SimulationConfig
    varied_feed_type: int | None
    multiplier: float
    base_price: float | None
    varied_price: float | None


@dataclass
class CustomSensitivityCase:
    """Variação de preço resolvida pelo nosso modelo de cinco restrições."""

    key: str
    label: str
    config: SimulationConfig
    solution: CustomOptimizationResult
    varied_feed_type: int | None
    multiplier: float
    base_price: float | None
    varied_price: float | None


def generate_custom_price_sensitivity_cases(
    reference: SimulationConfig,
    requirements: MainDietRequirements,
    feed_library_path: str | Path,
    baseline_solution: CustomOptimizationResult,
    multipliers: Iterable[float] = (0.8, 1.2),
) -> list[CustomSensitivityCase]:
    """Reotimiza nosso modelo após variar um preço por vez."""
    multiplier_values = tuple(float(value) for value in multipliers)
    if not multiplier_values or any(value <= 0 or value == 1 for value in multiplier_values):
        raise ValueError("os multiplicadores devem ser positivos, diferentes de 1 e não vazios")
    if not baseline_solution.success:
        raise ValueError("a solução-base do Notebook 2 não é válida")

    baseline_config = build_fixed_scenario_from_solution(
        reference, baseline_solution, name="fase3_base_notebook2"
    )
    cases = [
        CustomSensitivityCase(
            key="baseline",
            label="Linha de base do Notebook 2",
            config=baseline_config,
            solution=baseline_solution,
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
            varied_reference = copy.deepcopy(reference)
            varied = next(
                item for item in varied_reference.diet.ingredients if item.feed_type == ingredient.feed_type
            )
            base_price = varied.purchased_feed_cost_usd_per_kg_dm
            varied.purchased_feed_cost_usd_per_kg_dm *= multiplier
            solution = solve_custom_min_cost(varied_reference, feed_library_path, requirements)
            if not solution.success:
                raise RuntimeError(
                    f"nosso otimizador não encontrou dieta para {ingredient.feed_type} em {percentage:+d}%: "
                    f"{solution.message}"
                )
            config = build_fixed_scenario_from_solution(
                varied_reference, solution, name=f"fase3_nosso_{key}"
            )
            cases.append(
                CustomSensitivityCase(
                    key=key,
                    label=f"Ingrediente {ingredient.feed_type}: {abs(percentage)}% {direction}",
                    config=config,
                    solution=solution,
                    varied_feed_type=ingredient.feed_type,
                    multiplier=multiplier,
                    base_price=base_price,
                    varied_price=varied.purchased_feed_cost_usd_per_kg_dm,
                )
            )
    return cases


def summarize_custom_price_sensitivity(
    cases: list[CustomSensitivityCase],
    results: dict[str, dict[str, Any]],
    feed_library_path: str | Path,
    requirements: MainDietRequirements,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Consolida desempenho e verificação realizada das cinco restrições."""
    rows: list[dict[str, Any]] = []
    reports: list[pd.DataFrame] = []
    for case in cases:
        result = results[case.key]
        economics = calculate_economics(result, case.config)
        ration, totals = summarize_lactating_ration(result, case.config)
        realized_report = evaluate_ration_against_main_requirements(
            ration, feed_library_path, requirements
        )
        realized_report.insert(0, "key", case.key)
        realized_report.insert(1, "label", case.label)
        reports.append(realized_report)
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
                "objective_usd_per_cow_day": case.solution.objective_usd_per_cow_day,
                "planned_constraints_satisfied": bool(case.solution.constraint_report["satisfied"].all()),
                "realized_constraints_satisfied": bool(realized_report["satisfied"].all()),
                "average_dmi_kg_per_cow_day": totals["average_kg_dm_per_cow_day"],
                "average_ration_cost_usd_per_cow_day": totals["average_cost_usd_per_cow_day"],
                "total_milk_kg": result["metrics"]["total_milk_kg"],
                "total_feed_cost_usd": economics["total_lactating_feed_cost"],
                "milk_revenue_usd": economics["total_milk_revenue"],
                "margin_usd": economics["margin_over_lactating_feed_cost"],
            }
        )
    frame = pd.DataFrame(rows)
    baseline = frame.loc[frame["key"] == "baseline"].iloc[0]
    for column in ["total_milk_kg", "total_feed_cost_usd", "milk_revenue_usd", "margin_usd"]:
        frame[f"{column}_change_pct"] = (frame[column] / baseline[column] - 1) * 100
    return frame, pd.concat(reports, ignore_index=True)


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

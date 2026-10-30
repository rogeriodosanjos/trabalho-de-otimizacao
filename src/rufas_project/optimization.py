import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from .models import DietConfig, DietIngredient, SimulationConfig
from .validation import ConfigurationError, validate_simulation_config


@dataclass
class MainDietRequirements:
    """Cinco pisos nutricionais lineares definidos pelo modelo principal do PDF."""

    energy_tdn_min_kg_per_day: float
    protein_cp_min_kg_per_day: float
    calcium_min_g_per_day: float
    phosphorus_min_g_per_day: float
    fiber_ndf_min_kg_per_day: float
    source: str = "Fornecimento da dieta NASEM calculada pelo RuFaS"


@dataclass
class CustomOptimizationResult:
    """Solução e diagnósticos do nosso problema de programação linear."""

    success: bool
    message: str
    objective_usd_per_cow_day: float
    ration: pd.DataFrame
    constraint_report: pd.DataFrame


def build_min_cost_scenario(
    reference: SimulationConfig,
    name: str = "dieta_otimizada_menor_custo",
) -> SimulationConfig:
    """Cria um cenário que delega a formulação de menor custo ao RuFaS."""
    scenario = copy.deepcopy(reference)
    scenario.name = name
    scenario.diet.mode = "rufas_min_cost"
    if not scenario.diet.ingredients:
        raise ConfigurationError("a otimização precisa de pelo menos um ingrediente candidato")
    validate_simulation_config(scenario)
    return scenario


def describe_custom_min_cost_problem(
    config: SimulationConfig,
    requirements: MainDietRequirements,
) -> pd.DataFrame:
    """Descreve o problema linear independente implementado neste projeto."""
    return pd.DataFrame(
        [
            ("Variáveis de decisão", "xᵢ = kg de matéria seca do ingrediente i por vaca e por dia"),
            ("Função objetivo", "min C(x) = Σ pᵢ × xᵢ"),
            ("Método", "Programação linear pelo método HiGHS (scipy.optimize.linprog)"),
            ("Ingredientes candidatos", f"{len(config.diet.ingredients)} ingredientes"),
            (
                "Restrições",
                "Somente os cinco mínimos do PDF: energia (TDN), proteína bruta, cálcio, fósforo e fibra (NDF)",
            ),
            ("Origem dos mínimos", requirements.source),
            (
                "Independência",
                "A solução é calculada pelo código deste projeto; o formulador interno do RuFaS não é chamado nesta etapa",
            ),
        ],
        columns=["Elemento", "Definição"],
    )


def describe_custom_constraints(requirements: MainDietRequirements) -> pd.DataFrame:
    """Apresenta somente os cinco mínimos nutricionais do modelo principal."""
    rows = [
        ("Energia (TDN)", requirements.energy_tdn_min_kg_per_day, "kg TDN/vaca/dia"),
        ("Proteína bruta", requirements.protein_cp_min_kg_per_day, "kg PB/vaca/dia"),
        ("Cálcio", requirements.calcium_min_g_per_day, "g/vaca/dia"),
        ("Fósforo", requirements.phosphorus_min_g_per_day, "g/vaca/dia"),
        ("Fibra (NDF)", requirements.fiber_ndf_min_kg_per_day, "kg NDF/vaca/dia"),
    ]
    return pd.DataFrame(rows, columns=["Restrição", "Mínimo", "Unidade"])


def _load_feed_library(path: str | Path, feed_ids: list[int]) -> pd.DataFrame:
    library = pd.read_csv(path)
    selected = library[library["rufas_id"].isin(feed_ids)].copy()
    missing = sorted(set(feed_ids).difference(selected["rufas_id"].astype(int)))
    if missing:
        raise ConfigurationError(f"ingredientes ausentes na biblioteca nutricional do RuFaS: {missing}")
    return selected.set_index("rufas_id").loc[feed_ids].reset_index()


def derive_main_requirements_from_ration(
    ration: pd.DataFrame,
    feed_library_path: str | Path,
) -> MainDietRequirements:
    """Usa a dieta NASEM do RuFaS como referência para os cinco pisos lineares."""
    required_columns = {"feed_type", "average_kg_dm_per_cow_day"}
    missing_columns = required_columns.difference(ration.columns)
    if missing_columns:
        raise ConfigurationError(f"ração sem colunas obrigatórias: {sorted(missing_columns)}")
    feed_ids = [int(value) for value in ration["feed_type"]]
    library = _load_feed_library(feed_library_path, feed_ids)
    amounts = ration["average_kg_dm_per_cow_day"].to_numpy(dtype=float)

    def kg_nutrient(column: str) -> float:
        return float(np.dot(amounts, library[column].to_numpy(dtype=float) / 100.0))

    return MainDietRequirements(
        energy_tdn_min_kg_per_day=kg_nutrient("TDN"),
        protein_cp_min_kg_per_day=kg_nutrient("CP"),
        calcium_min_g_per_day=kg_nutrient("calcium") * 1000.0,
        phosphorus_min_g_per_day=kg_nutrient("phosphorus") * 1000.0,
        fiber_ndf_min_kg_per_day=kg_nutrient("NDF"),
    )


def evaluate_ration_against_main_requirements(
    ration: pd.DataFrame,
    feed_library_path: str | Path,
    requirements: MainDietRequirements,
) -> pd.DataFrame:
    """Avalia uma ração planejada ou realizada contra os cinco pisos do modelo."""
    amount_column = next(
        (
            column
            for column in ("average_kg_dm_per_cow_day", "kg_dm_per_cow_day")
            if column in ration.columns
        ),
        None,
    )
    if amount_column is None or "feed_type" not in ration.columns:
        raise ConfigurationError("ração sem ID dos ingredientes ou quantidade em kg MS/vaca/dia")
    feed_ids = [int(value) for value in ration["feed_type"]]
    library = _load_feed_library(feed_library_path, feed_ids)
    amounts = ration[amount_column].to_numpy(dtype=float)

    def kg_nutrient(column: str) -> float:
        return float(np.dot(amounts, library[column].to_numpy(dtype=float) / 100.0))

    values = {
        "Energia (TDN)": kg_nutrient("TDN"),
        "Proteína bruta": kg_nutrient("CP"),
        "Cálcio": kg_nutrient("calcium") * 1000.0,
        "Fósforo": kg_nutrient("phosphorus") * 1000.0,
        "Fibra (NDF)": kg_nutrient("NDF"),
    }
    rows = [
        ("Energia (TDN)", values["Energia (TDN)"], requirements.energy_tdn_min_kg_per_day, "kg TDN/vaca/dia"),
        ("Proteína bruta", values["Proteína bruta"], requirements.protein_cp_min_kg_per_day, "kg PB/vaca/dia"),
        ("Cálcio", values["Cálcio"], requirements.calcium_min_g_per_day, "g/vaca/dia"),
        ("Fósforo", values["Fósforo"], requirements.phosphorus_min_g_per_day, "g/vaca/dia"),
        ("Fibra (NDF)", values["Fibra (NDF)"], requirements.fiber_ndf_min_kg_per_day, "kg NDF/vaca/dia"),
    ]
    report = pd.DataFrame(rows, columns=["constraint", "value", "minimum", "unit"])
    report["satisfied"] = report["value"] >= report["minimum"] - 1e-7
    return report


def solve_custom_min_cost(
    config: SimulationConfig,
    feed_library_path: str | Path,
    requirements: MainDietRequirements,
) -> CustomOptimizationResult:
    """Minimiza o custo aplicando exclusivamente as cinco restrições do PDF."""
    validate_simulation_config(config)
    requirement_values = [
        requirements.energy_tdn_min_kg_per_day,
        requirements.protein_cp_min_kg_per_day,
        requirements.calcium_min_g_per_day,
        requirements.phosphorus_min_g_per_day,
        requirements.fiber_ndf_min_kg_per_day,
    ]
    if any(value <= 0 for value in requirement_values):
        raise ConfigurationError("todas as cinco exigências mínimas devem ser positivas")

    ingredients = config.diet.ingredients
    feed_ids = [item.feed_type for item in ingredients]
    library = _load_feed_library(feed_library_path, feed_ids)
    prices = np.array([item.purchased_feed_cost_usd_per_kg_dm for item in ingredients], dtype=float)
    nutrients = {
        "Energia (TDN)": library["TDN"].to_numpy(dtype=float) / 100.0,
        "Proteína bruta": library["CP"].to_numpy(dtype=float) / 100.0,
        "Cálcio": library["calcium"].to_numpy(dtype=float) / 100.0 * 1000.0,
        "Fósforo": library["phosphorus"].to_numpy(dtype=float) / 100.0 * 1000.0,
        "Fibra (NDF)": library["NDF"].to_numpy(dtype=float) / 100.0,
    }
    minimums = np.array(requirement_values, dtype=float)
    a_ub = -np.array(list(nutrients.values()))
    b_ub = -minimums

    solution = linprog(
        c=prices,
        A_ub=a_ub,
        b_ub=b_ub,
        bounds=[(0.0, None)] * len(ingredients),
        method="highs",
    )
    if not solution.success:
        return CustomOptimizationResult(
            success=False,
            message=solution.message,
            objective_usd_per_cow_day=float("nan"),
            ration=pd.DataFrame(),
            constraint_report=pd.DataFrame(),
        )

    amounts = np.asarray(solution.x, dtype=float)
    ration = pd.DataFrame(
        {
            "feed_type": feed_ids,
            "name": [item.name for item in ingredients],
            "kg_dm_per_cow_day": amounts,
            "percentage_dm": amounts / amounts.sum() * 100,
            "price_usd_per_kg_dm": prices,
            "cost_usd_per_cow_day": amounts * prices,
        }
    )
    report = evaluate_ration_against_main_requirements(ration, feed_library_path, requirements)
    return CustomOptimizationResult(
        success=True,
        message=solution.message,
        objective_usd_per_cow_day=float(solution.fun),
        ration=ration,
        constraint_report=report,
    )


def build_fixed_scenario_from_solution(
    reference: SimulationConfig,
    solution: CustomOptimizationResult,
    name: str = "dieta_otimizador_proprio",
) -> SimulationConfig:
    """Converte nossa solução em dieta fixa para avaliá-la dentro do RuFaS."""
    if not solution.success or solution.ration.empty:
        raise ConfigurationError("não é possível aplicar uma solução inexistente ou inviável")
    scenario = copy.deepcopy(reference)
    scenario.name = name
    scenario.diet = DietConfig(
        mode="fixed",
        formulation_interval_days=reference.diet.formulation_interval_days,
        ingredients=[
            DietIngredient(
                feed_type=int(row.feed_type),
                ration_percentage=float(row.percentage_dm),
                purchased_feed_cost_usd_per_kg_dm=float(row.price_usd_per_kg_dm),
                name=str(row.name),
            )
            for row in solution.ration.itertuples(index=False)
        ],
    )
    validate_simulation_config(scenario)
    return scenario


def describe_min_cost_problem(config: SimulationConfig) -> pd.DataFrame:
    """Descreve formalmente o problema resolvido pelo formulador interno do RuFaS."""
    return pd.DataFrame(
        [
            ("Variáveis de decisão", "xᵢ = kg de matéria seca do ingrediente i por vaca e por dia"),
            ("Função objetivo", "min C(x) = Σ pᵢ × xᵢ"),
            ("Preço", "pᵢ = USD por kg de matéria seca do ingrediente i"),
            ("Método numérico", "SLSQP, executado pelo formulador interno do RuFaS"),
            ("Padrão nutricional", "NASEM"),
            (
                "Restrições",
                "Energia líquida, proteína, cálcio, fósforo, NDF, NDF de forragem, gordura e consumo de matéria seca",
            ),
            ("Ingredientes candidatos", f"{len(config.diet.ingredients)} ingredientes informados no notebook"),
            ("Critério de comparação", "Custo alimentar, produção de leite, receita e margem sobre alimentação"),
        ],
        columns=["Elemento", "Definição"],
    )


def summarize_lactating_ration(
    result: dict[str, Any],
    config: SimulationConfig,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Resume a ração do lote em kg MS/vaca/dia, participação e custo médio."""
    names = {str(item.feed_type): item.name for item in config.diet.ingredients}
    prices = {
        str(feed_id): float(cost)
        for feed_id, cost in result.get("feed_costs_usd_per_kg_dm", {}).items()
    }
    prices.update(
        {
            str(item.feed_type): item.purchased_feed_cost_usd_per_kg_dm
            for item in config.diet.ingredients
        }
    )
    daily_per_cow: list[dict[str, float]] = []
    for row in result["series"]:
        cows = float(row.get("lactating_cows") or 0)
        if cows <= 0:
            continue
        daily_per_cow.append(
            {
                str(feed_id): float(amount) / cows
                for feed_id, amount in row.get("lactating_feed_kg_dm", {}).items()
            }
        )
    if not daily_per_cow:
        raise ValueError("o resultado não contém consumo de vacas em lactação")

    feed_ids = sorted({feed_id for day in daily_per_cow for feed_id in day}, key=int)
    rows = []
    for feed_id in feed_ids:
        average_amount = sum(day.get(feed_id, 0.0) for day in daily_per_cow) / len(daily_per_cow)
        if average_amount <= 1e-8:
            continue
        price = prices.get(feed_id, 0.0)
        rows.append(
            {
                "feed_type": int(feed_id),
                "name": names.get(feed_id, f"Ingrediente RuFaS {feed_id}"),
                "average_kg_dm_per_cow_day": average_amount,
                "price_usd_per_kg_dm": price,
                "average_cost_usd_per_cow_day": average_amount * price,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("a ração de vacas em lactação não contém ingredientes positivos")
    total_amount = float(frame["average_kg_dm_per_cow_day"].sum())
    total_cost = float(frame["average_cost_usd_per_cow_day"].sum())
    frame["percentage_dm"] = frame["average_kg_dm_per_cow_day"] / total_amount * 100
    return frame, {
        "average_kg_dm_per_cow_day": total_amount,
        "average_cost_usd_per_cow_day": total_cost,
    }

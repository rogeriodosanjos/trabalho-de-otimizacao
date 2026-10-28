import copy
from typing import Any

import pandas as pd

from .models import SimulationConfig
from .validation import ConfigurationError, validate_simulation_config


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

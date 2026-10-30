import re
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _find_column(frame: pd.DataFrame, variable: str) -> str | None:
    return next((str(column) for column in frame.columns if variable in str(column)), None)


def _numbers(frame: pd.DataFrame, variable: str) -> list[float]:
    column = _find_column(frame, variable)
    if column is None:
        return []
    return [float(value) for value in pd.to_numeric(frame[column], errors="coerce").dropna()]


def _number(frame: pd.DataFrame, variable: str) -> float | None:
    values = _numbers(frame, variable)
    return values[0] if values else None


def _text(frame: pd.DataFrame, variable: str) -> str | None:
    column = _find_column(frame, variable)
    if column is None:
        return None
    values = frame[column].dropna()
    return str(values.iloc[0]) if not values.empty else None


def _breed_name(frame: pd.DataFrame) -> str | None:
    """Remove a representação de conjunto usada pelo RuFaS para a raça."""
    value = _text(frame, "initial_breed")
    if value is None:
        return None
    return value.strip().strip("{}[]()'\" ")


def _feed_columns(frame: pd.DataFrame) -> dict[int, str]:
    columns: dict[int, str] = {}
    for column in frame.columns:
        text = str(column)
        if "ration_daily_feed_totals_for_pen_3_LAC_COW" not in text:
            continue
        match = re.search(r"\.(\d+)(?:\s|\(|$)", text)
        if match:
            columns[int(match.group(1))] = text
    return columns


def parse_rufas_results(run_dir: Path) -> dict[str, Any]:
    csv_files = sorted((run_dir / "output/csv").glob("*.csv"))
    if not csv_files:
        raise RuntimeError("O RuFaS terminou sem produzir o CSV solicitado")
    csv_path = csv_files[-1]
    frame = pd.read_csv(csv_path)
    lactating = _numbers(frame, "num_lactating_cows") or _numbers(frame, "milking_cow_num")
    dry = _numbers(frame, "num_dry_cows") or _numbers(frame, "dry_cow_num")
    total = _numbers(frame, "num_cows_total")
    milk = _numbers(frame, "daily_milk_production")
    dim = _numbers(frame, "avg_days_in_milk")
    if not lactating or not total or not milk:
        raise RuntimeError("O CSV não contém todas as variáveis essenciais de população e leite")

    feed_columns = _feed_columns(frame)
    feed_series = {
        feed_id: [
            float(value)
            for value in pd.to_numeric(frame[column], errors="coerce").fillna(0).tolist()
        ]
        for feed_id, column in feed_columns.items()
    }
    length = max(len(lactating), len(total), len(milk))

    def at(values: list[float], index: int) -> float | None:
        return values[index] if index < len(values) else None

    series = []
    for index in range(length):
        series.append(
            {
                "day": index + 1,
                "lactating_cows": at(lactating, index),
                "dry_cows": at(dry, index),
                "total_cows": at(total, index),
                "milk_kg": at(milk, index),
                "avg_days_in_milk": at(dim, index),
                "lactating_feed_kg_dm": {
                    str(feed_id): at(values, index) or 0.0 for feed_id, values in feed_series.items()
                },
            }
        )
    prices_path = run_dir / "feed_prices.json"
    feed_prices = (
        json.loads(prices_path.read_text(encoding="utf-8")) if prices_path.exists() else {}
    )
    config_path = run_dir / "resolved_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    initial_population = {
        "random_seed": config.get("random_seed"),
        "breed": _breed_name(frame),
        "number_of_calves": _number(frame, "initial_number_of_calves"),
        "number_of_heifer_is": _number(frame, "initial_number_of_heiferIs"),
        "number_of_heifer_iis": _number(frame, "initial_number_of_heiferIIs"),
        "number_of_heifer_iiis": _number(frame, "initial_number_of_heiferIIIs"),
        "number_of_cows": _number(frame, "initial_number_of_cows"),
        "number_of_lactating_cows": _number(frame, "initial_number_of_lactating_cows"),
        "number_of_dry_cows": _number(frame, "initial_number_of_dry_cows"),
        "average_cow_age_days": _number(frame, "initial_average_cow_age"),
        "average_cow_body_weight_kg": _number(frame, "initial_average_cow_body_weight"),
        "average_cow_days_in_pregnancy": _number(frame, "initial_average_cow_days_in_pregnancy"),
        "average_cow_days_in_milk": _number(frame, "initial_average_cow_days_in_milk"),
        "average_cow_parity": _number(frame, "initial_average_cow_parity"),
        "parity_distribution": {
            "1": _number(frame, "initial_number_of_parity_1_cows"),
            "2": _number(frame, "initial_number_of_parity_2_cows"),
            "3": _number(frame, "initial_number_of_parity_3_cows"),
            "4": _number(frame, "initial_number_of_parity_4_cows"),
            "5": _number(frame, "initial_number_of_parity_5_cows"),
            "6_or_more": _number(frame, "initial_number_of_parity_6_or_more_cows"),
        },
    }
    return {
        "source": "RuFaS",
        "csv_path": str(csv_path.relative_to(run_dir)),
        "metrics": {
            "initial_lactating_cows": lactating[0],
            "final_lactating_cows": lactating[-1],
            "final_dry_cows": dry[-1] if dry else None,
            "final_total_cows": total[-1],
            "total_milk_kg": sum(milk),
            "average_daily_milk_kg": sum(milk) / len(milk),
            "peak_daily_milk_kg": max(milk),
            "final_avg_days_in_milk": dim[-1] if dim else None,
        },
        "feed_costs_usd_per_kg_dm": feed_prices,
        "initial_population": initial_population,
        "series": series,
    }


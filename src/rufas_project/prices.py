import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .models import SimulationConfig


def load_price_snapshot(path: str | Path) -> dict[str, Any]:
    """Carrega e valida o snapshot reproduzível de preços do experimento."""
    with Path(path).open(encoding="utf-8") as stream:
        snapshot = json.load(stream)
    required = {"snapshot_date", "currency", "ingredients", "milk"}
    missing = required.difference(snapshot)
    if missing:
        raise ValueError(f"snapshot de preços incompleto: {sorted(missing)}")
    if snapshot["currency"] != "USD":
        raise ValueError("este experimento espera preços normalizados em USD")
    for record in snapshot["ingredients"]:
        if float(record["price_usd_per_kg_dm"]) < 0:
            raise ValueError(f"preço negativo para o ingrediente {record['feed_type']}")
    return snapshot


def apply_price_snapshot(config: SimulationConfig, snapshot: dict[str, Any]) -> SimulationConfig:
    """Aplica preços de ingredientes e leite a uma cópia do cenário."""
    priced = copy.deepcopy(config)
    records = {int(row["feed_type"]): row for row in snapshot["ingredients"]}
    missing = [item.feed_type for item in priced.diet.ingredients if item.feed_type not in records]
    if missing:
        raise ValueError(f"snapshot sem preço para os ingredientes: {missing}")
    for ingredient in priced.diet.ingredients:
        ingredient.purchased_feed_cost_usd_per_kg_dm = float(
            records[ingredient.feed_type]["price_usd_per_kg_dm"]
        )

    milk = snapshot["milk"]
    priced.economics.milk_price = float(milk["milk_price"])
    priced.economics.milk_price_unit = milk["milk_price_unit"]
    priced.economics.milk_density_kg_per_liter = float(milk["milk_density_kg_per_liter"])
    priced.economics.milk_price_source = (
        f"{milk['source_name']} ({milk['reference_date']}); {milk['source_url']}"
    )
    priced.economics.currency = snapshot["currency"]
    return priced


def describe_price_snapshot(snapshot: dict[str, Any]) -> pd.DataFrame:
    """Organiza preço, unidade original e proveniência para exibição no notebook."""
    return pd.DataFrame(
        [
            {
                "feed_type": int(row["feed_type"]),
                "name": row["name"],
                "range_min_brl_per_kg": float(row.get("range_min_brl_per_kg", row["raw_price"])),
                "range_max_brl_per_kg": float(row.get("range_max_brl_per_kg", row["raw_price"])),
                "raw_price": float(row["raw_price"]),
                "raw_unit": row["raw_unit"],
                "price_basis": row.get("price_basis", "não informada"),
                "dry_matter_fraction": float(row["dry_matter_fraction"]),
                "price_usd_per_kg_dm": float(row["price_usd_per_kg_dm"]),
                "source_kind": row["source_kind"],
                "source_name": row["source_name"],
                "reference_date": row["reference_date"] or "não disponível",
                "conversion_note": row.get("conversion_note", "não informada"),
            }
            for row in snapshot["ingredients"]
        ]
    )

import re

from .models import SimulationConfig


class ConfigurationError(ValueError):
    """Erro de configuração detectado antes da execução do RuFaS."""


def validate_simulation_config(config: SimulationConfig) -> None:
    errors: list[str] = []
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", config.name):
        errors.append("name deve conter apenas letras, números, '_' ou '-'")
    if not 1 <= config.simulation_days <= 365:
        errors.append("simulation_days deve estar entre 1 e 365")
    if not 0 <= config.random_seed <= 4_294_967_295:
        errors.append("random_seed está fora da faixa aceita pelo RuFaS")
    if not 6 <= config.herd.cow_num <= 100:
        errors.append("cow_num deve estar entre 6 e 100 neste ambiente")
    if not 0.5 <= config.herd.milking_cow_fraction <= 1.0:
        errors.append("milking_cow_fraction deve estar entre 0.5 e 1.0")
    if config.herd.breed not in {"HO", "JE"}:
        errors.append("breed deve ser 'HO' ou 'JE'")

    parity_total = sum(config.herd.parity_fractions.as_rufas_dict().values())
    if abs(parity_total - 1.0) > 1e-6:
        errors.append("as frações de paridade devem somar 1.0")
    if any(value < 0 or value > 1 for value in config.herd.parity_fractions.as_rufas_dict().values()):
        errors.append("cada fração de paridade deve estar entre 0 e 1")

    if not 2 <= config.milk.fat_percent <= 7:
        errors.append("fat_percent deve estar entre 2 e 7")
    if not 2 <= config.milk.protein_percent <= 6:
        errors.append("protein_percent deve estar entre 2 e 6")
    if not 300 <= config.milk.mature_body_weight_kg <= 1_000:
        errors.append("mature_body_weight_kg deve estar entre 300 e 1000")
    if config.diet.mode not in {"fixed", "rufas_min_cost"}:
        errors.append("diet.mode deve ser 'fixed' ou 'rufas_min_cost'")
    if not 1 <= config.diet.formulation_interval_days <= 365:
        errors.append("formulation_interval_days deve estar entre 1 e 365")

    if config.diet.ingredients:
        ids = [ingredient.feed_type for ingredient in config.diet.ingredients]
        if len(ids) != len(set(ids)):
            errors.append("feed_type não pode aparecer duas vezes na dieta")
        percentage_total = sum(item.ration_percentage for item in config.diet.ingredients)
        if config.diet.mode == "fixed" and abs(percentage_total - 100.0) > 1e-6:
            errors.append("a dieta fixa deve somar 100%")
        for item in config.diet.ingredients:
            if item.ration_percentage < 0:
                errors.append(f"percentual negativo para feed_type {item.feed_type}")
            if item.purchased_feed_cost_usd_per_kg_dm < 0:
                errors.append(f"custo negativo para feed_type {item.feed_type}")

    if config.economics.milk_price_usd_per_kg < 0:
        errors.append("milk_price_usd_per_kg não pode ser negativo")
    if not config.economics.milk_price_source.strip():
        errors.append("milk_price_source deve documentar a fonte ou hipótese")

    if errors:
        raise ConfigurationError("Configuração inválida:\n- " + "\n- ".join(errors))


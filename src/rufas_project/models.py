import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class ParityFractions:
    parity_1: float = 0.40
    parity_2: float = 0.25
    parity_3: float = 0.20
    parity_4: float = 0.10
    parity_5: float = 0.05

    def as_rufas_dict(self) -> dict[str, float]:
        return {
            "1": self.parity_1,
            "2": self.parity_2,
            "3": self.parity_3,
            "4": self.parity_4,
            "5": self.parity_5,
        }


@dataclass
class HerdConfig:
    cow_num: int = 20
    milking_cow_fraction: float = 0.80
    breed: Literal["HO", "JE"] = "HO"
    parity_fractions: ParityFractions = field(default_factory=ParityFractions)


@dataclass
class MilkConfig:
    fat_percent: float = 4.0
    protein_percent: float = 3.2
    mature_body_weight_kg: float = 740.1


@dataclass
class DietIngredient:
    feed_type: int
    ration_percentage: float
    purchased_feed_cost_usd_per_kg_dm: float
    name: str = ""


@dataclass
class DietConfig:
    mode: Literal["fixed", "rufas_min_cost"] = "fixed"
    ingredients: list[DietIngredient] = field(default_factory=list)
    formulation_interval_days: int = 30


@dataclass
class EconomicConfig:
    milk_price: float = 0.45
    milk_price_unit: Literal["per_kg", "per_liter"] = "per_kg"
    milk_density_kg_per_liter: float = 1.03
    milk_price_source: str = "Hipótese didática; substituir por fonte e data definidas pelo projeto"
    currency: str = "USD"

    @property
    def milk_price_per_kg(self) -> float:
        """Normaliza o preço informado para a unidade usada nas saídas do RuFaS."""
        if self.milk_price_unit == "per_liter":
            return self.milk_price / self.milk_density_kg_per_liter
        return self.milk_price


@dataclass
class SimulationConfig:
    name: str = "cenario_referencia"
    simulation_days: int = 30
    random_seed: int = 42
    herd: HerdConfig = field(default_factory=HerdConfig)
    milk: MilkConfig = field(default_factory=MilkConfig)
    diet: DietConfig = field(default_factory=DietConfig)
    economics: EconomicConfig = field(default_factory=EconomicConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def simulation_config_from_dict(data: dict[str, Any]) -> SimulationConfig:
    data = copy.deepcopy(data)
    parity = ParityFractions(**data["herd"].pop("parity_fractions"))
    herd = HerdConfig(parity_fractions=parity, **data["herd"])
    milk = MilkConfig(**data["milk"])
    ingredients = [DietIngredient(**item) for item in data["diet"].pop("ingredients")]
    diet = DietConfig(ingredients=ingredients, **data["diet"])
    economics_data = data["economics"]
    # Compatibilidade com cenários gravados antes da seleção de unidade e moeda.
    if "milk_price_usd_per_kg" in economics_data:
        economics_data["milk_price"] = economics_data.pop("milk_price_usd_per_kg")
        economics_data.setdefault("milk_price_unit", "per_kg")
        economics_data.setdefault("currency", "USD")
    economics = EconomicConfig(**economics_data)
    return SimulationConfig(
        name=data["name"],
        simulation_days=data["simulation_days"],
        random_seed=data["random_seed"],
        herd=herd,
        milk=milk,
        diet=diet,
        economics=economics,
    )


"""Ferramentas reutilizáveis para experimentos com o RuFaS."""

from .comparison import compare_scenarios
from .economics import calculate_economics
from .jobs import get_job, list_jobs, load_result, submit_simulation, wait_for_simulation
from .models import (
    DietConfig,
    DietIngredient,
    EconomicConfig,
    HerdConfig,
    MilkConfig,
    ParityFractions,
    SimulationConfig,
)
from .optimization import build_min_cost_scenario, describe_min_cost_problem, summarize_lactating_ration
from .reference import load_reference_scenario
from .sensitivity import (
    SensitivityCase,
    build_composition_matrix,
    generate_price_sensitivity_cases,
    summarize_price_sensitivity,
)
from .validation import validate_simulation_config

__all__ = [
    "DietConfig",
    "DietIngredient",
    "EconomicConfig",
    "HerdConfig",
    "MilkConfig",
    "ParityFractions",
    "SimulationConfig",
    "SensitivityCase",
    "calculate_economics",
    "build_min_cost_scenario",
    "build_composition_matrix",
    "compare_scenarios",
    "describe_min_cost_problem",
    "get_job",
    "generate_price_sensitivity_cases",
    "list_jobs",
    "load_reference_scenario",
    "load_result",
    "submit_simulation",
    "summarize_lactating_ration",
    "summarize_price_sensitivity",
    "validate_simulation_config",
    "wait_for_simulation",
]


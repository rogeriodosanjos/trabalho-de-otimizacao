"""Ferramentas reutilizáveis para experimentos com o RuFaS."""

from .artifacts import (
    CustomBaselineArtifact,
    load_custom_baseline_artifact,
    save_custom_baseline_artifact,
)
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
from .optimization import (
    CustomOptimizationResult,
    MainDietRequirements,
    build_fixed_scenario_from_solution,
    build_min_cost_scenario,
    derive_main_requirements_from_ration,
    describe_custom_constraints,
    describe_custom_min_cost_problem,
    describe_min_cost_problem,
    evaluate_ration_against_main_requirements,
    solve_custom_min_cost,
    summarize_lactating_ration,
)
from .prices import apply_price_snapshot, describe_price_snapshot, load_price_snapshot
from .reference import load_reference_scenario
from .sensitivity import (
    CustomSensitivityCase,
    SensitivityCase,
    build_composition_matrix,
    generate_price_sensitivity_cases,
    generate_custom_price_sensitivity_cases,
    summarize_custom_price_sensitivity,
    summarize_price_sensitivity,
)
from .validation import validate_simulation_config

__all__ = [
    "DietConfig",
    "CustomBaselineArtifact",
    "CustomSensitivityCase",
    "MainDietRequirements",
    "DietIngredient",
    "EconomicConfig",
    "HerdConfig",
    "MilkConfig",
    "ParityFractions",
    "SimulationConfig",
    "SensitivityCase",
    "CustomOptimizationResult",
    "apply_price_snapshot",
    "calculate_economics",
    "build_fixed_scenario_from_solution",
    "build_min_cost_scenario",
    "build_composition_matrix",
    "compare_scenarios",
    "describe_custom_constraints",
    "describe_custom_min_cost_problem",
    "describe_min_cost_problem",
    "describe_price_snapshot",
    "evaluate_ration_against_main_requirements",
    "derive_main_requirements_from_ration",
    "get_job",
    "generate_price_sensitivity_cases",
    "generate_custom_price_sensitivity_cases",
    "list_jobs",
    "load_reference_scenario",
    "load_price_snapshot",
    "load_custom_baseline_artifact",
    "load_result",
    "submit_simulation",
    "solve_custom_min_cost",
    "save_custom_baseline_artifact",
    "summarize_lactating_ration",
    "summarize_price_sensitivity",
    "summarize_custom_price_sensitivity",
    "validate_simulation_config",
    "wait_for_simulation",
]


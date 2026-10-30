import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from .models import SimulationConfig, simulation_config_from_dict
from .optimization import CustomOptimizationResult, MainDietRequirements


@dataclass
class CustomBaselineArtifact:
    """Linha de base transferida do Notebook 2 para a sensibilidade."""

    reference: SimulationConfig
    scenario: SimulationConfig
    requirements: MainDietRequirements
    solution: CustomOptimizationResult
    job_id: str
    created_by: str


def save_custom_baseline_artifact(
    path: str | Path,
    reference: SimulationConfig,
    scenario: SimulationConfig,
    requirements: MainDietRequirements,
    solution: CustomOptimizationResult,
    job_id: str,
) -> Path:
    """Salva a solução do Notebook 2 de forma reproduzível e portátil."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_by": "notebooks/02_otimizacao_dieta.ipynb",
        "job_id": job_id,
        "reference": reference.to_dict(),
        "scenario": scenario.to_dict(),
        "requirements": asdict(requirements),
        "solution": {
            "success": solution.success,
            "message": solution.message,
            "objective_usd_per_cow_day": solution.objective_usd_per_cow_day,
            "ration": solution.ration.to_dict(orient="records"),
            "constraint_report": solution.constraint_report.to_dict(orient="records"),
        },
    }
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(target)
    return target


def load_custom_baseline_artifact(path: str | Path) -> CustomBaselineArtifact:
    """Carrega e reconstrói a linha de base exportada pelo Notebook 2."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(
            f"Artefato do Notebook 2 não encontrado em {source}. Execute o Notebook 2 por completo primeiro."
        )
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("versão do artefato do Notebook 2 não suportada")
    solution_data = payload["solution"]
    solution = CustomOptimizationResult(
        success=bool(solution_data["success"]),
        message=str(solution_data["message"]),
        objective_usd_per_cow_day=float(solution_data["objective_usd_per_cow_day"]),
        ration=pd.DataFrame(solution_data["ration"]),
        constraint_report=pd.DataFrame(solution_data["constraint_report"]),
    )
    return CustomBaselineArtifact(
        reference=simulation_config_from_dict(payload["reference"]),
        scenario=simulation_config_from_dict(payload["scenario"]),
        requirements=MainDietRequirements(**payload["requirements"]),
        solution=solution,
        job_id=str(payload["job_id"]),
        created_by=str(payload["created_by"]),
    )

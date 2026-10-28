import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .economics import calculate_economics
from .inputs import prepare_run_inputs, read_json, write_json
from .models import simulation_config_from_dict
from .results import parse_rufas_results


def update_status(job_dir: Path, **changes: Any) -> None:
    status = read_json(job_dir / "status.json")
    status.update(changes)
    write_json(job_dir / "status.json", status)


def execute_job(
    job_dir: Path,
    rufas_root: Path,
    timeout_seconds: int = 1_800,
) -> None:
    config = simulation_config_from_dict(read_json(job_dir / "request.json"))
    update_status(job_dir, status="running", message="Preparando entradas", started_at=time.time())
    try:
        manager_path = prepare_run_inputs(job_dir, rufas_root, config)
        update_status(job_dir, message="Executando o main.py do RuFaS")
        with (job_dir / "run.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(rufas_root / "main.py"),
                    "-p",
                    str(manager_path),
                    "-g",
                    "-v",
                    "warnings",
                ],
                cwd=rufas_root,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        if completed.returncode != 0:
            raise RuntimeError(
                f"RuFaS encerrou com código {completed.returncode}; consulte run.log"
            )
        result = parse_rufas_results(job_dir)
        result["economics"] = calculate_economics(result, config)
        write_json(job_dir / "result.json", result)
        update_status(
            job_dir,
            status="succeeded",
            message="Simulação concluída e resultados processados",
            finished_at=time.time(),
        )
    except Exception as exc:
        update_status(
            job_dir,
            status="failed",
            message="Falha na execução",
            error=str(exc),
            finished_at=time.time(),
        )


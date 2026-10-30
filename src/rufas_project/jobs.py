import json
import time
import uuid
from pathlib import Path
from typing import Any

from .models import SimulationConfig
from .validation import validate_simulation_config


TERMINAL_STATES = {"succeeded", "failed"}
STATUS_LABELS = {
    "queued": "Aguardando",
    "running": "Em execução",
    "succeeded": "Concluída",
    "failed": "Falhou",
}


def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def submit_simulation(
    config: SimulationConfig,
    shared_root: str | Path = "/workspace/shared",
) -> str:
    validate_simulation_config(config)
    job_id = str(uuid.uuid4())
    job_dir = Path(shared_root) / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    _atomic_json_write(job_dir / "request.json", config.to_dict())
    _atomic_json_write(
        job_dir / "status.json",
        {
            "id": job_id,
            "scenario": config.name,
            "status": "queued",
            "message": "Solicitação gravada; aguardando o worker do RuFaS",
            "created_at": time.time(),
            "started_at": None,
            "finished_at": None,
            "error": None,
        },
    )
    return job_id


def get_job(job_id: str, shared_root: str | Path = "/workspace/shared") -> dict[str, Any]:
    path = Path(shared_root) / "jobs" / job_id / "status.json"
    if not path.exists():
        raise FileNotFoundError(f"Execução {job_id} não encontrada")
    return json.loads(path.read_text(encoding="utf-8"))


def wait_for_simulation(
    job_id: str,
    shared_root: str | Path = "/workspace/shared",
    timeout_seconds: float = 1_800,
    poll_seconds: float = 2,
    show_progress: bool = True,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_message = None
    while time.monotonic() < deadline:
        status = get_job(job_id, shared_root)
        label = STATUS_LABELS.get(status["status"], status["status"])
        message = f"{label}: {status.get('message', '')}"
        if show_progress and message != last_message:
            print(message)
            last_message = message
        if status["status"] in TERMINAL_STATES:
            if status["status"] == "failed":
                raise RuntimeError(status.get("error") or "A simulação falhou")
            return status
        time.sleep(poll_seconds)
    raise TimeoutError(f"A execução {job_id} não terminou em {timeout_seconds} segundos")


def load_result(job_id: str, shared_root: str | Path = "/workspace/shared") -> dict[str, Any]:
    path = Path(shared_root) / "jobs" / job_id / "result.json"
    if not path.exists():
        status = get_job(job_id, shared_root)
        raise FileNotFoundError(f"Resultado indisponível; estado atual: {status['status']}")
    return json.loads(path.read_text(encoding="utf-8"))


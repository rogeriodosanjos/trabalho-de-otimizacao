import os
import signal
import time
from pathlib import Path

from rufas_project.execution import execute_job, update_status
from rufas_project.inputs import read_json


SHARED_ROOT = Path(os.getenv("SHARED_ROOT", "/workspace/shared"))
RUFAS_ROOT = Path(os.getenv("RUFAS_ROOT", "/opt/rufas"))
POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1"))
TIMEOUT_SECONDS = int(os.getenv("SIMULATION_TIMEOUT_SECONDS", "1800"))
HEALTH_FILE = Path(os.getenv("WORKER_HEALTH_FILE", "/tmp/rufas-worker-ready"))
running = True


def stop(*_: object) -> None:
    global running
    running = False


def recover_interrupted_jobs() -> None:
    for status_path in (SHARED_ROOT / "jobs").glob("*/status.json"):
        status = read_json(status_path)
        if status.get("status") == "running":
            update_status(
                status_path.parent,
                status="failed",
                message="Execução interrompida pelo reinício do worker",
                error="O contêiner do worker foi reiniciado durante a simulação",
                finished_at=time.time(),
            )


def next_queued_job() -> Path | None:
    candidates = []
    for status_path in (SHARED_ROOT / "jobs").glob("*/status.json"):
        status = read_json(status_path)
        if status.get("status") == "queued":
            candidates.append((status.get("created_at", 0), status_path.parent))
    return min(candidates, default=(None, None), key=lambda item: item[0])[1]


def main() -> None:
    (SHARED_ROOT / "jobs").mkdir(parents=True, exist_ok=True)
    recover_interrupted_jobs()
    HEALTH_FILE.write_text("ready\n", encoding="utf-8")
    print(f"Worker RuFaS ativo; fila em {SHARED_ROOT / 'jobs'}", flush=True)
    while running:
        job_dir = next_queued_job()
        if job_dir is None:
            time.sleep(POLL_SECONDS)
            continue
        print(f"Executando {job_dir.name}", flush=True)
        execute_job(job_dir, RUFAS_ROOT, TIMEOUT_SECONDS)
        print(f"Finalizado {job_dir.name}", flush=True)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    main()


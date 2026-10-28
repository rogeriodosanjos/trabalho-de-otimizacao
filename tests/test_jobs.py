import json

from rufas_project.jobs import get_job, submit_simulation
from rufas_project.models import SimulationConfig


def test_submit_creates_an_atomic_queue_job(tmp_path):
    config = SimulationConfig()
    config.diet.ingredients = []
    config.diet.mode = "rufas_min_cost"
    job_id = submit_simulation(config, tmp_path)
    job_dir = tmp_path / "jobs" / job_id

    assert json.loads((job_dir / "request.json").read_text())["name"] == config.name
    assert get_job(job_id, tmp_path)["status"] == "queued"
    assert not list(job_dir.glob("*.tmp"))

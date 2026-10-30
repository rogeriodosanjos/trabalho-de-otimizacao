from rufas_project.artifacts import load_custom_baseline_artifact, save_custom_baseline_artifact
from rufas_project.models import DietConfig, DietIngredient, SimulationConfig
from rufas_project.optimization import MainDietRequirements, solve_custom_min_cost


def test_custom_baseline_round_trip(tmp_path):
    library = tmp_path / "feeds.csv"
    library.write_text(
        "rufas_id,TDN,CP,calcium,phosphorus,NDF\n"
        "44,80,10,0.5,0.3,10\n"
        "50,60,20,1.0,0.5,40\n",
        encoding="utf-8",
    )
    reference = SimulationConfig()
    reference.diet = DietConfig(
        ingredients=[
            DietIngredient(44, 40, 0.50, "Milho"),
            DietIngredient(50, 60, 0.10, "Silagem"),
        ]
    )
    requirements = MainDietRequirements(10.0, 2.0, 100.0, 50.0, 5.0)
    solution = solve_custom_min_cost(reference, library, requirements)
    artifact_path = tmp_path / "baseline.json"
    save_custom_baseline_artifact(
        artifact_path, reference, reference, requirements, solution, "job-123"
    )

    loaded = load_custom_baseline_artifact(artifact_path)
    assert loaded.job_id == "job-123"
    assert loaded.reference.random_seed == reference.random_seed
    assert loaded.requirements.energy_tdn_min_kg_per_day == 10.0
    assert loaded.solution.objective_usd_per_cow_day == solution.objective_usd_per_cow_day
    assert loaded.solution.constraint_report["satisfied"].all()

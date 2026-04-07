import os
from types import SimpleNamespace

from swe_bench.report import run_evals


def test_run_evals_uses_subprocess_cwd_without_chdir(tmp_path, monkeypatch):
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    original_cwd = os.getcwd()
    recorded = {}

    def fake_run(command, check, cwd, stdout, stderr):
        recorded["command"] = command
        recorded["check"] = check
        recorded["cwd"] = cwd
        recorded["stderr"] = stderr
        stdout.write("evaluation complete\n")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("swe_bench.report.subprocess.run", fake_run)

    run_evals(
        predictions_jsonl="predictions.jsonl",
        run_id="run-123",
        dataset_name="demo-dataset",
        root_dir="/repo",
        output_dir=str(output_dir),
        num_eval_procs=7,
    )

    assert os.getcwd() == original_cwd
    assert recorded["check"] is True
    assert recorded["cwd"] == output_dir
    assert recorded["command"][0] == "python"
    assert "--run_id" in recorded["command"]
    assert (output_dir / "run-123_run_evaluation.log").read_text() == "evaluation complete\n"

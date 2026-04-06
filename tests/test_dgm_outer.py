import json

from DGM_outer import choose_selfimproves, initialize_run


def write_metadata(base_dir, commit_id, overall_performance, parent_commit="initial"):
    commit_dir = base_dir / commit_id
    commit_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "parent_commit": parent_commit,
        "overall_performance": overall_performance,
    }
    (commit_dir / "metadata.json").write_text(json.dumps(metadata))


def test_choose_selfimproves_best_prefers_highest_score(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    write_metadata(
        output_dir,
        "initial",
        {
            "accuracy_score": 0.1,
            "total_unresolved_ids": ["initial_issue"],
            "total_emptypatch_ids": [],
            "total_resolved_ids": [],
        },
    )
    write_metadata(
        output_dir,
        "candidate_low",
        {
            "accuracy_score": 0.4,
            "total_unresolved_ids": ["low_issue"],
            "total_emptypatch_ids": [],
            "total_resolved_ids": [],
        },
    )
    write_metadata(
        output_dir,
        "candidate_high",
        {
            "accuracy_score": 0.9,
            "total_unresolved_ids": ["high_issue"],
            "total_emptypatch_ids": [],
            "total_resolved_ids": [],
        },
    )
    monkeypatch.setattr("random.choice", lambda items: items[0])

    chosen = choose_selfimproves(
        str(output_dir),
        ["initial", "candidate_low", "candidate_high"],
        selfimprove_size=1,
        method="best",
        polyglot=True,
    )

    assert chosen == [("candidate_high", "high_issue")]


def test_choose_selfimproves_skips_empty_unresolved_ids(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    write_metadata(
        output_dir,
        "initial",
        {
            "accuracy_score": 0.5,
            "total_unresolved_ids": [],
            "total_emptypatch_ids": [],
            "total_resolved_ids": ["resolved_issue"],
        },
    )
    monkeypatch.setattr("random.random", lambda: 1.0)

    chosen = choose_selfimproves(
        str(output_dir),
        ["initial"],
        selfimprove_size=1,
        method="random",
        polyglot=False,
    )

    assert chosen == []


def test_initialize_run_polyglot_copies_seed_data_to_initial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_dir = tmp_path / "initial_polyglot"
    source_dir.mkdir()
    (source_dir / "metadata.json").write_text("{}")

    output_dir = tmp_path / "output"
    archive, start_generation = initialize_run(str(output_dir), polyglot=True)

    assert archive == ["initial"]
    assert start_generation == 0
    assert (output_dir / "initial" / "metadata.json").exists()

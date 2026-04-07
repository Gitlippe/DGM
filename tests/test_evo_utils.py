from utils.evo_utils import is_compiled_self_improve


def test_is_compiled_self_improve_supports_missing_logger_and_issue_counts():
    metadata = {
        "overall_performance": {
            "accuracy_score": 0.5,
            "total_unresolved_ids": ["issue_b"],
            "total_resolved_ids": ["issue_a"],
            "total_emptypatch_ids": [],
            "total_submitted_instances": 2,
        }
    }

    assert is_compiled_self_improve(metadata) is True
    assert is_compiled_self_improve(metadata, num_swe_issues=[1, 2]) is True


def test_is_compiled_self_improve_rejects_missing_required_keys():
    metadata = {
        "overall_performance": {
            "accuracy_score": 0.5,
            "total_unresolved_ids": ["issue_b"],
            "total_resolved_ids": ["issue_a"],
            "total_emptypatch_ids": [],
        }
    }

    assert is_compiled_self_improve(metadata) is False

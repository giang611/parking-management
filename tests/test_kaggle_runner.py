from pathlib import Path


def test_kaggle_runner_reserves_unique_run_directory():
    script = Path(__file__).resolve().parents[1] / "loadtest" / "kaggle_runner.sh"
    source = script.read_text(encoding="utf-8")

    assert 'RUN_DIR="$(mktemp -d "$RESULTS_ROOT/${RUN_TIMESTAMP}-XXXXXXXX")"' in source
    assert 'RUN_ID="${RUN_DIR##*/}"' in source

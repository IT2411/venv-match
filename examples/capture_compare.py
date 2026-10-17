"""Example: Capture, save, load, and compare two environment snapshots."""

from pathlib import Path
import tempfile

from venv_match import CaptureConfig, capture, compare, load_snapshot


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        baseline_path = Path(tmp_dir) / "baseline.json"

        # 1. Capture and save baseline snapshot
        baseline = capture(CaptureConfig(env_vars=("TZ", "LANG")))
        baseline.save(baseline_path)

        # 2. Load snapshot from disk and compare against a fresh capture
        loaded = load_snapshot(baseline_path)
        current = capture(CaptureConfig(env_vars=("TZ", "LANG")))

        report = compare(loaded, current)
        print("Has differences:", report.has_differences)
        print(report.summary())


if __name__ == "__main__":
    main()

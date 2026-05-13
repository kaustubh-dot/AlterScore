from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.ml.data_generation.artifacts import materialize_synthetic_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate AlterScore synthetic data and save a validation summary.",
    )
    parser.add_argument("--row-count", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dataset-path", type=Path, default=None)
    parser.add_argument("--validation-summary-path", type=Path, default=None)
    parser.add_argument("--minimum-test-rows", type=int, default=1_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = materialize_synthetic_dataset(
        row_count=args.row_count,
        seed=args.seed,
        dataset_path=args.dataset_path,
        validation_summary_path=args.validation_summary_path,
        minimum_test_rows=args.minimum_test_rows,
    )
    print(
        json.dumps(
            {
                "dataset_path": str(artifacts.dataset_path),
                "validation_summary_path": str(artifacts.validation_summary_path),
                "row_count": artifacts.validation_summary["row_count"],
                "default_rate": artifacts.validation_summary["default_rate"],
                "months_11_12_rows": artifacts.validation_summary["months_11_12_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

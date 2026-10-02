from __future__ import annotations

import os
from pathlib import Path
import pytest

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from waypoint_optimizer.adapters.csv_adapter import ReferenceData, load_reference_data


REQUIRED_REAL_CSVS = (
    "outlets.csv",
    "vehicles.csv",
    "district_travel.csv",
    "service_allowance.csv",
    "calendar.csv",
    "traffic_speed.csv",
    "road_conditions.csv",
)


def resolve_real_data_dir() -> Path:
    """
    Locates the real data directory portably:
    - During development it may be beside the repository as ../data
    - Also supports ./data
    - Resolves the path relative to the test/repository location
    - Does not hardcode a Windows-only absolute path
    - Fails clearly if directory or required CSVs are missing
    - Never silently substitutes mock data
    """
    test_dir = Path(__file__).resolve().parent
    repo_root = test_dir.parent
    beside_repo = repo_root.parent / "data"

    candidates = [
        beside_repo,                # ../data relative to repo root
        repo_root / "data",         # ./data relative to repo root
        test_dir / "data",          # tests/data
        Path("data").resolve(),     # ./data relative to cwd
        Path("../data").resolve(),  # ../data relative to cwd
    ]

    for cand in candidates:
        if cand.is_dir() and (cand / "outlets.csv").is_file():
            missing = [f for f in REQUIRED_REAL_CSVS if not (cand / f).is_file()]
            if not missing:
                return cand.resolve()

    # If directory exists but missing some required CSVs, raise specific error
    for cand in candidates:
        if cand.is_dir():
            missing = [f for f in REQUIRED_REAL_CSVS if not (cand / f).is_file()]
            if missing:
                raise FileNotFoundError(
                    f"Data directory found at {cand}, but missing required CSV files: {missing}. "
                    "Do not silently substitute mock data."
                )

    searched_paths = "\n  - ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Real reference data directory not found.\n"
        f"Searched candidates:\n  - {searched_paths}\n"
        f"Required CSV files: {', '.join(REQUIRED_REAL_CSVS)}.\n"
        f"Do not silently substitute mock data."
    )


@pytest.fixture(scope="session")
def real_data_dir() -> Path:
    """Fixture returning the portable Path to the real reference data directory."""
    return resolve_real_data_dir()


@pytest.fixture(scope="session")
def real_reference_data(real_data_dir: Path) -> ReferenceData:
    """
    Authoritative reference data fixture loaded from real reference CSVs.

    Asserts that:
    1. Real data directory is portably resolved.
    2. Loaded via load_reference_data().
    3. Fails clearly if directory or CSVs are missing.
    4. Asserts expected records are loaded (>=100 outlets, >=50 vehicles,
       travel, allowances, calendar, traffic speed, road conditions).
    5. Does not silently substitute mock data.
    """
    ref = load_reference_data(real_data_dir)

    assert len(ref.outlets) >= 100, f"Expected >= 100 outlets, got {len(ref.outlets)}"
    assert len(ref.vehicles) >= 50, f"Expected >= 50 vehicles, got {len(ref.vehicles)}"
    assert len(ref.travel) >= 10, f"Expected >= 10 district travel rows, got {len(ref.travel)}"
    assert len(ref.allowances) >= 5, f"Expected >= 5 service allowances, got {len(ref.allowances)}"
    assert ref.calendar_rows is not None and len(ref.calendar_rows) > 0, (
        "calendar.csv must be loaded and non-empty in real reference data"
    )
    assert ref.traffic_speed_rows is not None and len(ref.traffic_speed_rows) > 0, (
        "traffic_speed.csv must be loaded and non-empty in real reference data"
    )
    assert ref.road_conditions_rows is not None and len(ref.road_conditions_rows) > 0, (
        "road_conditions.csv must be loaded and non-empty in real reference data"
    )

    return ref

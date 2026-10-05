import os
import json
import hashlib
import datetime
from pathlib import Path

REQUIRED_FILES = [
    ("General Data", "outlets.csv"),
    ("General Data", "vehicles.csv"),
    ("General Data", "calendar.csv"),
    ("General Data", "district_travel.csv"),
    ("General Data", "service_allowance.csv"),
    ("General Data", "traffic_speed.csv"),
    ("General Data", "road_conditions.csv"),
    ("Training Data", "deliveries_train.csv"),
    ("Training Data", "route_legs_train.csv"),
    ("Test Data", "task1_test_inputs.csv"),
    ("Test Data", "route_legs_test.csv"),
    ("Test Data", "task2a_test_inputs.csv"),
    ("Test Data", "task2b_peak_day_scenarios.csv"),
    ("Test Data", "task2b_peak_day_fleet.csv"),
    ("Submission Templates", "submission_task1.csv"),
    ("Submission Templates", "submission_task2a.csv"),
    ("Submission Templates", "submission_task2b.csv"),
    (".", "check_allocation.py"),
]

def calculate_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_valid_content(filepath: str) -> bool:
    """Check if file is non-empty and not an HTML error page."""
    path = Path(filepath)
    if not path.exists() or path.stat().st_size == 0:
        return False
    # Check first 512 bytes for HTML indicators
    with open(filepath, "rb") as f:
        head = f.read(512).lower()
        if b"<!doctype html" in head or b"<html" in head or b"404 not found" in head:
            return False
    return True

def generate_manifest(raw_data_dir: str, output_manifest_path: str) -> dict:
    raw_path = Path(raw_data_dir)
    manifest = {
        "retrieval_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "https://drive.google.com/drive/folders/13KBf2_QKZt9TJNtE3LiyT3Q0KLo7piVs",
        "files": {},
        "completeness_check": True,
        "missing_or_corrupt": []
    }

    for folder, fname in REQUIRED_FILES:
        rel_path = fname if folder == "." else os.path.join(folder, fname)
        full_path = raw_path / "data" / rel_path if folder != "." else raw_path / fname
        if not full_path.exists():
            # Check alternative path without 'data' subfolder
            alt_path = raw_path / rel_path
            if alt_path.exists():
                full_path = alt_path

        if not full_path.exists() or not is_valid_content(str(full_path)):
            manifest["completeness_check"] = False
            manifest["missing_or_corrupt"].append(rel_path)
            continue

        size_bytes = full_path.stat().st_size
        sha256 = calculate_sha256(str(full_path))
        manifest["files"][rel_path] = {
            "path": str(full_path.as_posix()),
            "size_bytes": size_bytes,
            "sha256": sha256,
            "status": "valid"
        }

    out_path = Path(output_manifest_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

if __name__ == "__main__":
    base = Path(__file__).resolve().parents[3]
    raw_dir = base / "data" / "raw"
    manifest_out = base / "data" / "manifest.json"
    res = generate_manifest(str(raw_dir), str(manifest_out))
    print(f"Manifest generated at {manifest_out}. Completeness: {res['completeness_check']}")

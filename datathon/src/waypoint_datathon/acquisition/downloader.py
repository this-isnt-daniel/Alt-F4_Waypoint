import os
import shutil
import zipfile
from pathlib import Path
from .manifest import generate_manifest

GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/13KBf2_QKZt9TJNtE3LiyT3Q0KLo7piVs"

def acquire_datasets(
    target_raw_dir: str,
    source_dir_or_zip: str | None = None,
    force_download: bool = False
) -> dict:
    target = Path(target_raw_dir)
    target.mkdir(parents=True, exist_ok=True)
    manifest_file = target.parent / "manifest.json"

    if source_dir_or_zip:
        src = Path(source_dir_or_zip)
        if src.is_file() and src.suffix.lower() == ".zip":
            print(f"Extracting local zip {src} into {target}...")
            with zipfile.ZipFile(src, "r") as zf:
                zf.extractall(target)
        elif src.is_dir():
            print(f"Copying local folder {src} into {target}...")
            for item in src.iterdir():
                dest = target / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            raise ValueError(f"Invalid source path: {source_dir_or_zip}")
    elif force_download or not (target / "data").exists():
        print(f"Downloading official datasets from Google Drive into {target}...")
        try:
            import gdown
            gdown.download_folder(GDRIVE_FOLDER_URL, output=str(target), quiet=False)
        except Exception as e:
            raise RuntimeError(f"Failed to download via gdown: {e}. Pass a local directory or ZIP to acquire_datasets.") from e

    manifest = generate_manifest(str(target), str(manifest_file))
    return manifest

if __name__ == "__main__":
    base = Path(__file__).resolve().parents[3]
    raw_dir = base / "data" / "raw"
    m = acquire_datasets(str(raw_dir))
    print(f"Data acquisition finished. Completeness: {m['completeness_check']}")

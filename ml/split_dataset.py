"""Build a stratified train/val/test manifest over training_data/Faulty_solar_panel.

Run once (or whenever the source images change) before train.py:
    python ml/split_dataset.py
"""
import json
from pathlib import Path

from sklearn.model_selection import train_test_split

SEED = 42
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "training_data" / "Faulty_solar_panel"
MANIFEST_PATH = Path(__file__).resolve().parent / "artifacts" / "split_manifest.json"


def collect_samples():
    classes = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir())
    samples = []
    for class_name in classes:
        for f in (DATA_DIR / class_name).iterdir():
            if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS:
                samples.append((str(f.relative_to(REPO_ROOT)), class_name))
    return classes, samples


def stratified_split(samples):
    paths = [s[0] for s in samples]
    labels = [s[1] for s in samples]

    train_val_paths, test_paths, train_val_labels, test_labels = train_test_split(
        paths, labels, test_size=TEST_FRACTION, stratify=labels, random_state=SEED,
    )
    val_size_within_train_val = VAL_FRACTION / (1.0 - TEST_FRACTION)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_val_paths, train_val_labels, test_size=val_size_within_train_val,
        stratify=train_val_labels, random_state=SEED,
    )

    return {
        "train": list(zip(train_paths, train_labels)),
        "val": list(zip(val_paths, val_labels)),
        "test": list(zip(test_paths, test_labels)),
    }


def main():
    classes, samples = collect_samples()
    split = stratified_split(samples)

    manifest = {
        "classes": classes,
        "train": [{"path": p, "label": l} for p, l in split["train"]],
        "val": [{"path": p, "label": l} for p, l in split["val"]],
        "test": [{"path": p, "label": l} for p, l in split["test"]],
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Classes ({len(classes)}): {classes}")
    print(f"{'split':<8}{'total':>8}  per-class counts")
    for split_name in ("train", "val", "test"):
        rows = manifest[split_name]
        counts = {c: sum(1 for r in rows if r["label"] == c) for c in classes}
        print(f"{split_name:<8}{len(rows):>8}  {counts}")
    print(f"\nManifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()

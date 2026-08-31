"""Bridge to the standalone ml/ training pipeline's trained classifier.

Adds the repo root to sys.path so the backend can import the ml package
directly, per the reusable seam documented in ml/predict.py.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.predict import predict_image  # noqa: E402

# Mirrors the (folder name -> taxonomy slug, severity) mapping in backend/seed.py's
# CLASSES table, so a live prediction lines up with the seeded taxonomy entries.
CLASS_TO_TAXONOMY = {
    "Clean": (None, "LOW"),
    "Bird-drop": ("bird_drop", "MEDIUM"),
    "Dusty": ("dusty", "LOW"),
    "Electrical-damage": ("electrical_damage", "HIGH"),
    "Physical-Damage": ("physical_damage", "HIGH"),
    "Snow-Covered": ("snow_covered", "MEDIUM"),
}


def classify(image_path):
    """Run the trained classifier and translate its output into CellMind's
    defect-probability / severity / taxonomy vocabulary.

    Raises FileNotFoundError if artifacts/best_model.pt hasn't been trained yet,
    and whatever PIL raises (e.g. UnidentifiedImageError) for an unreadable image.
    """
    prediction = predict_image(image_path)
    taxonomy_id, severity = CLASS_TO_TAXONOMY.get(prediction["label"], (None, "LOW"))
    clean_prob = prediction["probs"].get("Clean", 0.0)
    return {
        "label": prediction["label"],
        "confidence": prediction["confidence"],
        "probs": prediction["probs"],
        "taxonomyId": taxonomy_id,
        "severity": severity,
        "defectProbability": round(1 - clean_prob, 4),
    }

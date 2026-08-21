"""Load the trained solar-panel fault classifier and run inference on an image.

Usage:
    python ml/predict.py path/to/image.jpg

Reusable seam for later backend integration:
    from ml.predict import predict_image
    result = predict_image("some/photo.jpg")
"""
import json
import sys
from pathlib import Path

import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "best_model.pt"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

_model = None
_classes = None
_transform = None


def _load():
    global _model, _classes, _transform
    if _model is not None:
        return

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"{MODEL_PATH} not found. Run `python ml/train.py` first.")

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    classes = checkpoint["classes"]
    image_size = checkpoint["image_size"]

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    _model = model
    _classes = classes
    _transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def predict_image(image_path):
    _load()
    image = Image.open(image_path).convert("RGB")
    tensor = _transform(image).unsqueeze(0)

    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)

    best_idx = int(probs.argmax())
    return {
        "label": _classes[best_idx],
        "confidence": float(probs[best_idx]),
        "probs": {c: float(p) for c, p in zip(_classes, probs.tolist())},
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ml/predict.py <image_path>")
        sys.exit(1)

    result = predict_image(sys.argv[1])
    print(json.dumps(result, indent=2))

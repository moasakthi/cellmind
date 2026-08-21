"""Fine-tune a ResNet18 (ImageNet-pretrained) on training_data/Faulty_solar_panel.

Two-phase transfer learning:
  Phase A: backbone frozen, train only the replaced FC head.
  Phase B: full network unfrozen, fine-tuned at a lower LR with cosine decay
           and early stopping on validation macro-F1.

Usage:
    python ml/split_dataset.py   # once, to build the manifest
    python ml/train.py
"""
import json
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score

SEED = 42
IMAGE_SIZE = 224
BATCH_SIZE = 32
HEAD_EPOCHS = 5
FINETUNE_EPOCHS = 20
EARLY_STOP_PATIENCE = 5
HEAD_LR = 1e-3
FINETUNE_LR = 1e-4

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MANIFEST_PATH = ARTIFACTS_DIR / "split_manifest.json"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.RandomCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


class ManifestImageDataset(Dataset):
    def __init__(self, rows, class_to_idx, transform):
        self.rows = rows
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        image = Image.open(REPO_ROOT / row["path"]).convert("RGB")
        image = self.transform(image)
        label = self.class_to_idx[row["label"]]
        return image, label


def load_manifest():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"{MANIFEST_PATH} not found. Run `python ml/split_dataset.py` first."
        )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def build_model(num_classes):
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def class_weights_tensor(train_rows, classes):
    counts = {c: 0 for c in classes}
    for row in train_rows:
        counts[row["label"]] += 1
    total = len(train_rows)
    n_classes = len(classes)
    weights = [total / (n_classes * counts[c]) for c in classes]
    return torch.tensor(weights, dtype=torch.float32)


def run_epoch(model, loader, criterion, optimizer, device):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    all_preds, all_labels = [], []

    with torch.set_grad_enabled(training):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            all_preds.extend(outputs.argmax(dim=1).tolist())
            all_labels.extend(labels.tolist())

    avg_loss = total_loss / len(loader.dataset)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    return avg_loss, macro_f1


def train_phase(model, train_loader, val_loader, criterion, optimizer, scheduler,
                 epochs, device, phase_name, best_state):
    for epoch in range(1, epochs + 1):
        train_loss, train_f1 = run_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_f1 = run_epoch(model, val_loader, criterion, None, device)
        if scheduler is not None:
            scheduler.step()

        improved = val_f1 > best_state["val_f1"]
        marker = " *" if improved else ""
        print(f"[{phase_name}] epoch {epoch}/{epochs} "
              f"train_loss={train_loss:.4f} train_f1={train_f1:.4f} "
              f"val_loss={val_loss:.4f} val_f1={val_f1:.4f}{marker}")

        if improved:
            best_state["val_f1"] = val_f1
            best_state["state_dict"] = {k: v.clone() for k, v in model.state_dict().items()}
            best_state["patience_used"] = 0
        else:
            best_state["patience_used"] += 1
            if best_state["patience_used"] >= EARLY_STOP_PATIENCE:
                print(f"[{phase_name}] early stopping (no val_f1 improvement for "
                      f"{EARLY_STOP_PATIENCE} epochs)")
                break


def evaluate_on_test(model, test_loader, classes, device):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            all_preds.extend(outputs.argmax(dim=1).tolist())
            all_labels.extend(labels.tolist())

    report = classification_report(
        all_labels, all_preds, target_names=classes, output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(all_labels, all_preds).tolist()
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "classification_report": report,
        "confusion_matrix": cm,
        "confusion_matrix_labels": classes,
    }


def main():
    torch.manual_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    manifest = load_manifest()
    classes = manifest["classes"]
    class_to_idx = {c: i for i, c in enumerate(classes)}

    train_ds = ManifestImageDataset(manifest["train"], class_to_idx, train_transform)
    val_ds = ManifestImageDataset(manifest["val"], class_to_idx, eval_transform)
    test_ds = ManifestImageDataset(manifest["test"], class_to_idx, eval_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = build_model(len(classes)).to(device)
    weights = class_weights_tensor(manifest["train"], classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)

    best_state = {"val_f1": -1.0, "state_dict": None, "patience_used": 0}

    # Phase A: warm up the head only.
    for param in model.parameters():
        param.requires_grad = False
    for param in model.fc.parameters():
        param.requires_grad = True
    head_optimizer = optim.Adam(model.fc.parameters(), lr=HEAD_LR)
    train_phase(model, train_loader, val_loader, criterion, head_optimizer, None,
                HEAD_EPOCHS, device, "phase A (head warmup)", best_state)

    # Phase B: fine-tune the full network.
    for param in model.parameters():
        param.requires_grad = True
    finetune_optimizer = optim.Adam(model.parameters(), lr=FINETUNE_LR)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(finetune_optimizer, T_max=FINETUNE_EPOCHS)
    best_state["patience_used"] = 0
    train_phase(model, train_loader, val_loader, criterion, finetune_optimizer, scheduler,
                FINETUNE_EPOCHS, device, "phase B (fine-tune)", best_state)

    print(f"\nBest validation macro-F1: {best_state['val_f1']:.4f}")
    model.load_state_dict(best_state["state_dict"])

    metrics = evaluate_on_test(model, test_loader, classes, device)
    print(f"Test accuracy: {metrics['accuracy']:.4f}  Test macro-F1: {metrics['macro_f1']:.4f}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model_state": model.state_dict(),
        "classes": classes,
        "image_size": IMAGE_SIZE,
        "arch": "resnet18",
    }, ARTIFACTS_DIR / "best_model.pt")

    (ARTIFACTS_DIR / "label_map.json").write_text(
        json.dumps({str(i): c for i, c in enumerate(classes)}, indent=2), encoding="utf-8",
    )
    (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"\nArtifacts written to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()

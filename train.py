import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import models, datasets, transforms
from torch.utils.data import DataLoader
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import time
import copy

# CONFIG 

DATASET_DIR    = "./dataset"
CHECKPOINT_DIR = "./checkpoints"
IMAGE_SIZE     = 224
BATCH_SIZE     = 32

# Phase 1 — train only the classifier head
PHASE1_EPOCHS  = 5
PHASE1_LR      = 1e-3

# Phase 2 — fine-tune the whole network
PHASE2_EPOCHS  = 20
PHASE2_LR      = 1e-4

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#  DATA 

def get_dataloaders():
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    train_ds = datasets.ImageFolder(Path(DATASET_DIR) / "train", transform=train_transform)
    val_ds   = datasets.ImageFolder(Path(DATASET_DIR) / "val",   transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=4, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=4, pin_memory=True)

    return train_loader, val_loader, train_ds.classes


# MODEL 

def build_model(num_classes: int):
    """
    ResNet50 pretrained on ImageNet.
    We replace the final fully-connected layer so output = num_classes.
    """
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Freeze ALL layers first (we unfreeze in Phase 2)
    for param in model.parameters():
        param.requires_grad = False

    # Replace final layer — only THIS layer trains in Phase 1
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(in_features, num_classes)
    )

    return model.to(DEVICE)


# TRAINING LOOP

def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total   += labels.size(0)

    return running_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        outputs = model(images)
        loss    = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total   += labels.size(0)

    return running_loss / total, correct / total


def run_phase(model, train_loader, val_loader,
              num_epochs, lr, phase_name, best_acc, best_weights):
    """Generic training phase — returns updated best_acc and best_weights."""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr, weight_decay=1e-4
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    print(f"\n{'='*55}")
    print(f"  {phase_name}  (device: {DEVICE})")
    print(f"{'='*55}")

    for epoch in range(1, num_epochs + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss,   val_acc   = evaluate(model, val_loader, criterion)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"  Epoch {epoch:>3}/{num_epochs}  "
              f"train_loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
              f"val_loss={val_loss:.4f}  val_acc={val_acc:.3f}  "
              f"({elapsed:.1f}s)")

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        # Save best model
        if val_acc > best_acc:
            best_acc     = val_acc
            best_weights = copy.deepcopy(model.state_dict())
            ckpt_path    = Path(CHECKPOINT_DIR) / "best_model.pth"
            torch.save({
                "epoch"      : epoch,
                "model_state": best_weights,
                "val_acc"    : best_acc,
                "classes"    : class_names,   # saved globally below
            }, ckpt_path)
            print(f"    💾 Best model saved (val_acc={best_acc:.3f})")

    return best_acc, best_weights, history


# PLOTTING 

def plot_history(h1, h2):
    """Combine Phase 1 + Phase 2 history and plot curves."""
    tl = h1["train_loss"] + h2["train_loss"]
    vl = h1["val_loss"]   + h2["val_loss"]
    ta = h1["train_acc"]  + h2["train_acc"]
    va = h1["val_acc"]    + h2["val_acc"]
    ep = list(range(1, len(tl) + 1))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(ep, tl, label="Train Loss")
    ax1.plot(ep, vl, label="Val Loss")
    ax1.axvline(PHASE1_EPOCHS + 0.5, color="gray", linestyle="--", label="Phase 2 start")
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Loss")
    ax1.set_title("Loss"); ax1.legend()

    ax2.plot(ep, ta, label="Train Acc")
    ax2.plot(ep, va, label="Val Acc")
    ax2.axvline(PHASE1_EPOCHS + 0.5, color="gray", linestyle="--", label="Phase 2 start")
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Accuracy")
    ax2.set_title("Accuracy"); ax2.legend()

    plt.suptitle("Training History", fontsize=14)
    plt.tight_layout()
    plt.savefig("training_curves.png", dpi=100)
    plt.show()
    print("Training curves saved to 'training_curves.png'")


# MAIN 

if __name__ == "__main__":
    Path(CHECKPOINT_DIR).mkdir(exist_ok=True)

    print(f"Using device: {DEVICE}")
    if DEVICE.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Load data
    train_loader, val_loader, class_names = get_dataloaders()
    num_classes = len(class_names)
    print(f"\nClasses ({num_classes}): {class_names}")

    # Build model
    model = build_model(num_classes)
    print(f"\nModel: ResNet50 (pretrained) → {num_classes} classes")

    best_acc     = 0.0
    best_weights = None

    # Phase 1: train only the new head 
    best_acc, best_weights, h1 = run_phase(
        model, train_loader, val_loader,
        num_epochs=PHASE1_EPOCHS, lr=PHASE1_LR,
        phase_name="Phase 1 — Training classifier head only",
        best_acc=best_acc, best_weights=best_weights
    )

    # Phase 2: unfreeze all layers and fine-tune
    print("\nUnfreezing all layers for fine-tuning...")
    for param in model.parameters():
        param.requires_grad = True

    best_acc, best_weights, h2 = run_phase(
        model, train_loader, val_loader,
        num_epochs=PHASE2_EPOCHS, lr=PHASE2_LR,
        phase_name="Phase 2 — Fine-tuning entire network",
        best_acc=best_acc, best_weights=best_weights
    )

    print(f"\n✅ Training complete!  Best val accuracy: {best_acc:.3f}")
    print(f"   Checkpoint saved to '{CHECKPOINT_DIR}/best_model.pth'")

    # Plot
    plot_history(h1, h2)

    print("\n   Next step → run  step3_inference.py")
import os
import copy
import random
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
from PIL import Image


CHECKPOINT_IN  = "./checkpoints/best_model.pth"
CHECKPOINT_OUT = "./checkpoints/best_model_32.pth"

PARIKAR_ROOT   = "./parikar"
PARIKAR_CLASSES = {
    "burger":   "Burger",
    "dal_bhat": "Dalbhat",
    "kheer":    "Kheer",
    "sel_roti": "Selroti",
}
NEW_CLASSES = list(PARIKAR_CLASSES.keys())

TRAIN_RATIO  = 0.70
VAL_RATIO    = 0.15
IMAGE_SIZE   = 224
BATCH_SIZE   = 16
EPOCHS       = 25
LR           = 1e-4

DISTILL_TEMP   = 4.0
DISTILL_ALPHA  = 0.7

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ParikarDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples   = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


def get_transforms():
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    return train_tf, val_tf


def build_parikar_loaders(new_class_indices: dict):
    train_samples, val_samples = [], []

    for cls_key, folder_name in PARIKAR_CLASSES.items():
        cls_dir = Path(PARIKAR_ROOT) / folder_name
        if not cls_dir.exists():
            raise FileNotFoundError(f"Parikar folder not found: {cls_dir}")

        images = (list(cls_dir.glob("*.jpg")) +
                  list(cls_dir.glob("*.jpeg")) +
                  list(cls_dir.glob("*.png")))

        if len(images) == 0:
            raise ValueError(f"No images found in {cls_dir}")

        random.shuffle(images)
        label   = new_class_indices[cls_key]
        n_train = int(len(images) * TRAIN_RATIO)
        n_val   = int(len(images) * VAL_RATIO)

        for p in images[:n_train]:
            train_samples.append((p, label))
        for p in images[n_train: n_train + n_val]:
            val_samples.append((p, label))

        print(f"   {cls_key:15s}  total={len(images)}  "
              f"train={n_train}  val={n_val}")

    train_tf, val_tf = get_transforms()
    train_loader = DataLoader(ParikarDataset(train_samples, train_tf),
                              batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader   = DataLoader(ParikarDataset(val_samples, val_tf),
                              batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    return train_loader, val_loader


def build_teacher(checkpoint_path: str):
    ckpt        = torch.load(checkpoint_path, map_location=DEVICE)
    old_classes = ckpt["classes"]
    num_old     = len(old_classes)

    teacher = models.resnet50(weights=None)
    teacher.fc = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(teacher.fc.in_features, num_old)
    )
    teacher.load_state_dict(ckpt["model_state"])
    teacher.to(DEVICE).eval()

    for param in teacher.parameters():
        param.requires_grad = False

    print(f"   Teacher loaded: {num_old} classes, val_acc={ckpt['val_acc']:.3f}")
    return teacher, old_classes


def build_student(checkpoint_path: str, new_classes: list):
    ckpt        = torch.load(checkpoint_path, map_location=DEVICE)
    old_classes = ckpt["classes"]
    num_old     = len(old_classes)
    num_total   = num_old + len(new_classes)
    all_classes = old_classes + new_classes

    student = models.resnet50(weights=None)
    student.fc = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(student.fc.in_features, num_old)
    )
    student.load_state_dict(ckpt["model_state"])

    old_fc      = student.fc[1]
    in_features = old_fc.in_features
    new_fc      = nn.Linear(in_features, num_total)

    with torch.no_grad():
        new_fc.weight[:num_old] = old_fc.weight
        new_fc.bias[:num_old]   = old_fc.bias 

    student.fc = nn.Sequential(nn.Dropout(0.4), new_fc)

    for name, param in student.named_parameters():
        param.requires_grad = "fc" in name

    student.to(DEVICE)
    return student, all_classes


def distillation_loss(student_logits, teacher_logits, labels, num_old, alpha, temp):
    ce_loss = F.cross_entropy(student_logits, labels)

    student_old = student_logits[:, :num_old] / temp
    teacher_old = teacher_logits / temp

    kd_loss = F.kl_div(
        F.log_softmax(student_old, dim=1),
        F.softmax(teacher_old, dim=1),
        reduction="batchmean"
    ) * (temp ** 2)

    return (1 - alpha) * ce_loss + alpha * kd_loss


def train_one_epoch(student, teacher, loader, optimizer, num_old):
    student.train()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        student_logits = student(images)

        with torch.no_grad():
            teacher_logits = teacher(images)

        loss = distillation_loss(
            student_logits, teacher_logits, labels,
            num_old, DISTILL_ALPHA, DISTILL_TEMP
        )
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        correct    += student_logits.argmax(1).eq(labels).sum().item()
        total      += labels.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(student, loader):
    student.eval()
    correct, total = 0, 0
    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        correct += student(images).argmax(1).eq(labels).sum().item()
        total   += labels.size(0)
    return correct / total


if __name__ == "__main__":
    random.seed(42)
    torch.manual_seed(42)

    print("=" * 55)
    print("  Expanding model with knowledge distillation")
    print("=" * 55)
    print(f"  Device       : {DEVICE}")
    print(f"  Distill temp : {DISTILL_TEMP}")
    print(f"  Distill alpha: {DISTILL_ALPHA}")

    print("\n  Loading teacher model...")
    teacher, old_classes = build_teacher(CHECKPOINT_IN)
    num_old = len(old_classes)

    print("\n  Building student model...")
    student, all_classes = build_student(CHECKPOINT_IN, NEW_CLASSES)
    new_class_indices = {cls: all_classes.index(cls) for cls in NEW_CLASSES}
    print(f"   Student classes: {len(all_classes)}")
    print(f"   New indices    : {new_class_indices}")

    print("\n  Loading parikar images...")
    train_loader, val_loader = build_parikar_loaders(new_class_indices)

    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, student.parameters()),
        lr=LR, weight_decay=1e-4
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_acc     = 0.0
    best_weights = None

    print(f"\n  Training for {EPOCHS} epochs...\n")
    print("=" * 55)

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(student, teacher, train_loader, optimizer, num_old)
        val_acc = evaluate(student, val_loader)
        scheduler.step()
        elapsed = time.time() - t0

        print(f"  Epoch {epoch:>3}/{EPOCHS}  "
              f"train_loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
              f"val_acc={val_acc:.3f}  ({elapsed:.1f}s)")

        if val_acc > best_acc:
            best_acc     = val_acc
            best_weights = copy.deepcopy(student.state_dict())
            print(f"    💾 Best model saved (val_acc={best_acc:.3f})")

    Path("checkpoints").mkdir(exist_ok=True)
    torch.save({
        "model_state": best_weights,
        "classes":     all_classes,
        "val_acc":     best_acc,
    }, CHECKPOINT_OUT)

    print(f"\n{'='*55}")
    print(f"  ✅ Done! Best val_acc={best_acc:.3f}")
    print(f"  Total classes: {len(all_classes)}")
    print(f"  Classes: {all_classes}")

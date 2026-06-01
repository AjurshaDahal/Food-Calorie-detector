import os
import shutil
import random
from pathlib import Path

import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import numpy as np

FOOD101_ROOT = "./food-101"


OUTPUT_DIR   = "./dataset"

# Full list: https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/
SELECTED_CLASSES = [
    "pizza", "hot_dog", "french_fries", "fried_rice",
    "sushi", "ramen", "pad_thai", "dumplings", "spring_rolls",
    "grilled_salmon", "chicken_curry", "bibimbap", "pho", "tacos",
    "nachos", "waffles", "pancakes", "omelette",
    "caesar_salad", "greek_salad", "chocolate_cake", "cheesecake", "ice_cream",
    "donuts", "apple_pie", "strawberry_shortcake", "miso_soup", "edamame"
]

TRAIN_RATIO = 0.70   
VAL_RATIO   = 0.15   
TEST_RATIO  = 0.15   

IMAGE_SIZE  = 224    # ResNet/EfficientNet standard input size
BATCH_SIZE  = 32


def build_split_folders():
    """
    Copies images from Food-101 into a clean train/val/test structure.
    Output:
        dataset/train/pizza/...
        dataset/val/pizza/...
        dataset/test/pizza/...
    """
    src_images = Path(FOOD101_ROOT) / "images"

    if not src_images.exists():
        raise FileNotFoundError(
            f"Could not find {src_images}. "
            "Make sure FOOD101_ROOT points to the extracted food-101 folder."
        )

    print(f"Found source images at: {src_images}")
    print(f"Building dataset with {len(SELECTED_CLASSES)} classes...\n")

    for split in ["train", "val", "test"]:
        for cls in SELECTED_CLASSES:
            (Path(OUTPUT_DIR) / split / cls).mkdir(parents=True, exist_ok=True)

    for cls in SELECTED_CLASSES:
        cls_src = src_images / cls
        if not cls_src.exists():
            print(f"    Class '{cls}' not found in dataset, skipping.")
            continue

        images = list(cls_src.glob("*.jpg"))
        random.shuffle(images)

        n       = len(images)
        n_train = int(n * TRAIN_RATIO)
        n_val   = int(n * VAL_RATIO)

        splits = {
            "train": images[:n_train],
            "val"  : images[n_train : n_train + n_val],
            "test" : images[n_train + n_val :]
        }

        for split, files in splits.items():
            dst_dir = Path(OUTPUT_DIR) / split / cls
            for f in files:
                shutil.copy(f, dst_dir / f.name)

        print(f"   {cls:25s}  train={len(splits['train'])}  "
              f"val={len(splits['val'])}  test={len(splits['test'])}")

    print(f"\nDataset saved to '{OUTPUT_DIR}/'")


def get_transforms():
 
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE),   # random zoom + crop
        transforms.RandomHorizontalFlip(),           # flip left/right
        transforms.ColorJitter(                      # vary brightness/contrast
            brightness=0.3, contrast=0.3,
            saturation=0.3, hue=0.05
        ),
        transforms.RandomRotation(15),              # slight rotation
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    return train_transform, val_transform


def get_dataloaders():
    train_tf, val_tf = get_transforms()

    train_ds = datasets.ImageFolder(Path(OUTPUT_DIR) / "train", transform=train_tf)
    val_ds   = datasets.ImageFolder(Path(OUTPUT_DIR) / "val",   transform=val_tf)
    test_ds  = datasets.ImageFolder(Path(OUTPUT_DIR) / "test",  transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=4, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=4, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=4, pin_memory=True)

    print(f"\nDataLoader summary:")
    print(f"  Classes  : {len(train_ds.classes)}")
    print(f"  Train    : {len(train_ds)} images")
    print(f"  Val      : {len(val_ds)} images")
    print(f"  Test     : {len(test_ds)} images")

    return train_loader, val_loader, test_loader, train_ds.classes


def show_samples(loader, classes, n=16):
    """Plot a grid of sample images so you can verify loading is correct."""
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3,1,1)
    std  = torch.tensor([0.229, 0.224, 0.225]).view(3,1,1)

    images, labels = next(iter(loader))
    images = images[:n]
    labels = labels[:n]

    # un-normalize for display
    images = images * std + mean
    images = images.clamp(0, 1)

    fig, axes = plt.subplots(4, 4, figsize=(12, 12))
    for i, ax in enumerate(axes.flat):
        img = images[i].permute(1, 2, 0).numpy()
        ax.imshow(img)
        ax.set_title(classes[labels[i]], fontsize=9)
        ax.axis("off")
    plt.suptitle("Sample training images — verify these look correct!", fontsize=13)
    plt.tight_layout()
    plt.savefig("sample_images.png", dpi=100)
    plt.show()
    print("Sample image grid saved to 'sample_images.png'")


if __name__ == "__main__":
    random.seed(42)

    print("=" * 55)
    print("  STEP 1 — Prepare Dataset")
    print("=" * 55)

    # 1. Build folders
    build_split_folders()

    # 2. Create loaders
    train_loader, val_loader, test_loader, classes = get_dataloaders()

    # 3. Show samples
    print("\nGenerating sample image grid...")
    show_samples(train_loader, classes)

    print(" Data preparation complete!")

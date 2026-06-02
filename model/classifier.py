"""
Food Classifier Module
=======================
Wraps the ResNet50 model from the project's checkpoint into a clean
class that app.py can use for image analysis.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import os

from model.calorie_db import (
    get_food_info,
    calculate_total_calories,
    get_all_foods,
    FOOD_DESCRIPTIONS,
)

CHECKPOINT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "checkpoints", "best_model_32.pth"
)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Confidence threshold — below this we say "not recognized"
CONFIDENCE_THRESHOLD = 15.0


class FoodClassifier:
    """
    Loads the trained ResNet50 checkpoint and provides a .predict() method
    that returns the JSON structure the BhojanLens frontend expects.
    """

    def __init__(self):
        self.device = DEVICE
        self.model = None
        self.class_names = []
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225]),
        ])

        self._load_model()

    def _load_model(self):
        """Load the ResNet50 checkpoint."""
        if not os.path.exists(CHECKPOINT_PATH):
            print(f"[WARN] Checkpoint not found at {CHECKPOINT_PATH}")
            print("       The classifier will return dummy predictions.")
            print("       Train the model first with:  python train.py")
            return

        ckpt = torch.load(CHECKPOINT_PATH, map_location=self.device)
        self.class_names = ckpt["classes"]
        num_classes = len(self.class_names)

        self.model = models.resnet50(weights=None)
        self.model.fc = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(self.model.fc.in_features, num_classes),
        )
        self.model.load_state_dict(ckpt["model_state"])
        self.model.to(self.device).eval()

        val_acc = ckpt.get("val_acc", 0)
        print(f"[OK] ResNet50 loaded — {num_classes} classes, "
              f"val_acc={val_acc:.3f}, device={self.device}")

    @torch.no_grad()
    def predict(self, image_path: str, item_count: int = None) -> dict:
        """
        Classify a food image and return nutrition data.

        Returns a dict matching the JSON contract expected by app.js:
        {
            success, detected, confidence, model_used,
            nutrition: { food_name, description, serving_size,
                         total_calories, calories_per_unit, count,
                         protein_g, carbs_g, fat_g, fiber_g },
            top_predictions: [ { class, confidence } ],
            note
        }
        """
        count = max(int(item_count), 1) if item_count else 1

        # If model not loaded, return graceful error
        if self.model is None:
            return {
                "success": True,
                "detected": False,
                "message": "Model checkpoint not found. Please train the model first.",
                "suggestion": "Run `python train.py` to train the ResNet50 model.",
                "top_predictions": [],
            }

        # Load and preprocess the image
        try:
            pil_img = Image.open(image_path).convert("RGB")
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not open image: {str(e)}",
            }

        tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        probs = F.softmax(self.model(tensor), dim=1)[0]
        top_p, top_i = probs.topk(5)

        best_food = self.class_names[top_i[0].item()]
        best_conf = round(top_p[0].item() * 100, 1)

        # Build top predictions list
        top_predictions = []
        for p, i in zip(top_p.cpu().tolist(), top_i.cpu().tolist()):
            food_name = self.class_names[i]
            top_predictions.append({
                "class": food_name.replace("_", " ").title(),
                "confidence": round(p * 100, 1),
            })

        # Check confidence threshold
        if best_conf < CONFIDENCE_THRESHOLD:
            return {
                "success": True,
                "detected": False,
                "message": "Could not confidently identify this food item.",
                "suggestion": "Try a clearer photo with better lighting, "
                              "or ensure the food is one of our 28 supported categories.",
                "top_predictions": top_predictions,
            }

        # Get nutrition data
        nutrition = calculate_total_calories(best_food, count)
        if nutrition is None:
            nutrition = {
                "food_name": best_food.replace("_", " ").title(),
                "description": FOOD_DESCRIPTIONS.get(best_food, "Delicious food item"),
                "serving_size": "unknown",
                "total_calories": 0,
                "calories_per_unit": 0,
                "count": count,
                "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0,
            }

        return {
            "success": True,
            "detected": True,
            "confidence": best_conf,
            "model_used": "ResNet50 (Food-101)",
            "nutrition": nutrition,
            "top_predictions": top_predictions,
            "note": "Calorie estimation is approximate and may vary based on "
                    "portion size, preparation method, and ingredients.",
        }

    def get_supported_foods(self) -> list[dict]:
        """Return all foods from the nutrition database for the food grid."""
        return get_all_foods()

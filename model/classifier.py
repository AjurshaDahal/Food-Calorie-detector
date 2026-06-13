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

CONFIDENCE_THRESHOLD = 15.0


class FoodClassifier:

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
    def predict(self, image_path: str, portion_type: str = "grams", portion_value: int = None) -> dict:
        val = max(int(portion_value), 1) if portion_value else None

        if self.model is None:
            return {
                "success": True,
                "detected": False,
                "message": "Model checkpoint not found. Please train the model first.",
                "suggestion": "Run `python train.py` to train the ResNet50 model.",
                "top_predictions": [],
            }

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

        top_predictions = []
        for p, i in zip(top_p.cpu().tolist(), top_i.cpu().tolist()):
            food_name = self.class_names[i]
            top_predictions.append({
                "class": food_name.replace("_", " ").title(),
                "confidence": round(p * 100, 1),
            })

        if best_conf < CONFIDENCE_THRESHOLD:
            return {
                "success": True,
                "detected": False,
                "message": "Could not confidently identify this food item.",
                "suggestion": "Try a clearer photo with better lighting, "
                              "or ensure the food is one of our 28 supported categories.",
                "top_predictions": top_predictions,
            }

        nutrition = calculate_total_calories(best_food, portion_type, val)
        if nutrition is None:
            v = val if val else (100 if portion_type == "grams" else 1)
            nutrition = {
                "food_name": best_food.replace("_", " ").title(),
                "description": FOOD_DESCRIPTIONS.get(best_food, "Delicious food item"),
                "serving_size": f"{v}g" if portion_type == "grams" else f"{v} item(s)",
                "total_calories": 0,
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
        return get_all_foods()

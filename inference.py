import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import argparse
from pathlib import Path

# NUTRITION DATABASE
# All values per 100g (USDA FoodData Central)
NUTRITION_DB = {
    "pizza":                {"calories":266,"protein":11.0,"carbs":33.0,"fat":10.0,"fiber":2.2,"sugar":3.6,"sodium":598},
    "hot_dog":              {"calories":290,"protein":11.0,"carbs":22.0,"fat":18.0,"fiber":0.9,"sugar":4.0,"sodium":690},
    "french_fries":         {"calories":312,"protein":3.4, "carbs":41.0,"fat":15.0,"fiber":3.8,"sugar":0.3,"sodium":210},
    "fried_rice":           {"calories":163,"protein":4.4, "carbs":26.0,"fat":4.8, "fiber":1.0,"sugar":0.8,"sodium":450},
    "sushi":                {"calories":143,"protein":6.0, "carbs":27.0,"fat":1.0, "fiber":0.6,"sugar":2.0,"sodium":320},
    "ramen":                {"calories":95, "protein":5.0, "carbs":13.0,"fat":2.5, "fiber":0.8,"sugar":1.2,"sodium":580},
    "pad_thai":             {"calories":181,"protein":8.0, "carbs":25.0,"fat":5.5, "fiber":1.5,"sugar":4.0,"sodium":520},
    "dumplings":            {"calories":223,"protein":9.0, "carbs":28.0,"fat":8.5, "fiber":1.2,"sugar":1.5,"sodium":470},
    "spring_rolls":         {"calories":165,"protein":5.0, "carbs":22.0,"fat":6.5, "fiber":1.8,"sugar":2.0,"sodium":380},
    "grilled_salmon":       {"calories":208,"protein":28.0,"carbs":0.0, "fat":10.0,"fiber":0.0,"sugar":0.0,"sodium":190},
    "chicken_curry":        {"calories":150,"protein":12.0,"carbs":8.0, "fat":8.0, "fiber":1.5,"sugar":3.0,"sodium":420},
    "bibimbap":             {"calories":131,"protein":7.0, "carbs":18.0,"fat":3.5, "fiber":2.0,"sugar":2.5,"sodium":380},
    "pho":                  {"calories":55, "protein":4.5, "carbs":7.0, "fat":1.0, "fiber":0.5,"sugar":1.0,"sodium":410},
    "tacos":                {"calories":218,"protein":9.0, "carbs":23.0,"fat":10.0,"fiber":2.5,"sugar":2.0,"sodium":480},
    "nachos":               {"calories":346,"protein":8.0, "carbs":40.0,"fat":18.0,"fiber":3.5,"sugar":1.5,"sodium":560},
    "waffles":              {"calories":291,"protein":7.0, "carbs":41.0,"fat":11.0,"fiber":1.5,"sugar":8.0,"sodium":490},
    "pancakes":             {"calories":227,"protein":6.0, "carbs":35.0,"fat":7.5, "fiber":1.2,"sugar":9.0,"sodium":440},
    "omelette":             {"calories":154,"protein":11.0,"carbs":1.5, "fat":12.0,"fiber":0.0,"sugar":0.8,"sodium":340},
    "caesar_salad":         {"calories":158,"protein":5.0, "carbs":8.0, "fat":12.0,"fiber":1.5,"sugar":1.5,"sodium":380},
    "greek_salad":          {"calories":75, "protein":3.5, "carbs":6.0, "fat":4.5, "fiber":1.8,"sugar":4.0,"sodium":310},
    "chocolate_cake":       {"calories":371,"protein":5.0, "carbs":52.0,"fat":16.0,"fiber":2.5,"sugar":36.0,"sodium":340},
    "cheesecake":           {"calories":321,"protein":6.0, "carbs":32.0,"fat":19.0,"fiber":0.5,"sugar":22.0,"sodium":280},
    "ice_cream":            {"calories":207,"protein":3.5, "carbs":24.0,"fat":11.0,"fiber":0.0,"sugar":21.0,"sodium":80},
    "donuts":               {"calories":452,"protein":5.0, "carbs":51.0,"fat":25.0,"fiber":1.5,"sugar":20.0,"sodium":370},
    "apple_pie":            {"calories":237,"protein":2.5, "carbs":34.0,"fat":11.0,"fiber":1.5,"sugar":13.0,"sodium":270},
    "strawberry_shortcake": {"calories":280,"protein":4.5, "carbs":40.0,"fat":12.0,"fiber":1.0,"sugar":22.0,"sodium":240},
    "miso_soup":            {"calories":40, "protein":3.0, "carbs":4.5, "fat":1.0, "fiber":0.8,"sugar":1.0,"sodium":630},
    "edamame":              {"calories":122,"protein":11.0,"carbs":9.0, "fat":5.0, "fiber":5.0,"sugar":2.0,"sodium":6},
    "burger":               {"calories":295,"protein":17.0,"carbs":24.0,"fat":14.0,"fiber":1.5,"sugar":5.0,"sodium":510},
    "dal_bhat":              {"calories":130,"protein":5.0, "carbs":25.0,"fat":1.5, "fiber":3.0,"sugar":1.0,"sodium":280},
    "kheer":                {"calories":150,"protein":4.0, "carbs":28.0,"fat":3.5, "fiber":0.2,"sugar":20.0,"sodium":60},
    "sel_roti":              {"calories":320,"protein":4.5, "carbs":52.0,"fat":10.0,"fiber":1.0,"sugar":8.0,"sodium":180},

}

DEFAULT_SERVING_G = {
    "pizza":107,"hot_dog":98,"french_fries":117,"fried_rice":200,
    "sushi":150,"ramen":430,"pad_thai":300,"dumplings":100,
    "spring_rolls":100,"grilled_salmon":150,"chicken_curry":250,
    "bibimbap":400,"pho":500,"tacos":170,"nachos":113,
    "waffles":130,"pancakes":150,"omelette":120,"caesar_salad":200,
    "greek_salad":150,"chocolate_cake":100,"cheesecake":125,
    "ice_cream":132,"donuts":60,"apple_pie":155,
    "strawberry_shortcake":150,"miso_soup":240,"edamame":155,
    "burger":150,"dal_bhat":400,"kheer":150,"sel_roti":80,
}

PORTION_MULTIPLIERS = {"Small":0.6, "Medium":1.0, "Large":1.5, "XL":2.0}


def get_nutrition(food_name: str, weight_g: float = None, portion: str = "Medium") -> dict:
    key = food_name.lower().replace(" ", "_")
    n   = NUTRITION_DB.get(key)
    if n is None:
        return {"error": f"'{key}' not found in nutrition database"}

    default_g  = DEFAULT_SERVING_G.get(key, 100)
    multiplier = PORTION_MULTIPLIERS.get(portion, 1.0)
    if weight_g is None:
        weight_g = default_g * multiplier

    f = weight_g / 100.0
    return {
        "food":      key.replace("_"," ").title(),
        "weight_g":  round(weight_g, 1),
        "portion":   portion,
        "calories":  round(n["calories"] * f),
        "protein_g": round(n["protein"]  * f, 1),
        "carbs_g":   round(n["carbs"]    * f, 1),
        "fat_g":     round(n["fat"]      * f, 1),
        "fiber_g":   round(n["fiber"]    * f, 1),
        "sugar_g":   round(n["sugar"]    * f, 1),
        "sodium_mg": round(n["sodium"]   * f),
    }


# INFERENCE

DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT = "./checkpoints/best_model.pth"


def load_model():
    ckpt        = torch.load(CHECKPOINT, map_location=DEVICE)
    class_names = ckpt["classes"]
    num_classes = len(class_names)
    model = models.resnet50(weights=None)
    model.fc = nn.Sequential(nn.Dropout(0.4), nn.Linear(model.fc.in_features, num_classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()
    print(f"✅ Model loaded — {num_classes} classes, val_acc={ckpt['val_acc']:.3f}")
    return model, class_names


def preprocess_image(image_path: str):
    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
    ])
    img = Image.open(image_path).convert("RGB")
    return tf(img).unsqueeze(0).to(DEVICE)


@torch.no_grad()
def predict(model, class_names, image_path, weight_g=None, portion="Medium", top_k=3):
    tensor  = preprocess_image(image_path)
    probs   = F.softmax(model(tensor), dim=1)[0]
    top_p, top_i = probs.topk(top_k)
    results = []
    for prob, idx in zip(top_p.cpu().tolist(), top_i.cpu().tolist()):
        food = class_names[idx]
        results.append({
            "rank": len(results)+1,
            "food": food.replace("_"," ").title(),
            "confidence": round(prob*100, 1),
            "nutrition": get_nutrition(food, weight_g=weight_g, portion=portion),
        })
    return results


def print_results(results):
    print("\n" + "="*55)
    print("  🍽️  FOOD NUTRITION ESTIMATOR")
    print("="*55)
    for r in results:
        n = r["nutrition"]
        print(f"\n  #{r['rank']}  {r['food']}  ({r['confidence']}% confidence)")
        if "error" not in n:
            print(f"      Portion   : {n['portion']} ({n['weight_g']}g)")
            print(f"      Calories  : {n['calories']} kcal")
            print(f"      Protein   : {n['protein_g']}g  |  Carbs: {n['carbs_g']}g  |  Fat: {n['fat_g']}g")
            print(f"      Fiber     : {n['fiber_g']}g  |  Sugar: {n['sugar_g']}g  |  Sodium: {n['sodium_mg']}mg")
        else:
            print(f"      ⚠️  {n['error']}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",   required=True)
    parser.add_argument("--weight",  type=float, default=None)
    parser.add_argument("--portion", default="Medium", choices=["Small","Medium","Large","XL"])
    parser.add_argument("--top",     type=int, default=3)
    args = parser.parse_args()

    model, class_names = load_model()
    results = predict(model, class_names, args.image,
                      weight_g=args.weight, portion=args.portion, top_k=args.top)
    print_results(results)
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from inference import NUTRITION_DB, DEFAULT_SERVING_G, PORTION_MULTIPLIERS


FOOD_DESCRIPTIONS = {
    "pizza": "Italian flatbread with tomato sauce and toppings",
    "hot_dog": "Grilled sausage in a soft bun",
    "french_fries": "Deep-fried potato strips",
    "fried_rice": "Stir-fried rice with vegetables and egg",
    "sushi": "Japanese rice with seafood or vegetables",
    "ramen": "Japanese noodle soup with rich broth",
    "pad_thai": "Thai stir-fried rice noodles",
    "dumplings": "Filled dough pockets, steamed or fried",
    "spring_rolls": "Crispy rolled appetizer with fillings",
    "grilled_salmon": "Omega-3 rich grilled fish fillet",
    "chicken_curry": "Spiced chicken in aromatic sauce",
    "bibimbap": "Korean mixed rice bowl with vegetables",
    "pho": "Vietnamese beef noodle soup",
    "tacos": "Mexican tortilla with seasoned fillings",
    "nachos": "Tortilla chips with cheese and toppings",
    "waffles": "Grid-patterned baked breakfast cake",
    "pancakes": "Fluffy flat breakfast cakes",
    "omelette": "Folded egg dish with fillings",
    "caesar_salad": "Romaine lettuce with Caesar dressing",
    "greek_salad": "Fresh vegetables with feta cheese",
    "chocolate_cake": "Rich layered chocolate dessert",
    "cheesecake": "Creamy cheese-based dessert",
    "ice_cream": "Frozen dairy dessert",
    "donuts": "Fried dough ring with glaze",
    "apple_pie": "Baked pastry with spiced apple filling",
    "strawberry_shortcake": "Sponge cake with strawberries and cream",
    "miso_soup": "Japanese fermented soybean broth",
    "edamame": "Steamed young soybeans in pods",
    "burger":   "Juicy beef patty in a bun with fresh toppings",
    "dal_bhat": "Nepali staple — steamed rice with lentil soup",
    "kheer":    "Nepali creamy rice pudding with cardamom and nuts",
    "sel_roti": "Nepali traditional ring-shaped rice flour donut",
}


FOOD_CATEGORIES = {
    "pizza": "italian",
    "hot_dog": "american",
    "french_fries": "american",
    "fried_rice": "asian",
    "sushi": "japanese",
    "ramen": "japanese",
    "pad_thai": "thai",
    "dumplings": "asian",
    "spring_rolls": "asian",
    "grilled_salmon": "seafood",
    "chicken_curry": "indian",
    "bibimbap": "korean",
    "pho": "vietnamese",
    "tacos": "mexican",
    "nachos": "mexican",
    "waffles": "breakfast",
    "pancakes": "breakfast",
    "omelette": "breakfast",
    "caesar_salad": "salad",
    "greek_salad": "salad",
    "chocolate_cake": "dessert",
    "cheesecake": "dessert",
    "ice_cream": "dessert",
    "donuts": "dessert",
    "apple_pie": "dessert",
    "strawberry_shortcake": "dessert",
    "miso_soup": "japanese",
    "edamame": "japanese",
    "burger":   "american",
    "dal_bhat": "nepali",
    "kheer":    "nepali",
    "sel_roti": "nepali",

}



def get_food_info(food_key: str) -> dict | None:
    key = food_key.lower().replace(" ", "_")
    n = NUTRITION_DB.get(key)
    if n is None:
        return None

    serving_g = DEFAULT_SERVING_G.get(key, 100)
    f = serving_g / 100.0

    return {
        "food_name": key.replace("_", " ").title(),
        "description": FOOD_DESCRIPTIONS.get(key, "Delicious food item"),
        "category": FOOD_CATEGORIES.get(key, "other"),
        "serving_size": f"{serving_g}g",
        "calories_per_serving": round(n["calories"] * f),
        "protein_g": round(n["protein"] * f, 1),
        "carbs_g": round(n["carbs"] * f, 1),
        "fat_g": round(n["fat"] * f, 1),
        "fiber_g": round(n["fiber"] * f, 1),
        "sugar_g": round(n["sugar"] * f, 1),
        "sodium_mg": round(n["sodium"] * f),
    }


SINGLE_UNIT_WEIGHT_G = {
    "dumplings": 25,
    "pizza": 107,
    "hot_dog": 98,
    "sushi": 30,
    "spring_rolls": 50,
    "burger": 150,
    "donuts": 60,
    "waffles": 130,
    "pancakes": 75,
    "tacos": 85,
    "sel_roti": 80,
}

def calculate_total_calories(food_key: str, portion_type: str = "grams", portion_value: int = None) -> dict | None:
    key = food_key.lower().replace(" ", "_")
    n = NUTRITION_DB.get(key)
    if n is None:
        return None
        
    info = get_food_info(food_key)

    if portion_type == "count" or portion_type == "items":
        c = max(int(portion_value), 1) if portion_value else 1
        unit_g = SINGLE_UNIT_WEIGHT_G.get(key, DEFAULT_SERVING_G.get(key, 100))
        grams = unit_g * c
        serving_str = f"{c} item(s) (~{grams}g)"
    else:
        grams = max(int(portion_value), 1) if portion_value else DEFAULT_SERVING_G.get(key, 100)
        serving_str = f"{grams}g"
    
    f = grams / 100.0

    total_cal = round(n["calories"] * f)

    return {
        "food_name": info["food_name"],
        "description": info["description"],
        "serving_size": serving_str,
        "total_calories": total_cal,
        "protein_g": round(n["protein"] * f, 1),
        "carbs_g": round(n["carbs"] * f, 1),
        "fat_g": round(n["fat"] * f, 1),
        "fiber_g": round(n["fiber"] * f, 1),
        "sugar_g": round(n["sugar"] * f, 1),
        "sodium_mg": round(n["sodium"] * f),
    }


def get_all_foods() -> list[dict]:
    foods = []
    for key in NUTRITION_DB:
        info = get_food_info(key)
        if info is None:
            continue
        foods.append({
            "key": key,
            "name": info["food_name"],
            "description": info["description"],
            "category": info["category"],
            "calories": info["calories_per_serving"],
            "serving_size": info["serving_size"],
            "protein_g": info["protein_g"],
            "carbs_g": info["carbs_g"],
            "fat_g": info["fat_g"],
            "fiber_g": info["fiber_g"],
        })
    return foods


def get_nepali_foods_list() -> list[dict]:
    return []

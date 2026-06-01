"""
Calorie Database Module
========================
Wraps the project's NUTRITION_DB and DEFAULT_SERVING_G from inference.py
into the API surface that app.py and the frontend expect.
"""

import sys, os

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from inference import NUTRITION_DB, DEFAULT_SERVING_G, PORTION_MULTIPLIERS


# ─── Food descriptions (mirrors demo.py) ───────────────────────────────────

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
}


# Food category for display in the food database grid
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
}

# Emoji icons per food for the database grid
FOOD_EMOJIS = {
    "pizza": "🍕", "hot_dog": "🌭", "french_fries": "🍟", "fried_rice": "🍚",
    "sushi": "🍣", "ramen": "🍜", "pad_thai": "🍝", "dumplings": "🥟",
    "spring_rolls": "🥢", "grilled_salmon": "🐟", "chicken_curry": "🍛",
    "bibimbap": "🍲", "pho": "🍲", "tacos": "🌮", "nachos": "🧀",
    "waffles": "🧇", "pancakes": "🥞", "omelette": "🍳",
    "caesar_salad": "🥗", "greek_salad": "🥗",
    "chocolate_cake": "🍫", "cheesecake": "🍰", "ice_cream": "🍨",
    "donuts": "🍩", "apple_pie": "🥧", "strawberry_shortcake": "🍓",
    "miso_soup": "🍵", "edamame": "🫘",
}


def get_food_info(food_key: str) -> dict | None:
    """
    Return a rich info dict for a single food, or None if not in the DB.
    """
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
        "emoji": FOOD_EMOJIS.get(key, "🍽️"),
        "serving_size": f"{serving_g}g",
        "calories_per_serving": round(n["calories"] * f),
        "protein_g": round(n["protein"] * f, 1),
        "carbs_g": round(n["carbs"] * f, 1),
        "fat_g": round(n["fat"] * f, 1),
        "fiber_g": round(n["fiber"] * f, 1),
        "sugar_g": round(n["sugar"] * f, 1),
        "sodium_mg": round(n["sodium"] * f),
    }


def calculate_total_calories(food_key: str, count: int = None) -> dict | None:
    """
    Get full nutrition for a food, optionally multiplied by count.
    Returns the structure the frontend modal expects.
    """
    info = get_food_info(food_key)
    if info is None:
        return None

    c = max(int(count), 1) if count else 1
    total_cal = info["calories_per_serving"] * c

    return {
        "food_name": info["food_name"],
        "description": info["description"],
        "serving_size": info["serving_size"],
        "calories_per_unit": info["calories_per_serving"],
        "total_calories": total_cal,
        "count": c,
        "protein_g": round(info["protein_g"] * c, 1),
        "carbs_g": round(info["carbs_g"] * c, 1),
        "fat_g": round(info["fat_g"] * c, 1),
        "fiber_g": round(info["fiber_g"] * c, 1),
        "sugar_g": round(info["sugar_g"] * c, 1),
        "sodium_mg": round(info["sodium_mg"] * c),
    }


def get_all_foods() -> list[dict]:
    """
    Return a list of all foods in the database, formatted for the
    frontend food-grid cards.
    """
    foods = []
    for key in NUTRITION_DB:
        info = get_food_info(key)
        if info is None:
            continue
        foods.append({
            "key": key,
            "name": info["food_name"],
            "emoji": info["emoji"],
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
    """
    No Nepali-specific foods in the current database.
    Returns empty list — the frontend will hide the tab accordingly.
    """
    return []

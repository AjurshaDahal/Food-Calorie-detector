"""
Food Recognition + Calorie Estimator
Flask Application Server

An AI-powered system that recognizes food items from images
and estimates their calorie content using a ResNet50 model
trained on the Food-101 dataset (28 categories).
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from model.classifier import FoodClassifier
from model.calorie_db import (
    get_food_info,
    calculate_total_calories,
    get_nepali_foods_list,
    get_all_foods,
)


# App Configuration

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}


# Initialize the Food Classifier

print("=" * 60)
print("[*] BhojanLens — Food Recognition + Calorie Estimator")
print("    Initializing ResNet50 model...")
print("=" * 60)

classifier = FoodClassifier()

print("=" * 60)
print("[OK] System ready! Accepting food images for analysis.")
print(f"     Supported foods: {len(classifier.get_supported_foods())}")
print("=" * 60)



# Helper Functions

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



# Routes

@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze_food():
    """
    Analyze an uploaded food image.
    
    Accepts:
        - image file (multipart/form-data)
        - portion_size_g (optional): exact portion weight in grams
        
    Returns:
        JSON with food identification and nutritional information
    """
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {
                "success": False,
                "error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            }
        ), 400

    try:
        # Save the uploaded file
        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)

        # Get optional portion type and value
        portion_type = request.form.get("portion_type", "grams")
        portion_value = request.form.get("portion_value", None)
        if portion_value:
            try:
                portion_value = int(portion_value)
            except ValueError:
                portion_value = None

        # Run food classification
        result = classifier.predict(filepath, portion_type, portion_value)
        result["image_url"] = f"/static/uploads/{unique_filename}"

        return jsonify(result)

    except Exception as e:
        return jsonify(
            {"success": False, "error": f"Analysis failed: {str(e)}"}
        ), 500


@app.route("/api/manual-lookup", methods=["POST"])
def manual_lookup():
    """
    Manually look up calorie information for a food item.
    
    Accepts JSON:
        - food_key: key from the food database
        - count: optional item count for countable foods
    """
    data = request.get_json()
    if not data or "food_key" not in data:
        return jsonify({"success": False, "error": "food_key is required"}), 400

    food_key = data["food_key"]
    portion_type = data.get("portion_type", "grams")
    portion_value = data.get("portion_value", None)

    if portion_value:
        try:
            portion_value = int(portion_value)
        except ValueError:
            portion_value = None

    nutrition = calculate_total_calories(food_key, portion_type, portion_value)

    if nutrition:
        return jsonify({"success": True, "nutrition": nutrition})
    else:
        return jsonify({"success": False, "error": "Food item not found"}), 404


@app.route("/api/foods", methods=["GET"])
def get_foods():
    """Return list of all supported food items."""
    foods = classifier.get_supported_foods()
    return jsonify({"success": True, "foods": foods})


@app.route("/api/nepali-foods", methods=["GET"])
def get_nepali_foods():
    """Return list of Nepali food items."""
    foods = get_nepali_foods_list()
    return jsonify({"success": True, "foods": foods})



# Run Server

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

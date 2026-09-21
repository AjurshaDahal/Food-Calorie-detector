# 🍽️ Food Calorie Detector

Food Calorie Detector is an AI-powered web application that identifies food from an uploaded image and estimates its calorie content. The project also includes portion-size analysis to provide a more practical calorie estimate.

## Where the project stands

The project currently provides a working web-based food recognition and calorie estimation pipeline. Users can upload a food image, process it through the trained deep learning model, identify the detected food, and receive calorie information based on the predicted food and portion.

The project is intended as an educational and research-oriented machine learning application. Calorie estimates are approximate and should not be treated as medical or nutritional advice.

## What the project does

| Component | Responsibility | Current state |
|---|---|---|
| Food Recognition | Identify the food item from an uploaded image | Implemented |
| Image Processing | Prepare images for model inference | Implemented |
| Food Classification | Predict the corresponding food category | Implemented |
| Portion Analysis | Estimate serving/portion information | Implemented |
| Calorie Estimation | Calculate estimated calories | Implemented |
| Web Application | Provide an interface for image-based prediction | Implemented |
| Model Training | Train and retrain the classification model | Available |

## Choose your starting point

**Want to run the application:**  
Follow the installation and running instructions below.

**Want to understand the model:**  
Start with `inference.py` and the `model/` directory.

**Want to train or retrain the model:**  
Start with `prepare_data.py`, `train.py`, and `retrain.py`.

**Want to understand the web application:**  
Start with `app.py` and `templates/index.html`.

## Features

- Upload food images for recognition
- AI-based food classification
- Calorie estimation
- Portion-size analysis
- Food and calorie database
- Flask-based web interface
- Model training and retraining scripts
- Image preprocessing and inference pipeline
- Support for locally trained model checkpoints

## How it works

The application follows this general pipeline:

```text
Food Image
     ↓
Image Preprocessing
     ↓
Deep Learning Model
     ↓
Food Classification
     ↓
Portion Analysis
     ↓
Calorie Estimation
     ↓
Result Display

The user uploads an image through the web interface. The image is processed and passed through the trained classification model. After identifying the food category, the system uses the corresponding food information and portion information to estimate the calorie content.

Project Structure
Food-Calorie-detector/
│
├── app.py                  # Flask web application
├── demo.py                 # Demo / testing script
├── inference.py            # Model inference pipeline
├── prepare_data.py         # Dataset preparation
├── train.py                # Model training
├── retrain.py              # Model retraining
│
├── model/
│   ├── __init__.py
│   ├── classifier.py       # Food classification model
│   └── calorie_db.py       # Food and calorie database
│
├── templates/
│   └── index.html          # Web interface
│
├── static/
│   └── ...                 # CSS, JavaScript and static assets
│
├── checkpoints/
│   └── ...                 # Trained model checkpoints
│
└── requirements.txt        # Python dependencies
Technologies Used
Python
PyTorch
Flask
OpenCV
HTML
CSS
JavaScript
Machine Learning
Deep Learning
Quick Setup
1. Clone the repository
git clone https://github.com/AjurshaDahal/Food-Calorie-detector.git
cd Food-Calorie-detector
2. Create a virtual environment
python -m venv venv
3. Activate the environment

macOS / Linux

source venv/bin/activate

Windows

venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
Run the Application

Start the Flask application:

python app.py

The terminal will provide a local address for the application.

Open that address in your browser and use the web interface to upload a food image.

Model Training

The repository contains scripts for preparing data and training the food classification model.

Prepare the dataset
python prepare_data.py
Train the model
python train.py
Retrain the model
python retrain.py
Run inference
python inference.py

The exact training configuration depends on the available dataset, model configuration, and hardware.

Calorie Estimation

After the model identifies a food item, the application retrieves relevant calorie information from the food database.

The estimated calorie value can be influenced by the detected portion size.

Detected Food
     +
Portion Information
     ↓
Food Database
     ↓
Estimated Calories

The result is an estimate rather than a laboratory measurement.

Web Application

The project includes a Flask-based web interface.

The typical workflow is:

Upload a food image.
Process the image.
Run the trained model.
Identify the food category.
Analyze the portion.
Estimate calories.
Display the result.
Data and Model Files

Large datasets, trained model checkpoints, virtual environments, Python cache files, and runtime-uploaded images are excluded from version control where appropriate.

The repository .gitignore includes exclusions for files such as:

dataset/
food-101/
parikar/
checkpoints/
__pycache__/
*.pyc
*.pth
venv/
static/uploads/

This keeps the GitHub repository focused on the source code and project configuration.

Important Limitations
Food recognition accuracy depends on the trained model and available training data.
Calorie values are estimates.
Portion-size estimation may vary depending on the image.
Different preparation methods can significantly change actual calorie content.
The system should not be used as a substitute for professional nutritional or medical advice.
Model performance may vary for food categories that are underrepresented in the training data.
Future Improvements

Potential improvements include:

Expand the food classification dataset
Improve classification accuracy
Improve portion-size estimation
Add macronutrient estimation
Add protein, carbohydrate, fat, and fiber information
Support more food categories
Improve image preprocessing
Improve model inference speed
Add meal history and tracking
Add user accounts
Deploy the application to a cloud platform
Develop a mobile application
License

This project is intended primarily for educational and research purposes.

Author

Ajursha Dahal

B.Sc. Computer Science
Kathmandu University

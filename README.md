# Food Calorie Detector

An AI-powered food recognition and calorie estimation system that identifies food items from images and estimates their calorie content. The system also includes portion-size analysis to provide a more practical calorie estimate.

## Features

-  Upload food images for analysis
-  AI-based food recognition
-  Food classification
-  Calorie estimation
-  Portion-size analysis
-  Food and calorie information database
-  Web-based interface
-  Model training and retraining support
-  Deep learning-based inference
-  Simple and user-friendly interface

##  Technologies Used

- **Python**
- **PyTorch**
- **Flask**
- **OpenCV**
- **HTML / CSS / JavaScript**
- **Machine Learning**
- **Deep Learning**

##  Project Structure

```text
Food-Calorie-detector/
│
├── app.py                  # Flask web application
├── demo.py                 # Demonstration script
├── inference.py            # Model inference
├── prepare_data.py         # Data preparation
├── train.py                # Model training
├── retrain.py              # Model retraining
│
├── model/
│   ├── classifier.py       # Food classification model
│   ├── calorie_db.py       # Food calorie database
│   └── __init__.py
│
├── templates/
│   └── index.html          # Web interface
│
├── static/
│   └── ...                 # Static assets
│
├── checkpoints/            # Model checkpoints
│
└── requirements.txt        # Python dependencies
 Installation
1. Clone the repository
git clone https://github.com/AjurshaDahal/Food-Calorie-detector.git
cd Food-Calorie-detector
2. Create a virtual environment
python -m venv venv
3. Activate the virtual environment

macOS / Linux:

source venv/bin/activate

Windows:

venv\Scripts\activate
4. Install dependencies
pip install -r requirements.txt
Running the Application

Start the Flask application:

python app.py

The application will start on a local development server.

Open the URL displayed in the terminal in your web browser.

How It Works

The system follows a basic image-to-calorie estimation pipeline:

Food Image
    ↓
Image Processing
    ↓
Food Recognition
    ↓
Food Classification
    ↓
Portion Size Analysis
    ↓
Calorie Estimation
    ↓
Result Display

The uploaded food image is processed by the trained machine learning model. The system identifies the food item and uses the corresponding food information to estimate its calorie content. Portion information is incorporated to make the estimation more relevant to the detected serving.

 Model Training

The project includes scripts for training and retraining the food classification model.

Train the model
python train.py
Retrain the model
python retrain.py
Prepare data
python prepare_data.py

Model checkpoints and large datasets are not included in the repository and are excluded using .gitignore.

Calorie Estimation

After identifying the food item, the system uses its associated nutritional information to estimate calories.

The estimation can take portion size into account, allowing the application to provide a more useful result than simply identifying the food category.

Note: Calorie estimates are approximate and should not be considered medically accurate nutritional measurements.

 Web Application

The project includes a Flask-based web interface where users can interact with the food recognition and calorie estimation system.

Users can:

Upload a food image.
Process the image through the model.
Identify the detected food.
View the estimated calorie information.
Analyze portion-related information.
 Dependencies

Project dependencies are listed in:

requirements.txt

Install them using:

pip install -r requirements.txt
Files Excluded from Git

The following types of files are excluded from version control:

Virtual environments
Python cache files
Model checkpoint files
Large datasets
Training data
Runtime uploaded images

This keeps the repository lightweight and focused on the source code.

 Future Improvements

Possible future improvements include:

Improve food classification accuracy
Expand the food database
Improve portion-size estimation
Add nutritional information such as protein, carbohydrates, fats, and fiber
Support a wider range of food categories
Improve model performance
Add user history and meal tracking
Deploy the application to a cloud platform
Develop a mobile-friendly version

 License

This project is intended for educational and research purposes.


After pasting and saving it, run:

```bash
git add README.md
git commit -m "Add README documentation"
git push

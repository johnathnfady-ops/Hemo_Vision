# 🏥 HemoVision - AI-Powered Anemia Detection System

An intelligent web application for early anemia detection using conjunctiva and nailbed images, powered by XGBoost machine learning.

## 🌟 Key Features

- **Real AI Model**: XGBoost trained on 93 real patient images (MAE: 1.48 g/dL)
- **Image Analysis**: Extracts 34 color features from eye/nail images
- **User Management**: Flask-Login authentication with bcrypt encryption
- **Medical Dashboard**: Track hemoglobin history and screening results
- **Nutrition Planner**: Personalized meal plans for anemia recovery
- **Privacy Protected**: Auto-delete images after 1 hour

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_db.py
```

### 3. Run Application
```bash
python app.py
```

### 4. Access
Open: `http://localhost:5001`  
Demo Login: `demo@hemovision.com` / `demo123`

## 🧠 AI Model

- **Algorithm**: XGBoost (Extreme Gradient Boosting)
- **Features**: 34 color & texture features (RGB, HSV, LAB)
- **Training Data**: 93 conjunctiva images with hemoglobin labels
- **Performance**:
  - MAE: 1.48 g/dL
  - RMSE: 2.07 g/dL
  - CV MAE: 1.60 g/dL

### Retrain Model
```bash
python train_model_sklearn.py
```

## 📊 Model Performance

| Metric | Value | Description |
|--------|-------|-------------|
| MAE | 1.48 g/dL | Mean Absolute Error |
| RMSE | 2.07 g/dL | Root Mean Squared Error |
| CV MAE | 1.60 g/dL | Cross-Validation MAE |
| Patients | 93 | Training dataset size |
| Features | 34 | Extracted per image |

## 🏗️ Project Structure

```
hemo_vision/
├── app.py                      # Main Flask application
├── train_model_sklearn.py      # Model training script
├── init_db.py                  # Database initialization
├── requirements.txt            # Python dependencies
│
├── modules/                    # Core modules
│   ├── ml_analyzer.py         # XGBoost analyzer
│   ├── cv_analyzer.py         # OpenCV fallback
│   ├── database.py            # SQLAlchemy models
│   ├── image_quality.py       # Image quality checker
│   ├── nutrition_engine.py    # Meal plan generator
│   └── ocr_real.py            # OCR document parser
│
├── model/                      # Trained model files
│   ├── anemia_model.pkl       # XGBoost model
│   ├── feature_scaler.pkl     # Feature scaler
│   └── model_stats.pkl        # Performance metrics
│
├── archive/                    # Training dataset
│   └── dataset anemia/
│       └── India/             # 93 patient images
│
├── templates/                  # HTML templates
└── static/                     # CSS/JS/Images
```

## 🔬 How It Works

### 1. Feature Extraction
From each conjunctiva image, we extract:
- **RGB Statistics** (15 features): mean, std, median, quartiles
- **HSV Statistics** (6 features): hue, saturation, value
- **LAB Statistics** (6 features): lightness, red-green, yellow-blue
- **Color Ratios** (7 features): R/G, R/B, G/B, red dominance, etc.

### 2. Prediction
- Features are normalized using StandardScaler
- XGBoost model predicts hemoglobin value
- Result is classified into severity levels

### 3. Classification
```python
Hb >= 12.0 g/dL → Normal
Hb >= 11.0 g/dL → Mild Anemia
Hb >= 8.0 g/dL  → Moderate Anemia
Hb < 8.0 g/dL   → Severe Anemia
```

## 📦 Dependencies

```
flask>=3.0.3
xgboost>=2.0.0
opencv-python>=4.9.0
pandas>=2.0.0
scikit-learn>=1.3.0
openpyxl>=3.1.0
pytesseract>=0.3.10
bcrypt>=4.1.2
flask-login>=0.6.3
flask-sqlalchemy>=3.1.1
```

## ⚡ Performance

- **Prediction Speed**: ~65 ms per image
- **Memory Usage**: ~13 MB
- **Model Size**: ~2 MB
- **Accuracy**: ±1.5 g/dL average error

## 🎯 Top Contributing Features

1. **B_std** (10.47%) - Blue channel standard deviation
2. **S_std** (10.24%) - Saturation standard deviation
3. **A_std** (8.11%) - LAB A-channel std
4. **GB_ratio** (7.46%) - Green/Blue ratio
5. **H_mean** (7.12%) - Mean hue value

## ⚠️ Important Notes

### Medical Disclaimer
This application is for **educational purposes only**. It provides preliminary screening and should NOT replace professional medical diagnosis. Always consult a healthcare provider and perform laboratory CBC tests for accurate hemoglobin measurement.

### Image Quality
- Use natural lighting
- Avoid shadows and reflections
- Ensure clear focus
- Higher quality = better accuracy

### Model Limitations
- Trained on Indian patient data
- May vary across different ethnicities
- Average error: ±1.5 g/dL
- Not FDA/medical authority approved

## 📚 Documentation

- **README_AR.md** - Complete Arabic documentation
- **دليل_التدريب.md** - Training guide (Arabic)
- **ملخص_المشروع.md** - Project summary (Arabic)

## 🔐 Security Features

- **Authentication**: Flask-Login with session management
- **Password Hashing**: Bcrypt encryption
- **Privacy Protection**: Auto-delete uploaded images after 1 hour
- **Image Validation**: Quality checks before analysis
- **SQL Injection Protection**: SQLAlchemy ORM

## 🛠️ Technology Stack

- **Backend**: Python 3.14, Flask
- **AI/ML**: XGBoost, Scikit-learn, OpenCV
- **Database**: SQLite with SQLAlchemy
- **Authentication**: Flask-Login, Bcrypt
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js

## 📈 Future Improvements

- [ ] Deep Learning (CNN) models
- [ ] Data augmentation for better accuracy
- [ ] Multi-language support
- [ ] Mobile app version
- [ ] Real-time camera capture
- [ ] PDF report generation

## 👥 Team

Computer Science & AI Department - Graduation Project

## 📄 License

Educational use only.

---

**Last Updated**: June 14, 2026  
**Model Version**: XGBoost v1.0  
**Accuracy**: MAE 1.48 g/dL  
**Status**: Production Ready ✅

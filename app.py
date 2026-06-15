import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from modules.nutrition_engine import generate_meal_plan
from modules.database import db, User, Screening, Reminder, init_db
from modules.image_quality import assess_image_quality

try:
    from modules.ml_analyzer import analyze_conjunctiva_ml, analyze_nailbed_ml
    USE_ML = True
    analyze_eye_func = analyze_conjunctiva_ml
    analyze_nail_func = analyze_nailbed_ml
    print("[HemoVision] ML model loaded! Using ML-based analysis.")
except Exception as e:
    print(f"[HemoVision] ML not available ({e}). Using CV fallback.")
    USE_ML = False
    try:
        from modules.cv_analyzer import analyze_conjunctiva_real, analyze_nailbed_real
        analyze_eye_func = analyze_conjunctiva_real
        analyze_nail_func = analyze_nailbed_real
        print("[HemoVision] CV analyzer loaded.")
    except:
        from modules.analyzer import analyze_conjunctiva, analyze_nailbed
        analyze_eye_func = lambda path: analyze_conjunctiva(os.path.basename(path))
        analyze_nail_func = lambda path: analyze_nailbed(os.path.basename(path))
        print("[HemoVision] Using simulation fallback.")

try:
    from modules.ocr_real import parse_document_real
except:
    from modules.ocr_engine import parse_document as parse_document_real

app = Flask(__name__)
app.secret_key = "hemovision-secret-2026-enhanced"

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hemovision.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# Auto-delete uploaded images after analysis (privacy protection)
app.config["AUTO_DELETE_IMAGES"] = True
app.config["IMAGE_RETENTION_HOURS"] = 1  # Keep images for 1 hour max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
init_db(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def get_dashboard_data(user):
    """Generate dashboard data from database for current user"""
    screenings = Screening.query.filter_by(user_id=user.id).order_by(Screening.created_at.desc()).all()
    reminders = Reminder.query.filter_by(user_id=user.id, is_active=True).all()

    # Build HB trend (last 7 screenings)
    hb_trend = []
    for s in reversed(screenings[-7:]):
        hb_trend.append({
            "date": s.created_at.strftime("%d %b %Y"),
            "hb": s.hb_estimate
        })

    # Build screenings list
    screenings_list = []
    for s in screenings[:5]:  # Last 5 screenings
        screenings_list.append({
            "date": s.created_at.strftime("%d %b %Y"),
            "method": s.method,
            "hb": s.hb_estimate,
            "status": s.severity_key,
            "color": s.severity_label
        })

    reminders_list = []
    for r in reminders:
        reminders_list.append({
            "title": r.title,
            "time": r.time,
            "icon": r.icon,
            "days": r.days
        })

    current_hb = screenings[0].hb_estimate if screenings else 0
    first_hb = screenings[-1].hb_estimate if len(screenings) > 1 else current_hb
    improvement = ((current_hb - first_hb) / first_hb * 100) if first_hb > 0 else 0

    days_on_treatment = (datetime.utcnow() - user.created_at).days if user.created_at else 0

    return {
        "patient": {
            "name": user.name,
            "age": user.age or 0,
            "gender": user.gender or "Not specified",
            "blood_type": user.blood_type or "Unknown",
            "doctor": "Dr. Sara Khalil",
        },
        "hb_trend": hb_trend,
        "screenings": screenings_list,
        "reminders": reminders_list,
        "stats": {
            "total_screenings": len(screenings),
            "improvement_pct": f"{improvement:.1f}%",
            "days_on_treatment": days_on_treatment,
            "current_hb": current_hb,
        },
    }


def delete_old_images():
    """Delete images older than retention period (privacy protection)"""
    if not app.config["AUTO_DELETE_IMAGES"]:
        return
    try:
        retention_hours = app.config["IMAGE_RETENTION_HOURS"]
        cutoff_time = datetime.now() - timedelta(hours=retention_hours)
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    os.remove(filepath)
    except Exception as e:
        print(f"Error deleting old images: {e}")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template("index.html")


@app.route("/test")
def test():
    return render_template("test.html")


@app.route("/simple-login")
def simple_login():
    return render_template("simple_login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_type = request.form.get("blood_type")

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for('register'))

        user = User(
            email=email,
            name=name,
            age=int(age) if age else None,
            gender=gender,
            blood_type=blood_type
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('onboarding'))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/onboarding")
@login_required
def onboarding():
    return render_template("onboarding.html")


@app.route("/screening/eye")
@login_required
def screening_eye():
    return render_template("screening_eye.html")


@app.route("/nutrition")
@login_required
def nutrition():
    return render_template("nutrition.html")


@app.route("/dashboard")
@login_required
def dashboard():
    delete_old_images()
    data = get_dashboard_data(current_user)
    return render_template("dashboard.html", data=data)


# 
@app.route("/api/analyze/eye", methods=["POST"])
@app.route("/api/analyze/eye", methods=["POST"])
@login_required
def api_analyze_eye():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["image"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Check image quality
        quality = assess_image_quality(filepath)
        if not quality["is_acceptable"]:
            os.remove(filepath)
            return jsonify({
                "error": "Image quality insufficient",
                "issues": quality["issues"]
            }), 400

        # Analyze using ML or CV
        result = analyze_eye_func(filepath)
        result["image_url"] = f"/static/uploads/{filename}"

        # Save to database
        screening = Screening(
            user_id=current_user.id,
            method="Conjunctiva",
            hb_estimate=result["hb_estimate"],
            confidence=result["confidence"],
            pallor_index=result["pallor_index"],
            severity_key=result["severity_key"],
            severity_label=result["severity_label"],
            rbc_count=result.get("rbc_count"),
            mcv=result.get("mcv")
        )
        db.session.add(screening)
        db.session.commit()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/nail", methods=["POST"])
@login_required
def api_analyze_nail():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["image"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user.id}_{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Check image quality
        quality = assess_image_quality(filepath)
        if not quality["is_acceptable"]:
            os.remove(filepath)
            return jsonify({
                "error": "Image quality insufficient",
                "issues": quality["issues"]
            }), 400

        # Analyze using ML or CV
        result = analyze_nail_func(filepath)
        result["image_url"] = f"/static/uploads/{filename}"

        # Save to database
        screening = Screening(
            user_id=current_user.id,
            method="Nailbed",
            hb_estimate=result["hb_estimate"],
            confidence=result["confidence"],
            pallor_index=result["pallor_index"],
            severity_key=result["severity_key"],
            severity_label=result["severity_label"],
            capillary_refill=result.get("capillary_refill"),
            nail_color_score=result.get("nail_color_score")
        )
        db.session.add(screening)
        db.session.commit()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/nutrition", methods=["POST"])
@login_required
def api_nutrition():
    data = request.get_json()
    anemia_type = data.get("anemia_type", "iron_deficiency")
    severity    = data.get("severity",    "mild")
    diet_pref   = data.get("diet_pref",   "omnivore")
    allergies   = data.get("allergies",   "")
    result = generate_meal_plan(anemia_type, severity, diet_pref, allergies)
    return jsonify(result)



if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)

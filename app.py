import os
import random
import time
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename

from database import (
    init_db, create_user, verify_user, get_user_by_id,
    log_traffic_detection, get_db_connection
)
from ai_detector import process_video_or_image

app = Flask(__name__)

# Security configuration
app.secret_key = os.environ.get('SECRET_KEY', 'smart-traffic-secure-session-key-2026')
app.permanent_session_lifetime = timedelta(days=7)

# Upload directory configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database tables and default admin on startup
with app.app_context():
    init_db()


def allowed_file(filename):
    """Check if uploaded file has a permissible extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """
    Decorator to protect routes from unauthenticated access.
    Redirects to login if user session is absent.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Session expired or unauthorized. Please sign in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    """Redirect to dashboard if logged in, otherwise redirect to login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle operator account registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Input validation
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash("Passwords do not match. Please verify and try again.", "error")
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return redirect(url_for('signup'))

        # Create user in SQLite database
        success, message = create_user(full_name, email, password)
        if success:
            flash(message, "success")
            return redirect(url_for('login'))
        else:
            flash(message, "error")
            return redirect(url_for('signup'))

    return render_template('auth/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle operator authentication"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember_me'))

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for('login'))

        # Verify against SQLite database with secure password hashing
        user, error = verify_user(email, password)

        if error:
            flash(error, "error")
            return redirect(url_for('login'))

        # Set session state
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']

        session.permanent = remember

        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for('dashboard'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    """Invalidate session and redirect to login"""
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main Traffic Management Dashboard"""
    return render_template('dashboard.html', active_page='dashboard')


@app.route('/detection', methods=['GET', 'POST'])
@login_required
def detection():
    """
    AI Computer Vision Vehicle Detection View.
    Accepts video or image uploads, executes YOLOv8 / OpenCV inference,
    computes vehicle counts, density, and recommended green light timing.
    """
    results = None

    if request.method == 'POST':
        use_sample = request.form.get('use_sample') == 'true'

        if use_sample:
            sample_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_traffic.jpg')
            if not os.path.exists(sample_path):
                flash("Sample image not found. Please upload a traffic file.", "error")
                return redirect(url_for('detection'))
            target_path = sample_path
        else:
            if 'traffic_media' not in request.files:
                flash("No file was uploaded.", "error")
                return redirect(url_for('detection'))

            file = request.files['traffic_media']
            if file.filename == '':
                flash("No file selected. Please choose a traffic video or image.", "error")
                return redirect(url_for('detection'))

            if not allowed_file(file.filename):
                flash("Unsupported file format. Please upload MP4, AVI, MOV, JPG, or PNG.", "error")
                return redirect(url_for('detection'))

            filename = secure_filename(file.filename)
            unique_name = f"{int(time.time())}_{filename}"
            target_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(target_path)

        try:
            # Execute actual Computer Vision inference pipeline
            results = process_video_or_image(target_path, app.config['UPLOAD_FOLDER'])

            # Log result to SQLite database
            log_traffic_detection(
                vehicle_count=results['total_vehicles'],
                cars=results['cars'],
                bikes=results['bikes'],
                buses=results['buses'],
                trucks=results['trucks'],
                density=results['density'],
                recommended_green=results['recommended_green'],
                mode='Actual Video Detection'
            )

            flash(f"Inference complete: {results['total_vehicles']} vehicles classified. Green time set to {results['recommended_green']}s.", "success")
        except Exception as e:
            flash(f"Error during video inference: {str(e)}", "error")

    return render_template('detection.html', active_page='detection', results=results)


@app.route('/reports')
@login_required
def reports():
    """Historical Reports and Analytics from SQLite Database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM traffic_logs ORDER BY id DESC LIMIT 15')
    logs = cursor.fetchall()
    conn.close()

    return render_template('reports.html', active_page='reports', logs=logs)


@app.route('/settings')
@login_required
def settings():
    """System Settings and Operator Profile"""
    return render_template('settings.html', active_page='settings')


@app.route('/api/traffic-data')
@login_required
def api_traffic_data():
    """
    Simulated Real-Time Traffic Telemetry API.
    Generates realistic vehicle distributions, computes traffic density,
    and calculates optimal green-light duration.
    """
    cars = random.randint(12, 28)
    bikes = random.randint(5, 18)
    buses = random.randint(1, 5)
    trucks = random.randint(1, 4)
    total_vehicles = cars + bikes + buses + trucks

    if total_vehicles <= 18:
        density = "Low"
    elif total_vehicles <= 35:
        density = "Medium"
    else:
        density = "High"

    base_time = 15
    weighted_pcu = (cars * 1.5) + (bikes * 0.8) + (buses * 4.0) + (trucks * 5.0)
    recommended_green = int(min(max(base_time + (weighted_pcu * 0.6), 15), 75))

    cycle_time = int(time.time()) % 40
    if cycle_time < 22:
        light_state = "green"
    elif cycle_time < 26:
        light_state = "yellow"
    else:
        light_state = "red"

    return jsonify({
        "status": "success",
        "total_vehicles": total_vehicles,
        "cars": cars,
        "bikes": bikes,
        "buses": buses,
        "trucks": trucks,
        "density": density,
        "recommended_green": recommended_green,
        "light_state": light_state,
        "current_phase": "Phase A (North-South Corridor)",
        "mode": "Simulated Live Telemetry"
    })


if __name__ == '__main__':
    print("[*] Traffic.AI Development Server Starting...")
    port = int(os.environ.get('PORT', '5000'))
    print(f"[*] Open your browser at: http://127.0.0.1:{port}/")
    app.run(debug=True, port=port)

# 🚦 AI-Based Smart Traffic Management System

A full-stack, AI-powered traffic monitoring and adaptive signal recommendation web application designed for urban congestion management. Built with Python Flask, SQLite, OpenCV, YOLOv8, and modern HTML5/CSS3/JavaScript.

---

## 📌 Project Overview
Traditional traffic light systems operate on fixed timers regardless of whether 5 vehicles or 50 vehicles are waiting. This project introduces an **adaptive traffic management system** that:
- Detects and classifies vehicles (cars, motorcycles/bikes, buses, trucks) in real time using Computer Vision (OpenCV & YOLOv8).
- Calculates real-time traffic density (Low, Medium, High).
- Recommends optimal green-light durations dynamically based on waiting vehicle volumes.
- Features dual operating modes: **Live Simulated Sensor Feed** and **Real Video Upload & Analysis**.
- Provides a secure role-aware authentication system with user profile management and session control.
- Delivers an interactive analytics dashboard with Chart.js visualization.

> **Academic & Hardware Disclaimer:** This project serves as an intelligent software simulation and decision-support analytical dashboard. It computes and suggests optimal traffic signal timings; it does not claim direct physical actuator control over municipal hardware without approved IoT/PLC relays.

---

## 🛠️ Tech Stack
- **Frontend:** HTML5, CSS3 (Custom Dark Navy/Cyan Theme), Vanilla JavaScript, Chart.js
- **Backend:** Python (Flask, Werkzeug)
- **Database:** SQLite3 (Local, lightweight relational database)
- **Computer Vision & AI:** OpenCV (`cv2`), YOLOv8 (`ultralytics`), NumPy
- **Version Control & Dev Tools:** Git, GitHub, VS Code, GitHub Copilot

---

## 📁 Project Directory Structure
```text
ai-traffic-management/
│
├── app.py                     # Main Flask application & routing engine
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes virtual environments, database, and uploaded videos
├── README.md                  # Project documentation & setup guide
│
├── static/
│   ├── css/
│   │   ├── auth.css           # Styling for login & signup forms
│   │   └── dashboard.css      # Dark navy/cyan theme for dashboard & components
│   ├── js/
│   │   ├── auth.js            # Form validations, password toggling
│   │   ├── dashboard.js       # Chart.js integration, metrics updates
│   │   └── detection.js       # Video upload handler & detection viewer
│   └── uploads/
│       └── .gitkeep           # Target directory for uploaded traffic video files
│
└── templates/
    ├── base.html              # Base layout with sidebar, navbar, and flash alerts
    ├── auth/
    │   ├── login.html         # Login interface
    │   └── signup.html        # Signup interface
    ├── dashboard.html         # Main overview with real-time stats & charts
    ├── detection.html         # AI vehicle detection upload & video feed
    ├── reports.html           # Historical traffic analytics reports
    └── settings.html          # Profile settings and threshold configuration
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9 - 3.12 installed ([python.org](https://www.python.org/))
- Git installed ([git-scm.com](https://git-scm.com/))
- Visual Studio Code installed ([code.visualstudio.com](https://code.visualstudio.com/))

### 2. Setup Virtual Environment (Windows PowerShell)
```powershell
# Open terminal inside the project folder
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Running the Application
```powershell
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000/`

### 4. Deploying to Render
1. Push this project to a GitHub repository and create a **Web Service** on Render connected to that repository.
2. Set the **Build Command** to `pip install -r requirements.txt`.
3. Set the **Start Command** to `gunicorn app:app`.
4. In the Render service's environment settings, add `SECRET_KEY` with a long, unique random value. Do not use the development fallback secret for a public deployment.
5. Deploy the service. Gunicorn reads `gunicorn.conf.py`, which listens on `0.0.0.0` and uses Render's `PORT` environment variable (with `10000` as a local fallback).

The existing SQLite database and uploaded files are stored on the service's filesystem. On hosting plans where that filesystem is temporary, database changes and uploads may not survive a redeploy or restart; configure persistent storage or a hosted database if that data must be retained. The AI model file (`yolov8n.pt`) must also be present in the deployed repository or available to the app at runtime.

---

## 🔒 Security & Best Practices
- Passwords hashed using `werkzeug.security` (PBKDF2/SHA256).
- Sensitive files (`.env`, `*.db`, video uploads) are excluded via `.gitignore`.
- Flask session cookies configured for tamper resistance.

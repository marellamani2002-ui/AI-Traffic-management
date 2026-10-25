"""
Database Management Module for AI-Based Smart Traffic Management System
Handles SQLite connection, schema creation, user authentication queries, and default admin seeding.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traffic.db')


def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Configures row_factory to sqlite3.Row for dictionary-like column access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize SQLite database tables and seed default administrator credentials.
    Called automatically on application startup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Authentication & User Profiles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Traffic Officer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    # 2. Traffic Analytics & Detection Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vehicle_count INTEGER NOT NULL,
            cars INTEGER DEFAULT 0,
            bikes INTEGER DEFAULT 0,
            buses INTEGER DEFAULT 0,
            trucks INTEGER DEFAULT 0,
            density TEXT NOT NULL,
            recommended_green_time INTEGER NOT NULL,
            source_mode TEXT NOT NULL DEFAULT 'Simulated'
        )
    ''')

    conn.commit()

    # Seed Default Administrator if user table is empty
    cursor.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] == 0:
        default_admin_email = 'admin@traffic.ai'
        default_admin_password = 'admin123'
        hashed_password = generate_password_hash(default_admin_password)

        cursor.execute('''
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', ('Chief Traffic Controller', default_admin_email, hashed_password, 'Administrator'))
        conn.commit()
        print(f"[OK] Database initialized: Default admin account created ({default_admin_email} / {default_admin_password})")
    else:
        print("[OK] Database connected: Tables verified.")

    conn.close()


def create_user(full_name, email, password, role='Traffic Officer'):
    """
    Register a new user with secure password hashing.
    Returns: (success: bool, message: str)
    """
    email_clean = email.strip().lower()
    full_name_clean = full_name.strip()

    if not full_name_clean or not email_clean or not password:
        return False, "All fields are required."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if email is already taken
        cursor.execute('SELECT id FROM users WHERE email = ?', (email_clean,))
        if cursor.fetchone():
            conn.close()
            return False, "An account with this email address already exists."

        # Hash password securely using PBKDF2/scrypt
        password_hash = generate_password_hash(password)

        cursor.execute('''
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', (full_name_clean, email_clean, password_hash, role))
        conn.commit()
        conn.close()
        return True, "Account successfully created! You may now sign in."
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}"


def verify_user(email, password):
    """
    Verify user credentials for login.
    Returns: (user_record or None, error_message or None)
    """
    email_clean = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email_clean,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return None, "No account found with this email address."

    # Validate the hashed password
    if not check_password_hash(user['password_hash'], password):
        conn.close()
        return None, "Incorrect password. Please verify and try again."

    # Update last login timestamp
    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()

    return user, None


def get_user_by_id(user_id):
    """
    Retrieve user record by primary key ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, role, created_at, last_login FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def log_traffic_detection(vehicle_count, cars, bikes, buses, trucks, density, recommended_green, mode='Video Detection'):
    """
    Store detection telemetry and signal recommendations into traffic_logs table.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO traffic_logs 
            (vehicle_count, cars, bikes, buses, trucks, density, recommended_green_time, source_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (vehicle_count, cars, bikes, buses, trucks, density, recommended_green, mode))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Database log error: {e}")
        return False


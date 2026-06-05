import os
import json
import uuid
import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    send_file,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from scripts.analysis import analyze_dataframe, correlation_summary
from scripts.data_cleaning import clean_dataframe
from scripts.report_generator import generate_pdf_report
from scripts.validation import validate_dataframe
from scripts.visualization import build_visualization_html

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "datasets"
CLEANED_DIR = BASE_DIR / "cleaned_data"
REPORT_DIR = BASE_DIR / "reports"
VIS_DIR = BASE_DIR / "visualizations"

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "database": os.environ.get("DB_NAME", "research_toolkit"),
}

for folder in [UPLOAD_DIR, CLEANED_DIR, REPORT_DIR, VIS_DIR]:
    folder.mkdir(exist_ok=True)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()


def insert_dataset_record(user_id, name, filename, rows, columns, summary):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO datasets (user_id, name, filename, rows, columns, summary) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, name, filename, rows, columns, json.dumps(summary)),
        )
        conn.commit()
        return cursor.lastrowid


def load_dataset_row(dataset_id, user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM datasets WHERE id = %s AND user_id = %s", (dataset_id, user_id)
        )
        return cursor.fetchone()


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            flash("Please complete all fields.", "warning")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password_hash),
                )
                conn.commit()
                flash("Account created successfully. Please login.", "success")
                return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Username or email already exists.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, password_hash FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Login failed. Check your email and password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, filename, upload_date, status, rows, columns FROM datasets WHERE user_id = %s ORDER BY upload_date DESC",
            (user["id"],),
        )
        datasets = cursor.fetchall()

    return render_template("dashboard.html", user=user, datasets=datasets)


@app.route("/profile")
def profile():
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        uploaded_file = request.files.get("dataset_file")
        dataset_name = request.form.get("dataset_name", "Experimental Dataset").strip()

        if not uploaded_file or uploaded_file.filename == "":
            flash("A dataset file is required.", "warning")
            return redirect(url_for("upload"))

        if not allowed_file(uploaded_file.filename):
            flash("Only CSV and Excel files are allowed.", "danger")
            return redirect(url_for("upload"))

        filename = secure_filename(f"{uuid.uuid4().hex}_{uploaded_file.filename}")
        file_path = UPLOAD_DIR / filename
        uploaded_file.save(file_path)

        try:
            if file_path.suffix.lower() in {".xlsx", ".xls"}:
                df = pd.read_excel(file_path, engine="openpyxl")
            else:
                df = pd.read_csv(file_path)
        except Exception as exc:
            file_path.unlink(missing_ok=True)
            flash(f"Unable to read file: {exc}", "danger")
            return redirect(url_for("upload"))

        clean_df, clean_summary = clean_dataframe(df)
        rows, columns = clean_df.shape
        dataset_id = insert_dataset_record(
            user["id"], dataset_name, filename, rows, columns, clean_summary
        )

        clean_path = CLEANED_DIR / f"cleaned_{dataset_id}.csv"
        clean_df.to_csv(clean_path, index=False)

        flash("Dataset uploaded successfully and queued for analysis.", "success")
        return redirect(url_for("dashboard"))

    return render_template("upload.html", user=user)


@app.route("/dataset/<int:dataset_id>")
def dataset_detail(dataset_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    record = load_dataset_row(dataset_id, user["id"])
    if not record:
        flash("Dataset not found.", "danger")
        return redirect(url_for("dashboard"))

    cleaned_path = CLEANED_DIR / f"cleaned_{dataset_id}.csv"
    preview = []
    columns = []
    if cleaned_path.exists():
        df = pd.read_csv(cleaned_path)
        preview = df.head(6).to_dict(orient="records")
        columns = df.columns.tolist()

    return render_template(
        "analysis.html",
        user=user,
        record=record,
        preview=preview,
        columns=columns,
    )


@app.route("/analyze/<int:dataset_id>")
def analyze(dataset_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    record = load_dataset_row(dataset_id, user["id"])
    if not record:
        flash("Dataset not found.", "danger")
        return redirect(url_for("dashboard"))

    cleaned_path = CLEANED_DIR / f"cleaned_{dataset_id}.csv"
    if not cleaned_path.exists():
        flash("Cleaned dataset not available.", "warning")
        return redirect(url_for("dashboard"))

    df = pd.read_csv(cleaned_path)
    summary = analyze_dataframe(df)
    correlations = correlation_summary(df)

    return render_template(
        "analysis.html",
        user=user,
        record=record,
        preview=df.head(8).to_dict(orient="records"),
        columns=df.columns.tolist(),
        analysis=summary,
        correlations=correlations,
    )


@app.route("/visualize/<int:dataset_id>")
def visualize(dataset_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    record = load_dataset_row(dataset_id, user["id"])
    if not record:
        flash("Dataset not found.", "danger")
        return redirect(url_for("dashboard"))

    cleaned_path = CLEANED_DIR / f"cleaned_{dataset_id}.csv"
    if not cleaned_path.exists():
        flash("Cleaned dataset not available.", "warning")
        return redirect(url_for("dashboard"))

    df = pd.read_csv(cleaned_path)
    plot_html = build_visualization_html(df)

    return render_template(
        "visualization.html",
        user=user,
        record=record,
        plot_html=plot_html,
    )


@app.route("/export_report/<int:dataset_id>")
def export_report(dataset_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    record = load_dataset_row(dataset_id, user["id"])
    if not record:
        flash("Dataset not found.", "danger")
        return redirect(url_for("dashboard"))

    cleaned_path = CLEANED_DIR / f"cleaned_{dataset_id}.csv"
    if not cleaned_path.exists():
        flash("Cleaned dataset not available.", "warning")
        return redirect(url_for("dashboard"))

    df = pd.read_csv(cleaned_path)
    validation_report = validate_dataframe(df)
    analysis_report = analyze_dataframe(df)
    visualizations = build_visualization_html(df, return_images=True)
    report_path = REPORT_DIR / f"research_report_{dataset_id}.pdf"
    generate_pdf_report(
        dataset_name=record["name"],
        cleaned_df=df,
        validation_report=validation_report,
        analysis_report=analysis_report,
        plot_images=visualizations,
        destination_path=report_path,
    )

    return send_file(str(report_path), as_attachment=True)


@app.errorhandler(413)
def file_too_large(error):
    flash("Uploaded file is too large. Maximum size is 12 MB.", "danger")
    return redirect(url_for("upload"))


if __name__ == "__main__":
    app.run(debug=True)

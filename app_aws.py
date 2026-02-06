import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "snapstream_secret_key"

# ---------------- AWS CONFIG ----------------
REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

users_table = dynamodb.Table("SnapUsers")
videos_table = dynamodb.Table("SnapVideos")
feedback_table = dynamodb.Table("SnapFeedback")

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:XXXXXXXXXXXX:snapstream-events"

# ---------------- FILE STORAGE ----------------
VIDEO_FOLDER = "static/videos"
THUMB_FOLDER = "static/thumbnails"
PROFILE_FOLDER = "static/profile_photos"

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)
os.makedirs(PROFILE_FOLDER, exist_ok=True)

VIDEO_CATEGORIES = [
    "Education", "Entertainment", "Technology",
    "Music", "Gaming", "Vlogs", "Sports", "Others"
]

# ---------------- HELPERS ----------------
def notify(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print("SNS Error:", e)

# ---------------- ROUTES ----------------

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")

    response = videos_table.scan()
    videos = {v["video_id"]: v for v in response.get("Items", [])}

    return render_template(
        "videos.html",
        videos=videos,
        saved_ids=session.get("watch_later", [])
    )

# ---------------- AUTH ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users_table.put_item(Item={
            "username": request.form["username"],
            "password": request.form["password"],
            "role": request.form["role"],
            "profile_photo": None
        })
        notify("New User Registered", request.form["username"])
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        res = users_table.get_item(Key={"username": username})
        user = res.get("Item")

        if not user or user["password"] != password:
            flash("Invalid credentials", "error")
            return redirect("/login")

        session["user"] = username
        session["role"] = user["role"]
        session.setdefault("watch_history", [])
        session.setdefault("viewed_videos", [])

        notify("User Login", username)
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user" in session:
        notify("User Logout", session["user"])
    session.clear()
    return redirect("/")

# ---------------- VIDEO UPLOAD ----------------

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session or session["role"] != "creator":
        return redirect("/login")

    if request.method == "POST":
        video_id = str(uuid.uuid4())

        video_file = request.files["video"]
        thumb_file = request.files["thumbnail"]

        video_name = f"{video_id}_{secure_filename(video_file.filename)}"
        thumb_name = f"{video_id}_{secure_filename(thumb_file.filename)}"

        video_file.save(os.path.join(VIDEO_FOLDER, video_name))
        thumb_file.save(os.path.join(THUMB_FOLDER, thumb_name))

        videos_table.put_item(Item={
            "video_id": video_id,
            "title": request.form["title"],
            "description": request.form["description"],
            "filename": video_name,
            "thumbnail": thumb_name,
            "uploader": session["user"],
            "category": request.form["category"],
            "views": 0,
            "uploaded_at": datetime.now().strftime("%d %b %Y")
        })

        notify("New Video Uploaded", request.form["title"])
        return redirect("/dashboard")

    return render_template("upload.html", categories=VIDEO_CATEGORIES)

# ---------------- FEEDBACK ----------------

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    if "user" not in session:
        return redirect("/login")

    fid = str(uuid.uuid4())
    feedback = request.form.get("feedback")

    feedback_table.put_item(Item={
        "id": fid,
        "username": session["user"],
        "feedback": feedback,
        "time": datetime.now().isoformat()
    })

    notify("New Feedback", f"{session['user']} sent feedback")
    flash("Feedback submitted", "success")
    return redirect("/settings")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    history = session.get("watch_history", [])
    saved_ids = session.get("watch_later", [])

    videos = videos_table.scan().get("Items", [])
    videos_dict = {v["video_id"]: v for v in videos}

    saved_videos = [
        {"id": vid, **videos_dict[vid]}
        for vid in saved_ids if vid in videos_dict
    ]

    return render_template(
        "dashboard.html",
        my_history=history,
        saved_videos=saved_videos
    )

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash


app = Flask(__name__)
app.secret_key = "snapstream_secret_key"

VIDEO_CATEGORIES = [
    "Education",
    "Entertainment",
    "Technology",
    "Music",
    "Gaming",
    "Vlogs",
    "Sports",
    "Others"
]


# ---------------- STORAGE ----------------
users = {}
videos = {}

UPLOAD_FOLDER = "static/videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- ROUTES ----------------


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template(
    "videos.html",
    videos=videos,
    saved_ids=session.get("watch_later", [])
)





@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- AUTH ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users[request.form["username"]] = {
            "password": request.form["password"],
            "role": request.form["role"],
            "profile_photo": None
        }
        return redirect("/login")

    return render_template("register.html")

@app.route("/upload-profile-photo", methods=["POST"])
def upload_profile_photo():
    if "user" not in session:
        return redirect("/login")

    photo = request.files.get("profile_photo")
    if not photo or photo.filename == "":
        return redirect("/profile")

    ext = photo.filename.split(".")[-1]
    filename = f"{session['user']}.{ext}"

    save_path = os.path.join("static/profile_photos", filename)
    photo.save(save_path)

    users[session["user"]]["profile_photo"] = filename

   
    return redirect("/profile")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = users.get(username)

        if not user:
            flash("User not registered. Please create an account.", "error")
            return redirect("/login")

        if user["password"] != password:
            flash("Incorrect password. Please try again.", "error")
            return redirect("/login")

        # Successful login
        session["user"] = username
        session["role"] = user["role"]
        session.setdefault("viewed_videos", [])
        session.setdefault("watch_history", [])

        return redirect("/dashboard")

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect("/login")
    return render_template("settings.html")
@app.route("/toggle-theme")
def toggle_theme():
    if "user" not in session:
        return redirect("/login")

    # Toggle between dark and light
    current = session.get("theme", "dark")
    session["theme"] = "light" if current == "dark" else "dark"

    return redirect("/settings")
@app.route("/switch-account")
def switch_account():
    session.clear()
    return redirect("/login")
@app.route("/clear-history")
def clear_history():
    if "user" not in session:
        return redirect("/login")

    session["watch_history"] = []
    return redirect("/settings")
@app.route("/change-password", methods=["POST"])
def change_password():
    if "user" not in session:
        return redirect("/login")

    current = request.form.get("current_password")
    new = request.form.get("new_password")

    username = session["user"]
    user = users.get(username)

    if not user or user["password"] != current:
        flash("Current password is incorrect.", "error")
        return redirect("/settings")

    users[username]["password"] = new
    flash("Password updated successfully.", "success")
    return redirect("/settings")

@app.route("/change-username", methods=["POST"])
def change_username():
    if "user" not in session:
        return redirect("/login")

    new_username = request.form.get("new_username")
    old_username = session["user"]

    if not new_username:
        flash("Username cannot be empty.", "error")
        return redirect("/settings")

    if new_username in users:
        flash("Username already exists.", "error")
        return redirect("/settings")

    users[new_username] = users.pop(old_username)
    session["user"] = new_username

    for video in videos.values():
        if video["uploader"] == old_username:
            video["uploader"] = new_username

    flash("Username updated successfully.", "success")
    return redirect("/settings")


@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    if "user" not in session:
        return redirect("/login")

    feedback = request.form.get("feedback")

    if not feedback:
        flash("Feedback cannot be empty.", "error")
        return redirect("/settings")

    print(f"[FEEDBACK] {session['user']}: {feedback}")
    flash("Thank you for your feedback!", "success")
    return redirect("/settings")


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    role = session.get("role")

    uploads = [
        v for v in videos.values()
        if v["uploader"] == username
    ]

    watch_count = len(session.get("watch_history", []))

    return render_template(
    "profile.html",
    username=username,
    role=role,
    total_uploads=len(uploads),
    total_watched=watch_count,
    users=users
)


@app.route("/help")
def help_page():
    return render_template("help.html")
@app.route("/my-videos")
def my_videos():
    if "user" not in session or session.get("role") != "creator":
        return redirect("/home")

    username = session["user"]

    creator_videos = {
        vid: v for vid, v in videos.items()
        if v["uploader"] == username
    }

    return render_template(
        "my_videos.html",
        videos=creator_videos
    )
@app.route("/delete-video/<video_id>")
def delete_video(video_id):
    if "user" not in session or session.get("role") != "creator":
        return redirect("/home")

    video = videos.get(video_id)
    if not video or video["uploader"] != session["user"]:
        return redirect("/my-videos")

    # Remove file
    try:
        os.remove(video["path"])
        os.remove(video["thumbnail"])
    except:
        pass

    videos.pop(video_id)
    return redirect("/my-videos")
@app.route("/edit-video/<video_id>", methods=["POST"])
def edit_video(video_id):
    if "user" not in session or session.get("role") != "creator":
        return redirect("/home")

    video = videos.get(video_id)
    if not video or video["uploader"] != session["user"]:
        return redirect("/my-videos")

    video["title"] = request.form.get("title")
    video["description"] = request.form.get("description")

    return redirect("/my-videos")
@app.route("/creator-support")
def creator_support():
    if "user" not in session or session.get("role") != "creator":
        return redirect("/home")

    return render_template("creator_support.html")

# ---------------- VIDEOS ----------------




@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session or session["role"] != "creator":
        return redirect("/login")

    if request.method == "POST":
        video_id = str(uuid.uuid4())

        # Save video
        video_file = request.files["video"]
        video_filename = video_id + "_" + video_file.filename
        video_file.save(os.path.join("static/videos", video_filename))

        # Save thumbnail
        thumb_file = request.files["thumbnail"]
        thumb_filename = video_id + "_" + thumb_file.filename
        thumb_file.save(os.path.join("static/thumbnails", thumb_filename))
          
        category = request.form.get("category")

        videos[video_id] = {
            "title": request.form["title"],
            "description": request.form["description"],
            "filename": video_filename,
            "thumbnail": thumb_filename,
            "uploader": session["user"],
            "category": category,
            "views": 0,
            "uploaded_at": datetime.now().strftime("%d %b %Y")
        }

        return redirect("/dashboard")

    return render_template("upload.html", categories=VIDEO_CATEGORIES)

@app.route("/save-video/<video_id>")
def save_video(video_id):
    if "user" not in session:
        return redirect("/login")

    watch_later = session.get("watch_later", [])

    if video_id not in watch_later:
        watch_later.insert(0, video_id)  # newest first

    session["watch_later"] = watch_later
    return redirect(request.referrer or "/home")

@app.route("/remove-saved/<video_id>")
def remove_saved(video_id):
    if "user" not in session:
        return redirect("/login")

    watch_later = session.get("watch_later", [])

    if video_id in watch_later:
        watch_later.remove(video_id)

    session["watch_later"] = watch_later
    return redirect("/home")



@app.route("/stream/<video_id>")
def stream(video_id):
    if "user" not in session:
        return redirect("/login")

    video = videos.get(video_id)
    if not video:
        return "Video not found"

    # -------- INIT SESSION KEYS (VERY IMPORTANT) --------
    if "viewed_videos" not in session:
        session["viewed_videos"] = []

    if "watch_history" not in session:
        session["watch_history"] = []

    # -------- UNIQUE VIEW PER USER --------
    if video_id not in session["viewed_videos"]:
        video["views"] += 1
        session["viewed_videos"].append(video_id)

    # -------- UNIQUE WATCH HISTORY --------
    history = session["watch_history"]

    # Remove old entry if exists
    history = [h for h in history if h["id"] != video_id]

    # Add updated entry at top
    history.insert(0, {
        "id": video_id,
        "title": video["title"],
        "thumbnail": video.get("thumbnail"),
        "category": video.get("category", "Others"),
        "views": video["views"],
        "watched_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
    })

    session["watch_history"] = history

    return render_template("stream.html", video=video)



# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    my_history = session.get("watch_history", [])

    saved_ids = session.get("watch_later", [])
    saved_videos = [
        {"id": vid, **videos[vid]}
        for vid in saved_ids if vid in videos
    ]

    return render_template(
        "dashboard.html",
        my_history=my_history,
        saved_videos=saved_videos
    )

@app.route("/search")
def search():
    if "user" not in session:
        return redirect("/login")

    query = request.args.get("q", "").lower().strip()

    if not query:
        return redirect("/home")

    filtered_videos = {
        vid: video for vid, video in videos.items()
        if query in video["title"].lower()
    }

    return render_template(
        "videos.html",
        videos=filtered_videos,
        saved_ids=session.get("watch_later", []),
        search_query=query
    )


    
    


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)

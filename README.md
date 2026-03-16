# SnapStream 🎬

SnapStream is a cloud-ready video streaming platform built using Flask and AWS services.  
The project demonstrates how a locally hosted application can be migrated to AWS using core cloud services.

---

## 🔧 Tech Stack

**Backend**
- Python
- Flask

**Frontend**
- HTML
- CSS
- JavaScript

**Cloud Services (AWS)**
- Amazon EC2
- Amazon DynamoDB
- Amazon SNS
- AWS IAM

---

## 🚀 Features

- User registration and login
- Role-based access (Viewer / Creator)
- Video upload with thumbnails
- Video streaming and view tracking
- Watch history and Watch Later
- Search videos by title
- User profile with profile photo
- Feedback system with email notifications
- Dark / Light mode UI
- Creator dashboard (upload, edit, delete videos)

---

## ☁️ AWS Architecture

- **EC2** hosts the Flask application
- **DynamoDB** stores users, videos, and metadata
- **SNS** sends notifications for:
  - User login
  - Logout
  - Feedback submission
  - Video uploads
- **IAM Roles** manage secure access between services

Media files (videos, thumbnails, profile photos) are stored locally on the EC2 instance for simplicity.

---

Run SnapStream Locally
---
1. Clone the repository
   
```
git clone https://github.com/Utkarsh-Garg00/AWS_CAPSTONE_PROJECT-SNAPSTREAM.git


cd AWS_CAPSTONE_PROJECT-SNAPSTREAM
```
2. Create virtual environment (optional but recommended)

Windows
```
python -m venv .venv
.venv\Scripts\activate
```
Linux / Mac
```
python3 -m venv .venv
source .venv/bin/activate
```
3. Install dependencies
```
pip install -r requirements.txt
```
4. Run the application
 ```
python app.py
```
6. Open in browser
http://127.0.0.1:5000
---
Run AWS Version
---

After configuring AWS services (EC2, DynamoDB, SNS):
```
python app_aws.py
```
Requirements

Python 3.8+

pip

Git

from flask import Flask, render_template, request, jsonify
from ultralytics import YOLO
from PIL import Image
import io
import time
import cv2
import os
import threading
import winsound
import pandas as pd
import matplotlib.pyplot as plt

# 🔽 NEW: Import auto downloader
from download_model import download_model

# Import the notification functions and config variables
from notifications import send_sms_alert, send_email_alert, upload_image_to_cloudinary
import config
app=Flask(__name__)
last_smoke_value=0
fire_detected=False

# =====================================================
# 🔥 AI MODEL AUTO DOWNLOAD + LOAD (IMPORTANT SECTION)
# =====================================================

MODEL_PATH = "model/best.pt"

# Step 1: Download model automatically if missing
if not os.path.exists(MODEL_PATH):
    print("Custom model not found. Downloading from Google Drive...")
    download_model()

# Step 2: Load the model safely
try:
    model = YOLO(MODEL_PATH)
    print("✅ Custom Fire Detection Model Loaded Successfully!")
except Exception as e:
    print("❌ CRITICAL ERROR: Could not load the YOLOv8 model.")
    print("Details:", e)
    model = None

# =====================================================
# End of AI Model Setup
# =====================================================


# --- Alert Cooldown Logic ---
ALERT_COOLDOWN_SECONDS = 60  # Cooldown set to 1 minute
last_alert_time = 0
# --------------------------



def play_alarm():
    for _ in range(5):  # Beep 5 times
        winsound.Beep(1000, 500)  # frequency, duration

@app.route("/")
def home():
    return render_template("dashboard.html")




@app.route('/analytics')
def analytics():
    df = pd.read_csv('dataset/forestfires.csv')

    plt.figure()
    df.groupby('month')['area'].sum().plot(kind='bar')
    plt.title("Total Burned Area by Month")
    plt.xlabel("Month")
    plt.ylabel("Burned Area (hectares)")

    graph_path = "static/graph.png"
    plt.savefig(graph_path)
    plt.close()

    return render_template("analytics.html", graph=graph_path)
@app.route('/sensor', methods=['POST'])
def sensor():
    global last_smoke_value
    global fire_detected
    data = request.json
    smoke =int(data.get("smoke"))
    latitude = 17.3850
    longitude=78.4867
    last_smoke_value=smoke
    

    print("Smoke Value:", smoke)
   
    if smoke < 2000:
       fire_detected = False

    if smoke > 2000 and not fire_detected:
        fire_detected=True
        print("🔥 FIRE DETECTED!")
        
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("Camera not avalible")
            return jsonify({"status": "camera_error"})
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
        time.sleep(2)
     
        
        ret,frame = cap.read()
        print("Camera status:", ret)
        if ret:
            image_path = "static/fire_capture.jpg"
            cv2.imwrite(image_path, frame, [cv2.IMWRITE_JPEG_QUALITY,95])
            print("image captured:",image_path)
             
            with open(image_path, "rb") as img:
                image_bytes = img.read()
                
            image_url = upload_image_to_cloudinary(image_bytes)
            
            
            print("Image URL:", image_url)
            print("sending SMS...")
            sms_status = send_sms_alert(
                config.TWILIO_RECIPIENT_PHONE,
                latitude,
                longitude,
                image_url
            )
            print("SMS Status:", sms_status)
            
        cap.release()

    return jsonify({"status": "ok"})

@app.route("/latest")
def latest():
    return jsonify({"smoke": last_smoke_value})



@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# This block of code allows us to run the app directly
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000,debug=True)


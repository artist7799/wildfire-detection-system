# This file contains all functions related to sending alerts and notifications.

import config

from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import cloudinary
import cloudinary.uploader

# --- Cloudinary Configuration ---
try:
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET
    )
except Exception as e:
    print(f"Warning: Cloudinary is not configured. Check your credentials in config.py. Details: {e}")
# -----------------------------


def upload_image_to_cloudinary(image_bytes):
    """
    Uploads an image to Cloudinary and returns its public URL.
    Args:
        image_bytes (bytes): The image data to upload.
    Returns:
        str: The secure URL of the uploaded image, or None if the upload fails.
    """
    try:
        # Use cloudinary.uploader.upload to upload the image from memory
        upload_result = cloudinary.uploader.upload(image_bytes)
        # The secure_url is the https link to the image
        return upload_result.get('secure_url')
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None


def send_sms_alert(recipient, latitude, longitude, image_url=None):
    """
    Sends an SMS alert using Twilio with location and an optional image link.
    """
    try:
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Create a Google Maps link from the coordinates
        maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        
        # Construct the message body
        body = f"FIRE ALERT! Potential fire detected at your location.\n\n"
        body += f"Coordinates: {latitude}, {longitude}\n"
        body += f"View on Map: {maps_link}"
        
        # Add the image link if it exists
        if image_url:
            body += f"\n\nEvidence Photo: {image_url}"

        message = client.messages.create(
            body=body,
            from_=config.TWILIO_PHONE_NUMBER,
            to=recipient
        )
        return f"SMS Sent (SID): {message.sid}"
    except Exception as e:
        return f"Error sending SMS: {e}"


def send_email_alert(recipient, latitude, longitude, image_url=None):
    """
    Sends an email alert using SendGrid with location and an optional image link.
    """
    try:
        maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        
        # Construct the HTML content for the email
        html_content = f"""
        <html>
        <body>
            <h1>Fire Alert!</h1>
            <p>A potential fire has been detected by your automated system.</p>
            <h2>Location Details:</h2>
            <ul>
                <li>Latitude: {latitude}</li>
                <li>Longitude: {longitude}</li>
            </ul>
            <p><a href="{maps_link}" style="font-size: 16px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">View Location on Google Maps</a></p>
        """
        
        # Add the evidence image if the URL exists
        if image_url:
            html_content += f"""
            <h2>Evidence Photo:</h2>
            <p>The following image was captured at the time of detection:</p>
            <img src="{image_url}" alt="Fire Detection Evidence" style="max-width: 100%; height: auto;">
            """
        
        html_content += "</body></html>"

        message = Mail(
            from_email=config.SENDER_EMAIL,
            to_emails=recipient,
            subject='URGENT: Fire Alert Detected!',
            html_content=html_content
        )
        
        sg = SendGridAPIClient(config.SENDGRID_API_KEY)
        response = sg.send(message)
        return f"Email Sent (Status Code): {response.status_code}"
    except Exception as e:
        return f"Error sending email: {e}"


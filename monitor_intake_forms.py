"""
Form Submission Emailer
Copyright (c) 2024 Mukhtaar Muhammad-Bailey

This software is licensed under the MIT License.
See the LICENSE file for details.
"""


import os
import time
import logging
import smtplib
from threading import Thread
from pymongo import MongoClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
import certifi
from dotenv import load_dotenv


# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Load environment variables
load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()

# Environment variables
MONGO_URI = os.getenv("MONGO_URI")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 465
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS").split(",")
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", 30))


# Initialize MongoDb client and access collection
client = MongoClient(MONGO_URI)
# MongoDB connection
db = client["test"]
collection = db["forms"]

# Constants for file validation
ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/gif"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# Utility for centralized exception handling
def handle_exception(context, error):
    logging.exception(f"Error in {context}: {error}")
    raise


def send_email(text_data, file_data=None, file_name=None):
    """
        Sends an email with form details in the body and an optional file attachment.

        Args:
            text_data (dict): Form data to include in the email body.
            file_data (bytes): Optional file data to attach.
            file_name (str): Name of the attached file.
        """


    try:
        # Extract form data
        subject = "New Customer Submission"

        # Construct the email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ", ".join(RECIPIENT_EMAILS)
        msg['Subject'] = subject

        # Add form data as plain text in the email body
        body = "\n".join(f"{key}: {value}" for key, value in text_data.items() if key != "uploadedFile")
        msg.attach(MIMEText(body, 'plain'))



        # Attach a file, if provided
        if file_data and file_name:

            if len(file_data) > MAX_FILE_SIZE:
                logging.warning(f"File {file_name} exceeds the size limit. Email not sent")

            else:
                mime_type, _ = mimetypes.guess_type(file_name)
                main_type, sub_type = (mime_type or "application/octet-stream").split("/", 1)

                if mime_type not in ALLOWED_MIME_TYPES:
                    logging.warning(f"Unsupported file type: {mime_type}")
                    return
                else:
                    mime_base = MIMEBase(main_type, sub_type)
                    mime_base.set_payload(file_data)
                    encoders.encode_base64(mime_base)
                    mime_base.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
                    msg.attach(mime_base)

        # Connect to SMTP server and send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            logging.info(f"Email sent to")

    except smtplib.SMTPException as e:
        handle_exception("SMTP error occurred", e)

    except Exception as e:
        handle_exception("Error sending email", e)


def sent_email_async(*args, **kwargs):
    """"
    Sends an email asynchronously to avoid blocking the main thread.

    Args:
        *args, **kwargs: Arguments to pass to the `send_email` function.
    """

    Thread(target=send_email, args=args, kwargs=kwargs).start()


def fetch_new_forms(collection, last_check_id):
    """
        Fetches new forms from the MongoDB collection based on the last processed ID.

        Args:
            collection: MongoDB collection object.
            last_check_id: ID of the last processed form.

        Returns:
            Cursor containing the new form submissions.
        """

    query = {"_id": {"$gt": last_check_id}} if last_check_id else {}
    return collection.find(query).sort("_id", 1)


def process_form(form):
    """
        Processes a form, extracting customer data and handling file attachments.

        Args:
            form (dict): A MongoDB document containing form submission data.

        Returns:
            tuple: (customer_info, file_attachment, file_name)
        """

    customer_data_keys = [
        "name", "email", "phone", "communicationMethod", "contactTime",
        "projectType", "projectDescription", "uploadedFile", "createdAt"
    ]

    # Extract customer Information
    customer_info = {key: form.get(key, "N/A") for key in customer_data_keys}

    # Handle file attachments
    file_attachment = None
    file_name = None

    if "uploadedFile" in form:
        uploaded_file = form["uploadedFile"]
        if uploaded_file:
            file_data = uploaded_file.get("data")
            file_name = uploaded_file.get("filename")

            if file_data and file_name:
                file_attachment = file_data
            else:
                logging.warning(f"Invalid or unsupported file: {file_name}")
        else:
            logging.info("No file uploaded")

    return customer_info, file_attachment, file_name


def monitor_new_submission():
    """
    Monitors the MongoDB collection for new form submissions and processes them.
    """
    seen_ids = set()
    last_checked_id = None

    logging.info("Monitoring MongoDB for new form submissions...")
    while True:
        try:
            # Fetch new forms from the database
            new_forms = fetch_new_forms(collection, last_checked_id)

            for form in new_forms:
                form_name = str(form["name"])
                form_id = str(form["_id"])
                last_checked_id = form["_id"]

                # Skip already seen forms
                if form_id in seen_ids:
                    continue

                seen_ids.add(form_id)
                logging.info(f"Processing new submission name: {form_name} with ID: {form_id} ")

                # Process form and send email
                customer_info, file_attachment, file_name = process_form(form)
                send_email(customer_info, file_attachment, file_name)
            time.sleep(POLLING_INTERVAL)
        except Exception as e:
            handle_exception("Error monitoring submission:", e)
            time.sleep(30)


if __name__ == "__main__":
    print("Monitoring new form submissions")
    monitor_new_submission()
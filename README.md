## **License**

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

Form Submission Emailer:

This project monitors a MongoDB collection for new form submissions and sends an email notification with the form data and any attached files. It is designed for businesses to automatically handle customer inquiries and ensure prompt communication.

Features:

- Monitors MongoDB for new form submissions in real-time.
- Sends email notifications with form details in the body.
- Includes file attachments (e.g., PDFs, images) in emails.
- Logs activities and errors to a file (app.log) for easy debugging.
- Asynchronous email sending to prevent blocking the application.


Requirements:

Python 3.8+
MongoDB (cloud-hosted or local instance)
SMTP Email Server (e.g., Gmail)
Python Libraries:
pymongo
smtplib
email
dotenv
certifi

Installation:

- Clone the repository:
git clone https://github.com/Fearlesser/form-submission-emailer.git

- Navigate to the project directory:
cd form-submission-emailer

- Install the required Python packages:
pip install -r requirements.txt


Create a .env file for environment variables:
- MONGO_URI=your_mongo_connection_string
- EMAIL_ADDRESS=your_email@gmail.com
- GOOGLE_PASSWORD=your_app_specific_password
- RECIPIENT_EMAIL=recipient_email@gmail.com
- POLLING_INTERVAL=30

Run the application:
python app.py

Usage:
Ensure your MongoDB instance is running and has a forms collection with customer submissions.
The script monitors the collection and sends an email for each new form submission.
Emails include form details in the body and any attached files.

Configuration:
The application uses environment variables for secure configuration. Below are the required variables:

MONGO_URI: MongoDB connection string.
EMAIL_ADDRESS: The sender's email address.
GOOGLE_PASSWORD: The app-specific password for your email account.
RECIPIENT_EMAIL: The recipient's email address.
POLLING_INTERVAL: Time interval (in seconds) to check for new submissions.

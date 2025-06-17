from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect, url_for
from datetime import datetime
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this')

# Email Configuration - Load from environment variables
EMAIL_CONFIG = {
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
    'sender_email': os.environ.get('SENDER_EMAIL'),
    'sender_password': os.environ.get('SENDER_PASSWORD'),
    'admin_email': os.environ.get('ADMIN_EMAIL')
}

@app.route('/test-email')
def test_email():
    if validate_email_config():
        return "Email configuration looks good!"
    else:
        return "Email configuration is missing or incomplete"

# Admin credentials
ADMIN_CREDENTIALS = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'password': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
}

# Print configuration status (for debugging)
print("Email Configuration Status:")
for key, value in EMAIL_CONFIG.items():
    if key == 'sender_password':
        print(f"{key}: {'✓ Set' if value else '✗ Missing'}")
    else:
        print(f"{key}: {value if value else '✗ Missing'}")

# Directory to store membership applications
DATA_DIR = 'membership_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def validate_email_config():
    """Check if email configuration is properly set"""
    required_keys = ['sender_email', 'sender_password', 'admin_email']
    missing_keys = []
    for key in required_keys:
        if not EMAIL_CONFIG[key]:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"Missing email configuration: {', '.join(missing_keys)}")
        return False
    return True

def send_email_notification(membership_data, json_filepath):
    """Send email notification to admin when new membership is submitted"""
    if not validate_email_config():
        print("Email configuration incomplete. Skipping email notification.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['admin_email']
        msg['Subject'] = f"New KALAA Membership Application - {membership_data['name']}"
        
        # Create email body
        body = f"""
New Membership Application Received
==================================

Submission Date: {membership_data['submission_date']}
Name: {membership_data['name']}
Spouse Name: {membership_data.get('spouse_name', 'N/A')}
Email: {membership_data['email']}
Phone: {membership_data['phone']}
Address: {membership_data['address']}
Place: {membership_data['place']}
Membership Type: {membership_data['membership_type']}

Children Information:
"""
        
        if membership_data['children']:
            for i, child in enumerate(membership_data['children'], 1):
                body += f"""
Child {i}:
  Name: {child['name']}
  Date of Birth: {child.get('date_of_birth', 'N/A')}
  Sex: {child.get('sex', 'N/A')}
                """
        else:
            body += "\n        No children information provided."
        
        body += f"""

Please review this application in the admin panel.
The complete application data has been saved to: {json_filepath}
"""
        
        # Attach body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()  # Enable security
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['admin_email'], text)
        server.quit()
        
        print("✓ Admin notification email sent successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")
        return False

def send_confirmation_email(membership_data):
    """Send confirmation email to the member who submitted the application"""
    if not validate_email_config():
        print("Email configuration incomplete. Skipping confirmation email.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = membership_data['email']
        msg['Subject'] = "KALAA Membership Application - Confirmation"
        
        membership_types = {
            'annual_individual': 'Annual Individual Membership - $5',
            'lifetime_individual': 'Lifetime Individual Membership - $50',
            'lifetime_family': 'Lifetime Family Membership - $100'
        }
        
        body = f"""
Dear {membership_data['name']},

Thank you for your interest in joining the KALAA community!

We have successfully received your membership application with the following details:

Application Details:
- Name: {membership_data['name']}
- Email: {membership_data['email']}
- Phone: {membership_data['phone']}
- Membership Type: {membership_types.get(membership_data['membership_type'], 'Unknown')}
- Submission Date: {membership_data['submission_date']}

What's Next?
============
1. Our team will review your application
2. You will receive payment instructions via email
3. Once payment is confirmed, your membership will be activated

If you have any questions, please don't hesitate to contact us.

Best regards,
KALAA Community Team

---
This is an automated message. Please do not reply to this email.
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], membership_data['email'], text)
        server.quit()
        
        print("✓ Confirmation email sent successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error sending confirmation email: {str(e)}")
        return False

# Add the form submission route with better error handling
@app.route('/submit_membership', methods=['POST'])
def submit_membership():
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'address', 'place', 'membership_type']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field.replace("_", " ").title()}'})
        
        # Get form data
        membership_data = {
            'submission_date': datetime.now().isoformat(),
            'name': request.form.get('name').strip(),
            'spouse_name': request.form.get('spouse_name', '').strip(),
            'address': request.form.get('address').strip(),
            'place': request.form.get('place').strip(),
            'phone': request.form.get('phone').strip(),
            'email': request.form.get('email').strip().lower(),
            'membership_type': request.form.get('membership_type'),
            'children': []
        }
        
        # Process children data
        child_names = request.form.getlist('child_name[]')
        child_dobs = request.form.getlist('child_dob[]')
        child_sexes = request.form.getlist('child_sex[]')
        
        for i in range(len(child_names)):
            if child_names[i] and child_names[i].strip():
                child_data = {
                    'name': child_names[i].strip(),
                    'date_of_birth': child_dobs[i] if i < len(child_dobs) else '',
                    'sex': child_sexes[i] if i < len(child_sexes) else ''
                }
                membership_data['children'].append(child_data)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"membership_{timestamp}_{membership_data['name'].replace(' ', '_')}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(membership_data, f, indent=4, ensure_ascii=False)
        
        # Try to send email notifications
        email_success = send_email_notification(membership_data, filepath)
        confirmation_success = send_confirmation_email(membership_data)
        
        # Prepare response message
        if email_success and confirmation_success:
            message = 'Your membership request has been sent successfully! You will receive a confirmation email shortly.'
        elif email_success:
            message = 'Your membership request has been sent successfully! However, we could not send you a confirmation email.'
        else:
            message = 'Your membership request has been saved successfully! Our team will contact you soon via phone.'
        
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        print(f"Error processing membership submission: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while processing your request. Please try again.'})

# Keep all your existing routes (admin_login, admin_memberships, etc.)
# ... [rest of your existing code]

if __name__ == '__main__':
    print("\n" + "="*60)
    print("KALAA MEMBERSHIP APPLICATION")
    print("="*60)
    print("Make sure you have configured the .env file with:")
    print("✓ SENDER_EMAIL (your Gmail address)")
    print("✓ SENDER_PASSWORD (Gmail app password)")
    print("✓ ADMIN_EMAIL (where to receive applications)")
    print("✓ ADMIN_USERNAME & ADMIN_PASSWORD")
    print("="*60)
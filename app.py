from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Email Configuration - UPDATE THESE WITH YOUR DETAILS
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # For Gmail
    'smtp_port': 587,
    'sender_email': 'your-community-email@gmail.com',  # Your community email
    'sender_password': 'your-app-password',  # Gmail App Password (not regular password)
    'admin_email': 'admin@kalaa-community.com'  # Where to receive membership applications
}

# Directory to store membership applications
DATA_DIR = 'membership_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def send_email_notification(membership_data, json_filepath):
    """
    Send email notification to admin when new membership is submitted
    """
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
        
        Please review this application in the admin panel: http://your-domain.com/admin/memberships
        
        The complete application data has been saved to: {json_filepath}
        """
        
        # Attach body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the JSON file
        with open(json_filepath, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(json_filepath)}',
        )
        msg.attach(part)
        
        # Create SMTP session
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()  # Enable security
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['admin_email'], text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_confirmation_email(membership_data):
    """
    Send confirmation email to the member who submitted the application
    """
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
        
        return True
        
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False

@app.route('/')
def index():
    return send_from_directory('.', 'membership.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/submit_membership', methods=['POST'])
def submit_membership():
    try:
        # Get form data
        membership_data = {
            'submission_date': datetime.now().isoformat(),
            'name': request.form.get('name'),
            'spouse_name': request.form.get('spouse_name'),
            'address': request.form.get('address'),
            'place': request.form.get('place'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'membership_type': request.form.get('membership_type'),
            'children': []
        }
        
        # Process children data
        child_names = request.form.getlist('child_name[]')
        child_dobs = request.form.getlist('child_dob[]')
        child_sexes = request.form.getlist('child_sex[]')
        
        for i in range(len(child_names)):
            if child_names[i].strip():  # Only add if name is not empty
                membership_data['children'].append({
                    'name': child_names[i],
                    'date_of_birth': child_dobs[i] if i < len(child_dobs) else '',
                    'sex': child_sexes[i] if i < len(child_sexes) else ''
                })
        
        # Save to file
        filename = f"membership_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(membership_data, f, indent=4)
        
        # Send email notifications
        email_success = True
        confirmation_success = True
        
        # Send notification to admin
        if not send_email_notification(membership_data, filepath):
            email_success = False
        
        # Send confirmation to member
        if not send_confirmation_email(membership_data):
            confirmation_success = False
        
        # Prepare response message
        if email_success and confirmation_success:
            message = 'Your membership request has been sent successfully! You will receive a confirmation email shortly.'
        elif email_success:
            message = 'Your membership request has been sent successfully! However, we could not send you a confirmation email.'
        else:
            message = 'Your membership request has been saved, but there was an issue sending email notifications. Our team will contact you soon.'
        
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

@app.route('/admin/memberships')
def admin_memberships():
    """Admin route to view all membership applications"""
    memberships = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                memberships.append(data)
    
    # Sort by submission date (newest first)
    memberships.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
    
    # Create a simple HTML page for admin
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Membership Applications</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
        <style>
            body { background-color: #f8f9fa; }
            .admin-header { background: linear-gradient(135deg, #2c5aa0 0%, #1e3a6f 100%); color: white; padding: 2rem 0; margin-bottom: 2rem; }
            .membership-card { background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 2rem; overflow: hidden; }
            .card-header { background: #2c5aa0; color: white; padding: 1rem 1.5rem; font-weight: bold; }
            .card-body { padding: 1.5rem; }
            .info-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0; }
            .info-label { font-weight: bold; color: #333; }
            .info-value { color: #666; }
            .children-section { background: #f8f9fa; border-radius: 5px; padding: 1rem; margin-top: 1rem; }
            .child-item { background: white; border-radius: 5px; padding: 0.75rem; margin-bottom: 0.5rem; border-left: 4px solid #2c5aa0; }
            .membership-type { display: inline-block; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; text-transform: uppercase; font-size: 0.8rem; }
            .type-annual { background: #28a745; color: white; }
            .type-lifetime { background: #ffc107; color: #333; }
            .no-data { text-align: center; color: #666; font-style: italic; padding: 2rem; }
        </style>
    </head>
    <body>
        <div class="admin-header">
            <div class="container">
                <h1><i class="fas fa-users-cog"></i> KALAA Membership Applications</h1>
                <p class="mb-0">Administrative Dashboard - View and manage membership applications</p>
            </div>
        </div>
        <div class="container">
    """
    
    if memberships:
        html_content += f"""
        <div class="row">
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Total Applications:</strong> {len(memberships)}
                </div>
            </div>
        </div>
        """
        
        for membership in memberships:
            membership_type_class = "type-annual" if membership.get('membership_type') == 'annual_individual' else "type-lifetime"
            membership_type_text = {
                'annual_individual': 'Annual Individual - $5',
                'lifetime_individual': 'Lifetime Individual - $50',
                'lifetime_family': 'Lifetime Family - $100'
            }.get(membership.get('membership_type', ''), 'Unknown')
            
            html_content += f"""
            <div class="membership-card">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <span><i class="fas fa-user"></i> {membership.get('name', 'N/A')}</span>
                        <small>{membership.get('submission_date', '')[:10]}</small>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <div class="info-row">
                                <span class="info-label">Name:</span>
                                <span class="info-value">{membership.get('name', 'N/A')}</span>
                            </div>
            """
            
            if membership.get('spouse_name'):
                html_content += f"""
                            <div class="info-row">
                                <span class="info-label">Spouse:</span>
                                <span class="info-value">{membership.get('spouse_name')}</span>
                            </div>
                """
            
            html_content += f"""
                            <div class="info-row">
                                <span class="info-label">Email:</span>
                                <span class="info-value">{membership.get('email', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Phone:</span>
                                <span class="info-value">{membership.get('phone', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Address:</span>
                                <span class="info-value">{membership.get('address', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Place:</span>
                                <span class="info-value">{membership.get('place', 'N/A')}</span>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <span class="membership-type {membership_type_class}">{membership_type_text}</span>
                                <div class="mt-3">
                                    <small class="text-muted">
                                        <i class="fas fa-calendar"></i>
                                        Submitted: {membership.get('submission_date', '')[:19].replace('T', ' ')}
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
            """
            
            if membership.get('children') and len(membership.get('children', [])) > 0:
                html_content += """
                    <div class="children-section">
                        <h6><i class="fas fa-child"></i> Children Information:</h6>
                """
                for child in membership.get('children', []):
                    if child.get('name'):
                        html_content += f"""
                        <div class="child-item">
                            <div class="row">
                                <div class="col-md-4">
                                    <strong>{child.get('name', '')}</strong>
                                </div>
                                <div class="col-md-4">
                        """
                        if child.get('date_of_birth'):
                            html_content += f'<small><i class="fas fa-birthday-cake"></i> {child.get("date_of_birth")}</small>'
                        html_content += """
                                </div>
                                <div class="col-md-4">
                        """
                        if child.get('sex'):
                            html_content += f'<small><i class="fas fa-venus-mars"></i> {child.get("sex")}</small>'
                        html_content += """
                                </div>
                            </div>
                        </div>
                        """
                html_content += "</div>"
            
            html_content += """
                </div>
            </div>
            """
    else:
        html_content += """
        <div class="membership-card">
            <div class="card-body">
                <div class="no-data">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <h4>No Membership Applications</h4>
                    <p>No membership applications have been submitted yet.</p>
                </div>
            </div>
        </div>
        """
    
    html_content += """
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return html_content

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
from flask_mail import Mail, Message

app = Flask(__name__)

# ✅ Secret key for flashing messages (required for session-based features like flash)
app.secret_key = "secret-key-12345"  

# --- Email Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kranjaly2001@gmail.com'         # Replace with your email
app.config['MAIL_PASSWORD'] = 'bczh bxcj pofk zebp'       # Replace with your app password
app.config['MAIL_DEFAULT_SENDER'] = 'anjaly.anju7471@gmail.com'   # Replace with your email

mail = Mail(app)

# --- Routes ---

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/events/upcoming")
def upcoming_events():
    return render_template("events/upcoming.html")

@app.route("/events/past")
def past_events():
    return render_template("events/past.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        from_name = request.form.get("from_name")
        email = request.form.get("email")
        message_text = request.form.get("message")

        message_body = f"""
        New Contact Message

        Name: {from_name}
        Email: {email}
        Message:
        {message_text}
        """

        msg = Message(
            subject="New Contact Message - KALAA",
            recipients=["anjaly.anju7471@gmail.com"],
            body=message_body
        )
        mail.send(msg)

        # ✅ Flash success message
        flash("Your message has been sent successfully!")

        return redirect("/contact")

    return render_template("contact.html")


@app.route("/news")
def news():
    return render_template("news.html")

@app.route("/membership", methods=["GET", "POST"])
def membership():
    if request.method == "POST":
        name = request.form.get('name')
        spouse_name = request.form.get('spouse_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        place = request.form.get('place')
        membership_type = request.form.get('membership_type')

        # Compose the email content
        message_body = f"""
        New Membership Application Received

        Name: {name}
        Spouse Name: {spouse_name}
        Email: {email}
        Phone: {phone}
        Address: {address}
        Place: {place}
        Membership Type: {membership_type}
        """

        # Send the email
        msg = Message(
            subject="New Membership Application - KALAA",
            recipients=['anjaly.anju7471@gmail.com'],
            body=message_body
        )
        mail.send(msg)

        # ✅ Print message to console
        print("✅ Membership form submitted by:", name)
        print("📧 Email sent to: anjaly.anju7471@gmail.com")

        return redirect("/membership")

    return render_template("membership.html")


if __name__ == "__main__":
    app.run(debug=True)

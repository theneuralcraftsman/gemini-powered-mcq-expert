# server.py
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from db import initialize_database, generate_otp, hash_password, email_exists, get_user_data 
from db import insert_user, update_verification_status, login_user, update_password, delete_user
import datetime


app = Flask(__name__)

# Configure Flask app
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'stemedies@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'syzabaaxsehanfjn'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'stemedies@gmail.com'  # Replace with your email

mail = Mail(app)

# Initialize the database
initialize_database()

def send_otp_email(email, otp):
    try:
        message = Message("OTP for Registration", recipients=[email])
        message.body = f"Your OTP for registration is: {otp} \n\nThis OTP has a validity of 2mins."
        mail.send(message)
        return True
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False
    

def send_reset_otp_email(email, otp):
    try:
        message = Message("OTP for Password Reset", recipients=[email])
        message.body = f"Your OTP for reset password is: {otp}"
        mail.send(message)
        return True
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False

users_db = {}

def clean_users_db():
    # Clean users_db when it has more than 2 entries
    if len(users_db) > 2:
        # Assuming you want to keep only the latest 2 entries
        sorted_entries = sorted(users_db.items(), key=lambda x: x[1]["otp_creation_time"], reverse=True)
        users_db.clear()
        users_db.update(dict(sorted_entries[:2]))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')  # Include the name field

    if email and password and name:
        if email_exists(email):
            return jsonify({"message": "Email already registered."}), 400

        users_db[email] = {"otp": generate_otp(), "verified": False, "otp_creation_time": datetime.datetime.now()}

        clean_users_db()  # Clean users_db

        hashed_password = hash_password(password)

        # For simplicity, storing the hashed password in the database (not suitable for production)
        insert_user(email, hashed_password, name, 0)  # 0 indicates not verified

        # Send OTP via email
        if send_otp_email(email, users_db[email]["otp"]):
            return jsonify({"message": "Registration successful. Please check your email for OTP."})
        else:
            return jsonify({"message": "Failed to send OTP. Please try again later."}), 500

    return jsonify({"message": "Invalid data provided."}), 401

@app.route('/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    user_otp = data.get('otp')

    if email and user_otp and email in users_db:
        stored_otp = users_db[email]["otp"]
        otp_creation_time = users_db[email]["otp_creation_time"]

        # Check if the OTP is not expired (2 minutes expiration time)
        if datetime.datetime.now() < otp_creation_time + datetime.timedelta(minutes=2):
            if stored_otp == user_otp:
                users_db[email]['verified'] = True
                update_verification_status(email)
                return jsonify({"message": "OTP verified successfully."})
            else:
                return jsonify({"message": "Invalid OTP."}), 400
        else:
            return jsonify({"message": "Expired OTP. Please request a new one."}), 400

    return jsonify({"message": "Invalid email or OTP."}), 400

# @app.route('/login', methods=['POST'])
# def login_old():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email and password:
        if login_user(email, password):
            return jsonify({"message": "Login successful."})
        else:
            return jsonify({"message": "Invalid credentials or user not verified."}), 401

    return jsonify({"message": "Invalid data provided."})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email and password:
        user_data = get_user_data(email)

        if user_data:
            if login_user(email, password):
                if user_data["verified"]:
                    return jsonify({"message": "Login successful."})
                
                else:
                    # User is not verified, send OTP for verification
                    new_otp = generate_otp()
                    users_db[email] = {"otp": new_otp, "verified": False, "otp_creation_time": datetime.datetime.now()}
                    clean_users_db()  # Clean users_db

                    # Send OTP via email
                    if send_otp_email(email, new_otp):
                        return jsonify({"message": "User not verified. OTP sent for verification."}), 403
                    else:
                        return jsonify({"message": "Failed to send OTP. Please try again later."}), 500
            else:
                return jsonify({"message": "Invalid credentials."}), 401
            
        else:
            return jsonify({"message": "Invalid credentials or user not found."}), 401

    return jsonify({"message": "Invalid data provided."}), 400


@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    email = data.get('email')

    
    if email:
        user_data = get_user_data(email)

        if user_data:
            if user_data["verified"]==0:
                # Generate a new OTP
                new_otp = generate_otp()
                users_db[email]["otp"] = new_otp
                users_db[email]["otp_creation_time"] = datetime.datetime.now()

                # Send OTP via email
                if send_otp_email(email, new_otp):
                    return jsonify({"message": "New OTP sent successfully."})
                else:
                    return jsonify({"message": "Failed to send new OTP. Please try again later."}), 500
            else:
                return jsonify({"message": "User already verified"}), 400
        else:
            return jsonify({"message": "User not registered"}), 400
    else:
        return jsonify({"message": "Email not found."}), 404



@app.route('/delete_user', methods=['DELETE'])
def delete_user_route():
    data = request.get_json()
    email = data.get('email')

    if email:
        if delete_user(email):
            return jsonify({"message": "User deleted successfully."})
        else:
            return jsonify({"message": "User not found."}), 404

    return jsonify({"message": "Invalid data provided."}), 400


# Dictionary to store reset OTPs and associated emails
reset_otps = {}
@app.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    email = data.get('email')

    # Check if the email is registered
    if email_exists(email):
        # Generate a secure OTP
        otp = generate_otp()

        # Store the OTP with an expiration time (e.g., 10 minutes)
        expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        reset_otps[otp] = {"email": email, "expiration_time": expiration_time}

        # Send an email with the OTP
        send_reset_otp_email(email, otp)

        return jsonify({"message": "Password reset OTP sent."})
    else:
        return jsonify({"message": "Email not found."}), 404

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    otp = data.get('otp')
    new_password = data.get('new_password')

    if otp and new_password and otp in reset_otps:
        reset_info = reset_otps[otp]

        # Check if the OTP is not expired
        if datetime.datetime.now() < reset_info['expiration_time']:
            # Reset the user's password
            email = reset_info['email']
            hashed_password = hash_password(new_password)

            # Update the password in the database
            update_password(email, hashed_password)

            # Remove the used OTP
            del reset_otps[otp]

            return jsonify({"message": "Password reset successful."})
        else:
            return jsonify({"message": "Password reset OTP has expired."}), 400
    else:
        return jsonify({"message": "Invalid or missing OTP or new password."}), 400
    



@app.route('/send_user_data', methods=['POST'])
def send_user_data():
    data = request.get_json()
    email = data.get('email')

    user_data = get_user_data(email)

    if user_data:
        name = user_data["name"]
        
        if user_data["verified"]:
            return jsonify({"message":name})
        else:
            return jsonify({"message":"User is not verified"}), 403
        
    else:
        return jsonify({"message":"User does not exist"}), 400
    



if __name__ == '__main__':
    app.run(debug=True)

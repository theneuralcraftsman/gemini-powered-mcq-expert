# server.py
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from db import (initialize_database, generate_otp, hash_password, email_exists, get_user_data, 
                insert_user, update_verification_status, login_user, update_password, delete_user,
                insert_otp, verify_otp_in_database, get_user_by_id, get_max_requests,
                insert_user_request, update_user_requests, get_user_requests)
import datetime
from admin_blueprint import admin_bp
import re

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


# Register the admin blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

def send_otp_email(email, otp):
    try:
        message = Message("OTP for Registration", recipients=[email])
        message.body = f"Your OTP for registration is: {otp} \n\nThis OTP has a validity of 2 mins."
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
    

def is_valid_email(email):
    # Regular expression for a more specific email format validation
    email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    # Check if the email matches the regex pattern
    return bool(re.match(email_regex, email))





@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')  # Include the name field
   
    if email and password and name:
        if email_exists(email):
            return jsonify({"message": "Email already registered."}), 400
        
        # Validate email format and other input
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        #users_db[email] = {"otp": generate_otp(), "verified": False, "otp_creation_time": datetime.datetime.now()}

        otp = generate_otp()
        insert_otp(email, otp)

        

        hashed_password = hash_password(password)

        # For simplicity, storing the hashed password in the database (not suitable for production)
        insert_user(email, hashed_password, name, 0)  # 0 indicates not verified
        log_user_login("User registered", email, request.remote_addr, request.user_agent.string, 0, 0)


        # Send OTP via email
        if send_otp_email(email, otp):
            return jsonify({"message": "Registration successful. Please check your email for OTP."})
        else:
            return jsonify({"message": "Failed to send OTP. Please try again later."}), 500

    return jsonify({"message": "Invalid data provided."}), 401

@app.route('/verify', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    user_otp = data.get('otp')

    if email and user_otp:
   
        if verify_otp_in_database:
            update_verification_status(email)
            log_user_login("Verified", email, request.remote_addr, request.user_agent.string, "null", "null")
            return jsonify({"message": "OTP verified successfully."})
        else:
            return jsonify({"message": "Invalid or expired OTP."}), 400
       

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

        # Validate email format and other input # Added new not tested
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        if user_data:
            if login_user(email, password):
                
                if user_data["verified"]:
                    return jsonify({"message": "Login successful.", "user_id":user_data["user_id"]})
                
                else:
                    # User is not verified, send OTP for verification
                    # User is not verified, send OTP for verification
                    new_otp = generate_otp()
                    insert_otp(email, new_otp)  # Store OTP in the database

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
                insert_otp(email, new_otp)

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

def clear_reset_otp():
    # Clean users_db when it has more than 2 entries
    if len(reset_otps) > 50:
        # Assuming you want to keep only the latest 2 entries
        sorted_entries = sorted(reset_otps.items(), key=lambda x: x[1]["otp_creation_time"], reverse=True)
        reset_otps.clear()
        reset_otps.update(dict(sorted_entries[:2]))



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
        clear_reset_otp()  # Clear reset otps
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
    user_id_rec = data.get('saved_u_id')
    ip_addr = data.get('ip_address') or "Not available"
    device_id = data.get('device_id') or "Not available"
    device_name = data.get('device_name') or "Not available"

    user_data = get_user_data(email)

    if user_data:
        name = user_data["name"]
        sub_status = user_data["subscription_level"]
        
        if user_id_rec==user_data["user_id"]:

            log_user_login("Auto Login",email, ip_addr, request.user_agent.string, device_id, device_name)
            return jsonify({"subscription_level":sub_status, "name":name})
        
        else:
            return jsonify({"message":"Can't match user credentials login again"}), 403
        
    else:
        return jsonify({"message":"User does not exist"}), 400
    

# 09-01-2024
def max_requests_allowed(user_id):

    # Step 1: Retrieve user data from user_info table
    user_data = get_user_by_id(user_id)
    if not user_data:
        return jsonify({'message': 'User not found.'}), 404
    # Step 2: Extract subscription level from user data
    subscription_level = user_data.get('subscription_level')
    if subscription_level is None:
        return jsonify({'message': 'Subscription level not found for the user.'}), 400
    # Step 3: Use subscription level to query subscription_tier table
    max_requests = get_max_requests(subscription_level)
    if not max_requests:
        return jsonify({'message': 'Subscription tier not found for the user.'}), 400
    return max_requests
   


# 09-01-2024
@app.route('/max_requests_for_users', methods=['POST'])
def get_user_requests_data():
    data = request.get_json()
    user_id = data.get('user_id')
    
    MAX_REQUESTS_ALLOWED = max_requests_allowed(user_id)
    
    try:
        # Check if the guest user exists
        user_data = get_user_requests(user_id)
        
        if user_data:
            requests_made = user_data["requests_made"]
            if requests_made < MAX_REQUESTS_ALLOWED:
                update_user_requests(user_id)
                
            else:
                # Max requests reached, return an appropriate response
                return jsonify({'message': 'Max limit reached for user. Try again later.'}), 429
        else:
            
            # Guest user does not exist, insert a new entry
            insert_user_request(user_id)
            print("abc")

        return jsonify({'message': 'User data processed successfully.'})

    except Exception as e:
        # Handle exceptions (e.g., database errors)
        return jsonify({'error': f'Error processing guest data: {str(e)}'}), 500



@app.route('/sign_out', methods=['POST'])
def sign_out_user():
    data = request.get_json()
    email = data.get('email')
    log_user_login("Signed Out",email, request.remote_addr, request.user_agent.string)
    return jsonify({"message":"Signed out"})
        

def log_user_login(status, email, ip_address, user_agent, device_id, device_name):
    # Log user login details to CSV file
    log_format = '{},{},{},{},{},{},{}\n'.format(status, datetime.datetime.now(), email, ip_address, user_agent, device_id, device_name)
    with open('user_login_log.csv', 'a') as log_file:
        log_file.write(log_format)

if __name__ == '__main__':
    app.run(debug=True)

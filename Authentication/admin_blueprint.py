# admin_routes.py
from flask import Blueprint, jsonify, request, send_file
from db import (get_user_data, delete_user, update_verification_status, get_non_verified_users,
                get_all_users, get_users_registered_on_date, delete_non_verified_users,
                get_users_in_time)
import datetime
import os

admin_bp = Blueprint("admin", __name__)


# Assuming your log file is named 'login_log.txt'
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'user_login_log.csv')

@admin_bp.route('/get_login_logs', methods=['GET'])
def get_login_logs():
    try:
        # Check if the log file exists
        if not os.path.exists(LOG_FILE_PATH):
            return jsonify({"message": "Log file not found."}), 404

        # Send the log file as a response
        return send_file(LOG_FILE_PATH, as_attachment=True)

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    


@admin_bp.route('/get_all_data', methods=['GET'])
def fetch_all_users_data():
    all_users_data = get_all_users()

    if all_users_data:
        return jsonify(all_users_data)
    else:
        return jsonify({"message": "No users found."}), 404

@admin_bp.route('/user', methods=['GET'])
def fetch_user_details():
    data = request.get_json()
    email = data.get('email')

    if email:
        user_data = get_user_data(email)
        if user_data:
            return jsonify(user_data)
        else:
            return jsonify({"message": f"User {email} not found."}), 404
    else:
        return jsonify({"message": "Invalid or missing email in the request."}), 400


@admin_bp.route('/user', methods=['DELETE'])
def delete_user_by_admin():
    data = request.get_json()
    email = data.get('email')

    if email:
        if delete_user(email):
            return jsonify({"message": f"User {email} deleted successfully."})
        else:
            return jsonify({"message": f"User {email} not found."}), 404
    else:
        return jsonify({"message": "Invalid or missing email in the request."}), 400


@admin_bp.route('/verify', methods=['POST'])
def verify_user_by_admin():
    data = request.get_json()
    user_email = data.get('email')  # Use a different variable name

    if user_email:
        # Mark user as verified by admin
        update_verification_status(user_email)
        return jsonify({"message": f"User {user_email} verified by admin."})
    else:
        return jsonify({"message": "Invalid or missing email in the request."}), 400
    



@admin_bp.route('/users_registered_on_date', methods=['GET'])
def get_users_registered_on_date_route():
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({"message": "Date parameter is missing in the request."}), 400

    try:
        # Convert date string to datetime object
        registration_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    users_on_date = get_users_registered_on_date(registration_date)

    if users_on_date:
        return jsonify(users_on_date)
    else:
        return jsonify({"message": f"No users found registered on {date_str}."}), 404
    




@admin_bp.route('/delete_non_verified_users', methods=['DELETE'])
def delete_non_verified_users_route():
    # Call the function to delete non-verified users
    delete_non_verified_users()

    return jsonify({"message": "Non-verified users deleted successfully."})


@admin_bp.route('/get_non_verified_users', methods=['GET'])
def get_non_verified_users_route():
    # Call the function to get non-verified users
    non_verified_users = get_non_verified_users()

    if non_verified_users:
        return jsonify(non_verified_users)
    else:
        return jsonify({"message": "No non-verified users found."}), 404
    

@admin_bp.route('/delete_previous_logs', methods=['DELETE'])
def delete_previous_logs():
    try:
        # Check if the log file exists
        if os.path.exists(LOG_FILE_PATH):
            # Delete the previous log file
            os.remove(LOG_FILE_PATH)
            return jsonify({"message": "Previous log file deleted successfully."})
        else:
            return jsonify({"message": "Previous log file not found."}), 404

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    

# NEW - 06/01/24
@admin_bp.route('/users_in_time_duration', methods=['GET'])
def get_users_in_time_duration():
    try:
        duration = request.args.get('duration')

        if duration:
            start_date, end_date = parse_duration(duration)

            # Fetch users registered in the specified duration
            users_in_duration = get_users_in_time(start_date, end_date)

            return jsonify(users_in_duration)
        else:
            return jsonify({"message": "Invalid or missing duration parameter in the request."}), 400

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

# Function to parse the duration parameter
def parse_duration(duration):
    end_date = datetime.datetime.now()
    if duration == "Last 30 Days":
        start_date = end_date - datetime.timedelta(days=30)
    elif duration == "Last 6 Months":
        start_date = end_date - datetime.timedelta(days=6 * 30)
    elif duration == "Last Year":
        start_date = end_date - datetime.timedelta(days=365)
    else:
        start_date = datetime.datetime(1900, 1, 1)  # Default: All Time

    return start_date, end_date



# database.py
import sqlite3
from passlib.hash import sha256_crypt
import os
import pyotp
import datetime
import uuid
from apscheduler.schedulers.background import BackgroundScheduler

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Specify the database file path
DB_FILE = os.path.join(script_dir, 'data', 'user_info.db')

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
                    s_no INTEGER PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    verified INTEGER NOT NULL,
                    registration_time TEXT NOT NULL,
                    subscription_level INTEGER DEFAULT 0
                )

    ''')

    # Added 08-01-2024
    # Create the subscription_tier table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_tier (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            max_requests_allowed INTEGER NOT NULL
        )
    ''')

    # 09-01-2024
    # Insert data for different subscription levels if the table is empty
    cursor.execute('SELECT COUNT(*) FROM subscription_tier')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'INSERT INTO subscription_tier (id, name, max_requests_allowed) VALUES (?, ?, ?)',
            [
                (0, 'Free Tier', 5),
                (1, 'Tier 1', 20),
                (2, 'Tier 2', -1),  # Assuming -1 represents unlimited requests
            ]
        )


        # Create the user_requests table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_requests (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                requests_made INTEGER DEFAULT 0,
                last_request_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')


    conn.commit()
    conn.close()

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32())
    return totp.now()

# 09-01-2024
def get_subscription_tier_by_level(subscription_level):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch subscription tier data based on the subscription level
    cursor.execute('SELECT * FROM subscription_tier WHERE id = ?', (subscription_level,))
    tier_data = cursor.fetchone()

    conn.close()

    # Convert the result to a dictionary for easier use
    if tier_data:
        return {"id": tier_data[0], "name": tier_data[1], "max_requests_allowed": tier_data[2]}
    else:
        return None

# Assuming this function is part of the server.py file
def insert_otp(email, otp):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get the current date and time
    creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    

    cursor.execute('INSERT OR REPLACE INTO otps (email, otp, creation_time) VALUES (?, ?, ?)',
                   (email, otp, creation_time))

    conn.commit()
    conn.close()


def verify_otp_in_database(email, user_otp):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch the latest OTP for the given email
    cursor.execute('SELECT otp, creation_time FROM otps WHERE email = ? ORDER BY creation_time DESC LIMIT 1', (email,))
    result = cursor.fetchone()

    conn.close()

    if result:
        stored_otp, creation_time = result
        # Check if the OTP is not expired (2 minutes expiration time)
        if datetime.datetime.now() < datetime.datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=2):
            return stored_otp == user_otp

    return False


def delete_expired_otps():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Calculate the timestamp 24 hours ago
    expiration_time_threshold = datetime.datetime.now() - datetime.timedelta(hours=12)

    # Delete expired OTPs
    cursor.execute('DELETE FROM otps WHERE creation_time < ?', (expiration_time_threshold.strftime("%Y-%m-%d %H:%M:%S"),))

    conn.commit()
    conn.close()

# Schedule the task to run every 24 hours
scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_otps, 'interval', hours=12)
scheduler.start()


def hash_password(password):
    return sha256_crypt.hash(password)

def email_exists(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
    count = cursor.fetchone()[0]

    conn.close()

    return count > 0

def insert_user(email, password, name, verified):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Generate a unique user_id using UUID
    user_id = str(uuid.uuid4())

    # Get the current date and time
    registration_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('INSERT INTO users (user_id, email, password, name, verified, registration_time) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, email, password, name, verified, registration_time))

    conn.commit()
    conn.close()



def login_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT password, verified FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()

    conn.close()

    if result:
        stored_password, verified = result
        if sha256_crypt.verify(password, stored_password):
            return True
    return False


def update_verification_status(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET verified = 1 WHERE email = ?', (email,))

    conn.commit()
    conn.close()


def update_password(email, hashed_password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))

    conn.commit()
    conn.close()

def get_user_data(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch user data based on email
    cursor.execute('SELECT s_no, user_id, email, password, name, verified, registration_time, subscription_level FROM users WHERE email = ?', (email,))
    user_data = cursor.fetchone()

    conn.close()

    # Convert the result to a dictionary for easier use
    if user_data:
        return {"s_no": user_data[0],
                "user_id": user_data[1],
                "email": user_data[2], 
                "password": user_data[3], 
                "name": user_data[4], 
                "verified": bool(user_data[5]), 
                "registration_time": user_data[6],
                "subscription_level": user_data[7]
                }
    else:
        return None

# 09-01-2024
def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch user data based on user_id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    conn.close()

    # Convert the result to a dictionary for easier use
    if user_data:
        return {
            "s_no": user_data[0],
            "user_id": user_data[1],
            "email": user_data[2], 
            "password": user_data[3], 
            "name": user_data[4], 
            "verified": bool(user_data[5]), 
            "registration_time": user_data[6],
            "subscription_level": user_data[7]
        }
    else:
        return None

# 09-01-2024
def get_max_requests(subscription_level):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch max_requests_allowed based on subscription_level
    cursor.execute('SELECT max_requests_allowed FROM subscription_tier WHERE id = ?', (subscription_level,))
    tier_data = cursor.fetchone()

    conn.close()

    # Return the tier or None if not found
    return tier_data[0] if tier_data else None

# 09-01-2024
def insert_user_request(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Insert a new entry for the user
    cursor.execute('INSERT INTO user_requests (user_id, requests_made, last_request_time) VALUES (?, 1, ?)',
                   (user_id, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

# 09-01-2024
def update_user_requests(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Update requests_made if it's less than MAX_REQUESTS_ALLOWED
    cursor.execute('UPDATE user_requests SET requests_made = requests_made + 1 WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

# 09-01-2024
def get_user_requests(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch user_requests data based on user_id
    cursor.execute('SELECT * FROM user_requests WHERE user_id = ?', (user_id,))
    user_requests_data = cursor.fetchone()

    conn.close()

    # Convert the result to a dictionary for easier use
    if user_requests_data:
        return {
            "id": user_requests_data[0],
            "user_id": user_requests_data[1],
            "requests_made": user_requests_data[2],
            "last_request_time": user_requests_data[3]
        }
    else:
        return None


# 09-01-2024
def delete_old_user_requests():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Calculate the timestamp 24 hours ago
    expiration_time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

    # Delete old user_requests entries
    cursor.execute('DELETE FROM user_requests WHERE last_request_time < ?',
                   (expiration_time_threshold.strftime("%Y-%m-%d %H:%M:%S"),))

    conn.commit()
    conn.close()

# Schedule the task to run every 24 hours
scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_user_requests, 'interval', hours=1)
scheduler.start()

def delete_user(email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE email = ?', (email,))
    rows_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return rows_deleted > 0

def get_non_verified_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch non-verified users from the table along with registration date
    cursor.execute('SELECT s_no, user_id, email, password, name, verified, registration_time FROM users WHERE verified = 0')
    non_verified_users = cursor.fetchall()

    conn.close()

    # Convert the result to a list of dictionaries for easier use
    user_list = [
        {
            "s_no":user[0],
            "user_id":user[1],
            "email": user[2],
            "password": user[3],
            "name": user[4],
            "verified": bool(user[5]),
            "registration_time": user[6]
        }
        for user in non_verified_users
    ]

    return user_list

# database.py
def delete_non_verified_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE verified = 0')

    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch all users from the table
    cursor.execute('SELECT s_no, user_id, email, name, verified, registration_time, subscription_level FROM users')
    all_users = cursor.fetchall()

    conn.close()

    # Convert the result to a list of dictionaries for easier use
    user_list = [{"s_no":user[0],
                  "user_id":user[1],
                  "email": user[2], 
                  "name": user[3], 
                  "verified": bool(user[4]), 
                  "registration_time":user[5],
                  "subscription_level":user[6]} for user in all_users]

    return user_list


def get_users_registered_on_date(registration_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch users registered on a particular date
    cursor.execute('SELECT s_no, user_id, email, name, verified, subscription_level FROM users WHERE DATE(registration_time) = ?', (registration_date,))
    users_on_date = cursor.fetchall()

    conn.close()

    # Convert the result to a list of dictionaries for easier use
    user_list = [{
        "s_no":user[0],
        "user_id":user[1],
        "email": user[2], 
        "name": user[3], 
        "verified": bool(user[4]), 
        "subscription_level": user[5]} for user in users_on_date]

    return user_list

# NEW - 06/01/24
def get_users_in_time(start_date, end_date):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch users registered in the specified duration
    cursor.execute('SELECT email, password, name, verified, registration_time, subscription_level FROM users WHERE registration_time BETWEEN ? AND ?', (start_date, end_date))
    users_in_duration = cursor.fetchall()

    conn.close()

    # Convert the result to a list of dictionaries for easier use
    user_list = [
        {
            "email": user[0],
            "password": user[1],
            "name": user[2],
            "verified": bool(user[3]),
            "registration_time": user[4],
            "subscription_level": user[5]
        }
        for user in users_in_duration
    ]

    return user_list


if __name__ == '__main__':
    initialize_database()

# database.py
import sqlite3
from passlib.hash import sha256_crypt
import os
import pyotp
import datetime
import uuid

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

    conn.commit()
    conn.close()

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32())
    return totp.now()

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
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
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
    cursor.execute('SELECT * FROM users WHERE registration_time BETWEEN ? AND ?', (start_date, end_date))
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

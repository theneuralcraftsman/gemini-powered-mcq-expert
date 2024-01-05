# database.py
import sqlite3
from passlib.hash import sha256_crypt
import os
import pyotp

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
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            verified INTEGER NOT NULL
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

    cursor.execute('INSERT INTO users (email, password, name, verified) VALUES (?, ?, ?, ?)', (email, password, name, verified))

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
    cursor.execute('SELECT email, password, name, verified FROM users WHERE email = ?', (email,))
    user_data = cursor.fetchone()

    conn.close()

    # Convert the result to a dictionary for easier use
    if user_data:
        return {"email": user_data[0], "password": user_data[1], "name": user_data[2], "verified": bool(user_data[3])}
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

# database.py
def delete_non_verified_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE verified = 0')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()

import sqlite3
import hashlib


conn = sqlite3.connect('/Users/sahithikaruparthi/Desktop/recruit/backend/db/resume_screening.db')
cursor = conn.cursor()

username = 'admin'
email = 'admin@techrecruit.example.com'
password = 'securepassword123'
password_hash = hashlib.sha256(password.encode()).hexdigest()
role = 'admin'

try:
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    ''', (username, email, password_hash, role))
    conn.commit()
    print("✅ Admin inserted successfully.")
except sqlite3.IntegrityError as e:
    print("⚠️ Admin already exists or other DB error:", e)
finally:
    conn.close()

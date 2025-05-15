import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER

# Ensure the base upload folder exists
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

# Initialize the database
conn = sqlite3.connect('users.db')
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
)
""")
conn.commit()
conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = sqlite3.connect('users.db')
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            os.makedirs(os.path.join(BASE_UPLOAD_FOLDER, username), exist_ok=True)
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        cursor = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            user_dir = os.path.join(BASE_UPLOAD_FOLDER, username)
            os.makedirs(user_dir, exist_ok=True)
            return redirect('/')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect('/login')
    file = request.files['file']
    if file:
        user_dir = os.path.join(BASE_UPLOAD_FOLDER, session['username'])
        file.save(os.path.join(user_dir, file.filename))
    return redirect('/')

@app.route('/view-files')
def view_files():
    if 'username' not in session:
        return redirect('/login')
    user_dir = os.path.join(BASE_UPLOAD_FOLDER, session['username'])
    files = os.listdir(user_dir)
    return render_template('view_files.html', files=files)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'username' not in session:
        return redirect('/login')
    user_dir = os.path.join(BASE_UPLOAD_FOLDER, session['username'])
    file_path = os.path.join(user_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(user_dir, filename)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)

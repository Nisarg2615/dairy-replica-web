
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simple in-memory user database (would use a real database in production)
users = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        farm_name = request.form.get('farm_name')
        
        # Simple validation
        if not all([username, email, password, farm_name]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if email in users:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Store user (would hash password in real app)
        users[email] = {
            'username': username,
            'password': generate_password_hash(password),
            'farm_name': farm_name
        }
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = users.get(email)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = users.get(session['user'])
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

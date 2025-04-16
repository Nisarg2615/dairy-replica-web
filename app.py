
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('dairy_dash.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password TEXT,
        farm_name TEXT,
        role TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

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
        
        if not all([username, email, password, farm_name]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            conn.close()
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        conn.execute('INSERT INTO users (username, email, password, farm_name, role) VALUES (?, ?, ?, ?, ?)',
                  (username, email, generate_password_hash(password), farm_name, 'admin'))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if not all([name, phone, password]):
            flash('All fields are required', 'error')
            return render_template('register_customer.html')
        
        conn = get_db_connection()
        existing_customer = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        
        if existing_customer:
            conn.close()
            flash('Phone number already registered', 'error')
            return render_template('register_customer.html')
        
        conn.execute('INSERT INTO users (username, phone, password, role) VALUES (?, ?, ?, ?)',
                  (name, phone, generate_password_hash(password), 'customer'))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login_customer'))
    
    return render_template('register_customer.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            session['role'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/login_customer', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        conn = get_db_connection()
        customer = conn.execute('SELECT * FROM users WHERE phone = ? AND role = ?', 
                             (phone, 'customer')).fetchone()
        conn.close()
        
        if customer and check_password_hash(customer['password'], password):
            session['user'] = phone
            session['role'] = 'customer'
            flash('Login successful!', 'success')
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login_customer.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['user'],)).fetchone()
    conn.close()
    
    return render_template('dashboard.html', user=user)

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM users WHERE phone = ?', (session['user'],)).fetchone()
    conn.close()
    
    return render_template('customer_dashboard.html', customer=customer)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

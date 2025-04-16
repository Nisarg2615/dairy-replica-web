
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
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    ''')
    
    # Add milkmen table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS milkmen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        password TEXT
    )
    ''')
    
    # Add customers table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        address TEXT,
        milkman_id INTEGER,
        password TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
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
        
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                      (username, email, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered', 'error')
            return render_template('register.html')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'admin'  # Set role for admin users
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register_milkman', methods=['GET', 'POST'])
def register_milkman():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if not all([name, phone, password]):
            flash('All fields are required', 'error')
            return render_template('register_milkman.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register_milkman.html')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO milkmen (name, phone, password) VALUES (?, ?, ?)',
                      (name, phone, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login_milkman'))
        except sqlite3.IntegrityError:
            flash('Phone number already registered', 'error')
            return render_template('register_milkman.html')
        finally:
            conn.close()
    
    return render_template('register_milkman.html')

@app.route('/login_milkman', methods=['GET', 'POST'])
def login_milkman():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        conn = get_db_connection()
        milkman = conn.execute('SELECT * FROM milkmen WHERE phone = ?', (phone,)).fetchone()
        conn.close()
        
        if milkman and check_password_hash(milkman['password'], password):
            session['user_id'] = milkman['id']
            session['username'] = milkman['name']
            session['role'] = 'milkman'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # You might want to create a milkman_dashboard route
        else:
            flash('Invalid phone or password', 'error')
    
    return render_template('login_milkman.html')

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        milkman_id = request.form.get('milkman_id')
        password = request.form.get('password')
        
        if not all([name, phone, address, milkman_id, password]):
            flash('All fields are required', 'error')
            return render_template('register_customer.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register_customer.html')
        
        conn = get_db_connection()
        try:
            # Check if milkman_id exists
            milkman = conn.execute('SELECT id FROM milkmen WHERE id = ?', (milkman_id,)).fetchone()
            if not milkman:
                flash('Invalid Milkman ID', 'error')
                return render_template('register_customer.html')
                
            conn.execute('INSERT INTO customers (name, phone, address, milkman_id, password) VALUES (?, ?, ?, ?, ?)',
                      (name, phone, address, milkman_id, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login_customer'))
        except sqlite3.IntegrityError:
            flash('Phone number already registered', 'error')
            return render_template('register_customer.html')
        finally:
            conn.close()
    
    return render_template('register_customer.html')

@app.route('/login_customer', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        conn = get_db_connection()
        customer = conn.execute('SELECT * FROM customers WHERE phone = ?', (phone,)).fetchone()
        conn.close()
        
        if customer and check_password_hash(customer['password'], password):
            session['user_id'] = customer['id']
            session['username'] = customer['name']
            session['role'] = 'customer'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # You might want to create a customer_dashboard route
        else:
            flash('Invalid phone or password', 'error')
    
    return render_template('login_customer.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role', 'user')
    
    if role == 'milkman':
        return redirect(url_for('milkman_dashboard'))
    elif role == 'customer':
        return redirect(url_for('customer_dashboard'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/milkman_dashboard')
def milkman_dashboard():
    if 'user_id' not in session or session.get('role') != 'milkman':
        return redirect(url_for('login_milkman'))
    
    # Here you would fetch data needed for the milkman dashboard
    # For now, using a generic dashboard template
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    # Here you would fetch data needed for the customer dashboard
    # For now, using a generic dashboard template
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

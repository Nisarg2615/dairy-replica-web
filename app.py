
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Available milk brands
milk_brands = ["Premium", "Regular", "Toned", "Double-Toned", "Organic"]

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
        address TEXT,
        milkman_id TEXT,
        role TEXT,
        preferences TEXT DEFAULT '{"brand":"Premium","quantity":1}'
    )
    ''')
    
    # Create milkmen table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS milkmen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        password TEXT,
        milkman_id TEXT UNIQUE
    )
    ''')
    
    # Create orders table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_phone TEXT,
        delivery_date TEXT,
        brand TEXT,
        quantity REAL,
        notes TEXT,
        UNIQUE(customer_phone, delivery_date)
    )
    ''')
    
    # Create deliveries table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_phone TEXT,
        delivery_date TEXT,
        status TEXT,
        UNIQUE(customer_phone, delivery_date)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def generate_milkman_id():
    while True:
        milkman_id = str(random.randint(100000, 999999))
        conn = get_db_connection()
        existing = conn.execute('SELECT milkman_id FROM milkmen WHERE milkman_id = ?', 
                             (milkman_id,)).fetchone()
        conn.close()
        if existing is None:
            return milkman_id

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
        
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            conn.close()
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Store user
        conn.execute('INSERT INTO users (username, email, password, farm_name, role) VALUES (?, ?, ?, ?, ?)',
                  (username, email, generate_password_hash(password), farm_name, 'admin'))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/register_milkman', methods=['GET', 'POST'])
def register_milkman():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Simple validation
        if not all([name, phone, password]):
            flash('All fields are required', 'error')
            return render_template('register_milkman.html')
        
        conn = get_db_connection()
        existing_milkman = conn.execute('SELECT * FROM milkmen WHERE phone = ?', (phone,)).fetchone()
        
        if existing_milkman:
            conn.close()
            flash('Phone number already registered', 'error')
            return render_template('register_milkman.html')
        
        # Generate unique milkman ID
        milkman_id = generate_milkman_id()
        
        # Store milkman
        conn.execute('INSERT INTO milkmen (name, phone, password, milkman_id) VALUES (?, ?, ?, ?)',
                  (name, phone, generate_password_hash(password), milkman_id))
        conn.commit()
        conn.close()
        
        session['user'] = phone
        session['role'] = 'milkman'
        flash('Registration successful!', 'success')
        return redirect(url_for('milkman_dashboard'))
    
    return render_template('register_milkman.html')

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')
        milkman_id = request.form.get('milkman_id')
        
        # Simple validation
        if not all([name, phone, address, password, milkman_id]):
            flash('All fields are required', 'error')
            return render_template('register_customer.html')
        
        conn = get_db_connection()
        existing_customer = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        
        if existing_customer:
            conn.close()
            flash('Phone number already registered', 'error')
            return render_template('register_customer.html')
        
        # Validate milkman ID
        milkman = conn.execute('SELECT * FROM milkmen WHERE milkman_id = ?', (milkman_id,)).fetchone()
        
        if not milkman:
            conn.close()
            flash('Invalid Milkman ID', 'error')
            return render_template('register_customer.html')
        
        # Store customer with default preferences
        import json
        default_preferences = json.dumps({"brand": milk_brands[0], "quantity": 1})
        
        conn.execute('''
            INSERT INTO users (username, phone, password, address, milkman_id, role, preferences) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, generate_password_hash(password), address, milkman_id, 'customer', default_preferences))
        
        conn.commit()
        conn.close()
        
        session['user'] = phone
        session['role'] = 'customer'
        flash('Registration successful!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('register_customer.html', milk_brands=milk_brands)

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
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/login_milkman', methods=['GET', 'POST'])
def login_milkman():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        conn = get_db_connection()
        milkman = conn.execute('SELECT * FROM milkmen WHERE phone = ?', (phone,)).fetchone()
        conn.close()
        
        if milkman and check_password_hash(milkman['password'], password):
            session['user'] = phone
            session['role'] = 'milkman'
            flash('Login successful!', 'success')
            return redirect(url_for('milkman_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login_milkman.html')

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
    
    role = session.get('role', 'admin')
    
    if role == 'milkman':
        return redirect(url_for('milkman_dashboard'))
    elif role == 'customer':
        return redirect(url_for('customer_dashboard'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['user'],)).fetchone()
    conn.close()
    
    return render_template('dashboard.html', user=user)

@app.route('/milkman_dashboard')
def milkman_dashboard():
    if 'user' not in session or session.get('role') != 'milkman':
        return redirect(url_for('login_milkman'))
    
    conn = get_db_connection()
    milkman = conn.execute('SELECT * FROM milkmen WHERE phone = ?', (session['user'],)).fetchone()
    
    # Get next day's date
    next_day = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get all orders for next day from all linked customers
    next_day_orders = []
    
    # Get all customers linked to this milkman
    customers = conn.execute('''
        SELECT * FROM users 
        WHERE milkman_id = ? AND role = 'customer'
    ''', (milkman['milkman_id'],)).fetchall()
    
    for customer in customers:
        import json
        preferences = json.loads(customer['preferences'])
        
        # Check if there's a specific order for the next day
        order = conn.execute('''
            SELECT * FROM orders 
            WHERE customer_phone = ? AND delivery_date = ?
        ''', (customer['phone'], next_day)).fetchone()
        
        if order:
            next_day_orders.append({
                'customer_name': customer['username'],
                'address': customer['address'],
                'brand': order['brand'],
                'quantity': order['quantity'],
                'notes': order['notes']
            })
        else:
            # Use default preferences if no specific order
            next_day_orders.append({
                'customer_name': customer['username'],
                'address': customer['address'],
                'brand': preferences['brand'],
                'quantity': preferences['quantity'],
                'notes': ''
            })
    
    conn.close()
    
    return render_template('milkman_dashboard.html', milkman=milkman, orders=next_day_orders)

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM users WHERE phone = ?', (session['user'],)).fetchone()
    
    # Find milkman name
    milkman = conn.execute('SELECT * FROM milkmen WHERE milkman_id = ?', 
                        (customer['milkman_id'],)).fetchone()
    
    milkman_name = milkman['name'] if milkman else "Unknown"
    conn.close()
    
    return render_template('customer_dashboard.html', customer=customer, milkman_name=milkman_name)

@app.route('/milk_preference', methods=['GET', 'POST'])
def milk_preference():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM users WHERE phone = ?', (customer_phone,)).fetchone()
    
    import json
    preferences = json.loads(customer['preferences'])
    
    if request.method == 'POST':
        brand = request.form.get('brand')
        quantity = float(request.form.get('quantity'))
        date = request.form.get('date')
        notes = request.form.get('notes', '')
        
        # Update default preferences if selected
        if request.form.get('update_default') == 'on':
            new_preferences = json.dumps({"brand": brand, "quantity": quantity})
            conn.execute('UPDATE users SET preferences = ? WHERE phone = ?', 
                      (new_preferences, customer_phone))
        
        # Save specific order for the date
        try:
            conn.execute('''
                INSERT INTO orders (customer_phone, delivery_date, brand, quantity, notes) 
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_phone, date, brand, quantity, notes))
        except sqlite3.IntegrityError:
            # Update existing order for this date
            conn.execute('''
                UPDATE orders 
                SET brand = ?, quantity = ?, notes = ? 
                WHERE customer_phone = ? AND delivery_date = ?
            ''', (brand, quantity, notes, customer_phone, date))
        
        conn.commit()
        flash('Milk preference updated successfully!', 'success')
        return redirect(url_for('milk_preference'))
    
    # Get all orders for this customer
    customer_orders = {}
    orders = conn.execute('SELECT * FROM orders WHERE customer_phone = ? ORDER BY delivery_date', 
                       (customer_phone,)).fetchall()
    
    for order in orders:
        customer_orders[order['delivery_date']] = {
            'brand': order['brand'],
            'quantity': order['quantity'],
            'notes': order['notes']
        }
    
    conn.close()
    
    # Update the customer object with parsed preferences for template
    customer = dict(customer)
    customer['preferences'] = preferences
    
    return render_template('milk_preference.html', 
                          customer=customer, 
                          milk_brands=milk_brands, 
                          orders=customer_orders)

@app.route('/calendar_view')
def calendar_view():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM users WHERE phone = ?', (customer_phone,)).fetchone()
    
    import json
    preferences = json.loads(customer['preferences'])
    customer = dict(customer)
    customer['preferences'] = preferences
    
    # Get the current month and year
    today = datetime.now()
    month = today.month
    year = today.year
    
    # Get the first day of the month and the number of days in the month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    num_days = last_day.day
    
    # Get all delivery data for this customer for the current month
    deliveries_data = conn.execute('''
        SELECT * FROM deliveries 
        WHERE customer_phone = ? AND delivery_date LIKE ?
    ''', (customer_phone, f"{year}-{month:02d}-%")).fetchall()
    
    orders_data = conn.execute('''
        SELECT * FROM orders 
        WHERE customer_phone = ? AND delivery_date LIKE ?
    ''', (customer_phone, f"{year}-{month:02d}-%")).fetchall()
    
    # Create dictionaries for easier lookup
    customer_deliveries = {row['delivery_date']: row for row in deliveries_data}
    customer_orders = {row['delivery_date']: {
        'brand': row['brand'],
        'quantity': row['quantity'],
        'notes': row['notes']
    } for row in orders_data}
    
    conn.close()
    
    # Create calendar data
    calendar_data = []
    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        
        status = "not_ordered"
        if date_str in customer_deliveries:
            status = "delivered"
        elif date_str in customer_orders:
            if datetime.now() > datetime.strptime(date_str, '%Y-%m-%d'):
                status = "delivered"  # For demo purposes, assume delivered if in the past
            else:
                status = "ordered"
        
        calendar_data.append({
            'day': day,
            'status': status,
            'order': customer_orders.get(date_str)
        })
    
    return render_template('calendar_view.html', 
                          customer=customer, 
                          calendar_data=calendar_data,
                          month=month,
                          year=year,
                          month_name=first_day.strftime('%B'))

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM users WHERE phone = ?', (customer_phone,)).fetchone()
    
    if request.method == 'POST':
        address = request.form.get('address')
        milkman_id = request.form.get('milkman_id')
        
        # Validate milkman ID
        milkman = conn.execute('SELECT * FROM milkmen WHERE milkman_id = ?', (milkman_id,)).fetchone()
        
        if not milkman:
            conn.close()
            flash('Invalid Milkman ID', 'error')
            return redirect(url_for('update_profile'))
        
        # Update customer profile
        conn.execute('UPDATE users SET address = ?, milkman_id = ? WHERE phone = ?', 
                  (address, milkman_id, customer_phone))
        conn.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    conn.close()
    
    return render_template('update_profile.html', customer=customer)

@app.route('/cancel_order/<date>')
def cancel_order(date):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    
    # Check if the order is for a future date
    order_date = datetime.strptime(date, '%Y-%m-%d')
    cutoff_date = datetime.now().replace(hour=23, minute=59, second=59)
    if order_date < cutoff_date:
        flash('Cannot cancel orders for today or past dates', 'error')
        return redirect(url_for('milk_preference'))
    
    # Remove the order
    conn = get_db_connection()
    result = conn.execute('DELETE FROM orders WHERE customer_phone = ? AND delivery_date = ?', 
                      (customer_phone, date))
    conn.commit()
    conn.close()
    
    if result.rowcount > 0:
        flash('Order cancelled successfully!', 'success')
    else:
        flash('Order not found', 'error')
    
    return redirect(url_for('milk_preference'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

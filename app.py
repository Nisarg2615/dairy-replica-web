
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simple in-memory databases (would use a real database in production)
users = {}
milkmen = {}
milk_brands = ["Premium", "Regular", "Toned", "Double-Toned", "Organic"]
orders = {}
deliveries = {}

def generate_milkman_id():
    while True:
        milkman_id = str(random.randint(100000, 999999))
        if milkman_id not in milkmen:
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
        
        if email in users:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Store user
        users[email] = {
            'username': username,
            'password': generate_password_hash(password),
            'farm_name': farm_name,
            'role': 'admin'
        }
        
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
        
        if phone in milkmen:
            flash('Phone number already registered', 'error')
            return render_template('register_milkman.html')
        
        # Generate unique milkman ID
        milkman_id = generate_milkman_id()
        
        # Store milkman
        milkmen[phone] = {
            'name': name,
            'password': generate_password_hash(password),
            'milkman_id': milkman_id,
            'customers': [],
            'role': 'milkman'
        }
        
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
        
        if phone in users:
            flash('Phone number already registered', 'error')
            return render_template('register_customer.html')
        
        # Validate milkman ID
        milkman_found = False
        milkman_phone = None
        for phone_key, milkman in milkmen.items():
            if milkman['milkman_id'] == milkman_id:
                milkman_found = True
                milkman_phone = phone_key
                break
        
        if not milkman_found:
            flash('Invalid Milkman ID', 'error')
            return render_template('register_customer.html')
        
        # Store customer
        users[phone] = {
            'name': name,
            'password': generate_password_hash(password),
            'address': address,
            'milkman_id': milkman_id,
            'role': 'customer',
            'preferences': {
                'brand': milk_brands[0],
                'quantity': 1,
            }
        }
        
        # Add customer to milkman's customer list
        milkmen[milkman_phone]['customers'].append(phone)
        
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
        
        user = users.get(email)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            session['role'] = user.get('role', 'admin')
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
        
        milkman = milkmen.get(phone)
        
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
        
        customer = users.get(phone)
        
        if customer and customer.get('role') == 'customer' and check_password_hash(customer['password'], password):
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
    
    user = users.get(session['user'])
    role = session.get('role', 'admin')
    
    if role == 'milkman':
        return redirect(url_for('milkman_dashboard'))
    elif role == 'customer':
        return redirect(url_for('customer_dashboard'))
    
    return render_template('dashboard.html', user=user)

@app.route('/milkman_dashboard')
def milkman_dashboard():
    if 'user' not in session or session.get('role') != 'milkman':
        return redirect(url_for('login_milkman'))
    
    milkman = milkmen.get(session['user'])
    
    # Get next day's date
    next_day = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get all orders for next day from all linked customers
    next_day_orders = []
    for customer_phone in milkman['customers']:
        customer = users.get(customer_phone)
        if customer:
            # Check if there's a specific order for the next day
            customer_orders = orders.get(customer_phone, {})
            order = customer_orders.get(next_day)
            
            if order:
                next_day_orders.append({
                    'customer_name': customer['name'],
                    'address': customer['address'],
                    'brand': order['brand'],
                    'quantity': order['quantity'],
                    'notes': order.get('notes', '')
                })
            else:
                # Use default preferences if no specific order
                next_day_orders.append({
                    'customer_name': customer['name'],
                    'address': customer['address'],
                    'brand': customer['preferences']['brand'],
                    'quantity': customer['preferences']['quantity'],
                    'notes': ''
                })
    
    return render_template('milkman_dashboard.html', milkman=milkman, orders=next_day_orders)

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer = users.get(session['user'])
    
    # Find milkman name
    milkman_name = "Unknown"
    for phone, milkman in milkmen.items():
        if milkman['milkman_id'] == customer['milkman_id']:
            milkman_name = milkman['name']
            break
    
    return render_template('customer_dashboard.html', customer=customer, milkman_name=milkman_name)

@app.route('/milk_preference', methods=['GET', 'POST'])
def milk_preference():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    customer = users.get(customer_phone)
    
    if request.method == 'POST':
        brand = request.form.get('brand')
        quantity = float(request.form.get('quantity'))
        date = request.form.get('date')
        notes = request.form.get('notes', '')
        
        # Update default preferences if selected
        if request.form.get('update_default') == 'on':
            customer['preferences']['brand'] = brand
            customer['preferences']['quantity'] = quantity
        
        # Save specific order for the date
        if not date in orders:
            orders[customer_phone] = {}
        
        orders[customer_phone][date] = {
            'brand': brand,
            'quantity': quantity,
            'notes': notes
        }
        
        flash('Milk preference updated successfully!', 'success')
        return redirect(url_for('milk_preference'))
    
    # Get all orders for this customer
    customer_orders = orders.get(customer_phone, {})
    
    return render_template('milk_preference.html', 
                          customer=customer, 
                          milk_brands=milk_brands, 
                          orders=customer_orders)

@app.route('/calendar_view')
def calendar_view():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    customer = users.get(customer_phone)
    
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
    customer_deliveries = deliveries.get(customer_phone, {})
    customer_orders = orders.get(customer_phone, {})
    
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
    customer = users.get(customer_phone)
    
    if request.method == 'POST':
        address = request.form.get('address')
        milkman_id = request.form.get('milkman_id')
        
        # Validate milkman ID
        milkman_found = False
        new_milkman_phone = None
        for phone, milkman in milkmen.items():
            if milkman['milkman_id'] == milkman_id:
                milkman_found = True
                new_milkman_phone = phone
                break
        
        if not milkman_found:
            flash('Invalid Milkman ID', 'error')
            return redirect(url_for('update_profile'))
        
        # Remove customer from old milkman's list
        for phone, milkman in milkmen.items():
            if customer_phone in milkman['customers']:
                milkman['customers'].remove(customer_phone)
        
        # Add customer to new milkman's list
        milkmen[new_milkman_phone]['customers'].append(customer_phone)
        
        # Update customer profile
        customer['address'] = address
        customer['milkman_id'] = milkman_id
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('update_profile.html', customer=customer)

@app.route('/cancel_order/<date>')
def cancel_order(date):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('login_customer'))
    
    customer_phone = session['user']
    customer_orders = orders.get(customer_phone, {})
    
    # Check if the order is for a future date
    order_date = datetime.strptime(date, '%Y-%m-%d')
    cutoff_date = datetime.now().replace(hour=23, minute=59, second=59)
    if order_date < cutoff_date:
        flash('Cannot cancel orders for today or past dates', 'error')
        return redirect(url_for('milk_preference'))
    
    # Remove the order
    if date in customer_orders:
        del customer_orders[date]
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

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mysql.connector
import random
import json
import datetime
from flask import abort
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- API: Staff assigned orders ---
# ...existing code...

# --- API: Accept order ---
@app.route('/admin/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'accepted' WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "message": "Order accepted."})
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Raghul#2006&',   # change if needed
        database='soft'            # change if needed
    )

# --- API: Staff assigned orders ---
@app.route('/api/staff_orders/<staff_id>')
def api_staff_orders(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date, o.total_amount,
               w.name AS warehouse_name, c.name AS customer_name, c.email
        FROM orders o
        JOIN warehouses w ON o.warehouse_id = w.id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.staff_id = %s
        ORDER BY o.order_date DESC
    ''', (staff_id,))
    orders = cursor.fetchall()
    for o in orders:
        cursor.execute('''
            SELECT oi.product_id, p.name, oi.quantity, p.unit
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        ''', (o['id'],))
        o['items'] = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('reg.html')

@app.route('/order')
def order():
    user_id = session.get('user_id', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, category, price, unit, status, manufacturing_date, expiry_date, image FROM products WHERE status = 'available'")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('place_order.html', user_id=user_id, products=products)


def generate_unique_customer_id(cursor):
    while True:
        customer_id = f"cs{random.randint(10000, 99999)}"
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        if not cursor.fetchone():
            return customer_id

def generate_unique_staff_id(cursor):
    while True:
        staff_id = f"staff{random.randint(10000, 99999)}"
        cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (staff_id,))
        if not cursor.fetchone():
            return staff_id

def generate_unique_password():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

@app.route('/register/customer', methods=['POST'])
def register_customer():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    customer_id = generate_unique_customer_id(cursor)
    password = generate_unique_password()
    cursor.execute("""
        INSERT INTO customers (customer_id, name, email, phone, address, city, state, zip_code, country, password)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (customer_id, data['name'], data['email'], data['phone'], data['address'],
          data['city'], data['state'], data['zip_code'], data['country'], password))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"customer_id": customer_id, "password": password}), 201

@app.route('/register/staff', methods=['POST'])
def register_staff():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    staff_id = generate_unique_staff_id(cursor)
    password = generate_unique_password()
    cursor.execute("""
        INSERT INTO staff (staff_id, name, email, phone, age, city, address, password)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (staff_id, data['name'], data['email'], data['phone'], data['age'],
          data['city'], data['address'], password))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"staff_id": staff_id, "password": password}), 201

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    user_id = request.form['user_id']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if user_id.startswith("cs"):
        table = "customers"
        id_col = "customer_id"
        profile_url = 'customer_profile'
    elif user_id.startswith("staff"):
        table = "staff"
        id_col = "staff_id"
        profile_url = 'staff_profile'
    elif user_id.startswith("admin"):
        table = "admin"
        id_col = "admin_id"
        profile_url = 'admin_dashboard'
    else:
        return render_template('login.html', error="Invalid user ID format!")

    cursor.execute(f"SELECT * FROM {table} WHERE {id_col} = %s AND password = %s", (user_id, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        session['user_id'] = user_id
        session['user_type'] = profile_url
        return redirect(url_for(profile_url, user_id=user_id))
    else:
        return render_template('login.html', error="Invalid credentials!")

@app.route('/customer/<user_id>')
def customer_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return render_template('customer.html', user=user, user_type='Customer')
    return "Customer not found!"



@app.route('/admin/profile/<user_id>')
def admin_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return render_template('profile.html', user=user, user_type='Admin')
    return "Admin not found!"

@app.route('/staff/<user_id>')
def staff_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return render_template('staff.html', user=user, user_type='Staff')
    return "Staff not found!"



#profile staff and customer;
@app.route('/api/customer_orders/<customer_id>')
def api_customer_orders(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date, o.total_amount,
               w.name AS warehouse_name, o.distance_km, o.transport_cost, o.transport_time_hours
        FROM orders o
        JOIN warehouses w ON o.warehouse_id = w.id
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC
    """, (customer_id,))
    orders = cursor.fetchall()
    for o in orders:
        cursor.execute("""
            SELECT oi.product_id, p.name, oi.quantity, p.unit
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (o['id'],))
        o['items'] = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(orders)
@app.route('/customer/profile/<user_id>')
def customer_profile1(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return render_template('profile.html', user=user, user_type='Customer')
    return "Customer not found!"


@app.route('/staff/profile/<user_id>')
def staff_profile1(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return render_template('profile.html', user=user, user_type='Staff')
    return "Staff not found!"

    
@app.route('/admin/<user_id>', methods=['GET', 'POST'])
def admin_dashboard(user_id):
    print(f"[DEBUG] admin_dashboard called with user_id={user_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get admin
    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (user_id,))
    user = cursor.fetchone()
    print(f"[DEBUG] admin query result: {user}")
    if not user:
        cursor.close()
        conn.close()
        print(f"[ERROR] Admin not found for user_id={user_id}")
        return "Admin not found!", 404

    # Get products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    # Get warehouses and their stock
    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()

    for warehouse in warehouses:
        cursor.execute("""
            SELECT ws.id AS stock_id, ws.quantity, p.name, p.id AS product_id, p.image
            FROM warehouse_stock ws
            JOIN products p ON ws.product_id = p.id
            WHERE ws.warehouse_id = %s
        """, (warehouse['id'],))
        warehouse['stock'] = cursor.fetchall()

    # Get orders
    cursor.execute("""
        SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date,
               c.name AS customer_name, c.email, c.city, w.name AS warehouse_name, s.name AS staff_name, o.total_amount
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN warehouses w ON o.warehouse_id = w.id
        LEFT JOIN staff s ON o.staff_id = s.staff_id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    # Attach items to each order
    for o in orders:
        cursor.execute("""
            SELECT oi.product_id, p.name, oi.quantity, p.unit, p.image
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (o['id'],))
        o['items'] = cursor.fetchall()

    # Get customers
    cursor.execute("SELECT customer_id, name, email, phone, address, city, state, zip_code FROM customers")
    customers = cursor.fetchall()

    # Get staff
    cursor.execute("SELECT staff_id, name, email, phone, city FROM staff")
    staff = cursor.fetchall()

    # Always fetch latest stock for full dashboard
    cursor.execute("""
        SELECT w.name AS warehouse_name, p.name AS product_name, ws.quantity
        FROM warehouse_stock ws
        JOIN warehouses w ON ws.warehouse_id = w.id
        JOIN products p ON ws.product_id = p.id
    """)
    stock = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        'admin.html',
        user=user,
        products=products,
        warehouses=warehouses,
        orders=orders,
        customers=customers,
        staff=staff,
        stock=stock,
        prod_msg=None,
        prod_success=True,
        stock_msg=None,   # Pass default values so template won't break
        stock_success=True
    )

@app.route('/admin/<user_id>/products', methods=['POST'])
def admin_products(user_id):
    prod_msg = None
    prod_success = False
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()
    for warehouse in warehouses:
        cursor.execute("""
            SELECT ws.quantity, p.name, p.id, p.image
            FROM warehouse_stock ws
            JOIN products p ON ws.product_id = p.id
            WHERE ws.warehouse_id = %s
        """, (warehouse['id'],))
        warehouse['stock'] = cursor.fetchall()
    

    
    if user:
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        unit = request.form['unit']
        status = request.form['status']
        manufacturing_date = request.form.get('manufacturing_date')
        # Calculate expiry_date as manufacturing_date + 6 months
        expiry_date = None
        if manufacturing_date:
            try:
                mfg_date = datetime.datetime.strptime(manufacturing_date, "%Y-%m-%d")
                expiry_date = (mfg_date + datetime.timedelta(days=182)).strftime("%Y-%m-%d")
            except Exception:
                expiry_date = None
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
                image_filename = filename
        try:
            cursor.execute('''INSERT INTO products 
                (name, category, price, unit, status, manufacturing_date, expiry_date, image) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                           (name, category, price, unit, status, manufacturing_date, expiry_date, image_filename))
            conn.commit()
            prod_msg = "Product added successfully!"
            prod_success = True

            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
        except Exception as e:
            prod_msg = "Failed to add product: " + str(e)
            prod_success = False

    # Always fetch latest orders, customers, staff, and stock for full dashboard
    cursor.execute("""
        SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date,
               c.name AS customer_name, c.email, c.city, w.name AS warehouse_name, s.name AS staff_name, o.total_amount
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN warehouses w ON o.warehouse_id = w.id
        LEFT JOIN staff s ON o.staff_id = s.staff_id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    for o in orders:
        cursor.execute("""
            SELECT oi.product_id, p.name, oi.quantity, p.unit, p.image
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (o['id'],))
        o['items'] = cursor.fetchall()
    cursor.execute("SELECT customer_id, name, email, phone, address, city, state, zip_code FROM customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT staff_id, name, email, phone, city FROM staff")
    staff = cursor.fetchall()
    cursor.execute("""
        SELECT w.name AS warehouse_name, p.name AS product_name, ws.quantity
        FROM warehouse_stock ws
        JOIN warehouses w ON ws.warehouse_id = w.id
        JOIN products p ON ws.product_id = p.id
    """)
    stock = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', user=user, products=products, warehouses=warehouses,
                           orders=orders, customers=customers, staff=staff, stock=stock,
                           prod_msg=prod_msg, prod_success=prod_success)

@app.route('/admin/<user_id>/warehouses', methods=['POST'])
def admin_warehouses(user_id):
    wh_msg = None
    wh_success = False
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch admin
    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (user_id,))
    user = cursor.fetchone()

    # Fetch products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    # Fetch warehouses + stock
    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()
    for warehouse in warehouses:
        cursor.execute("""
            SELECT ws.quantity, p.name, p.id, p.image
            FROM warehouse_stock ws
            JOIN products p ON ws.product_id = p.id
            WHERE ws.warehouse_id = %s
        """, (warehouse['id'],))
        warehouse['stock'] = cursor.fetchall()

    if user:
        name = request.form['name']
        address = request.form['address']
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')

        try:
            cursor.execute('''
                INSERT INTO warehouses (name, address, city, state, zip_code)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, address, city, state, zip_code))
            conn.commit()
            wh_msg = "Warehouse added successfully!"
            wh_success = True

            cursor.execute("SELECT * FROM warehouses")
            warehouses = cursor.fetchall()
        except Exception as e:
            wh_msg = "Failed to add warehouse: " + str(e)
            wh_success = False

    # You might also want orders, customers, staff fetched here like in admin_dashboard
    cursor.execute("""SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date,
                             c.name AS customer_name, w.name AS warehouse_name, s.name AS staff_name, o.total_amount
                      FROM orders o
                      JOIN customers c ON o.customer_id = c.customer_id
                      JOIN warehouses w ON o.warehouse_id = w.id
                      LEFT JOIN staff s ON o.staff_id = s.staff_id
                      ORDER BY o.order_date DESC""")
    orders = cursor.fetchall()

    cursor.execute("SELECT customer_id, name, email, phone, address, city, state, zip_code FROM customers")
    customers = cursor.fetchall()

    cursor.execute("SELECT staff_id, name, email, phone, city FROM staff")
    staff = cursor.fetchall()

    # Always fetch latest stock for full dashboard
    cursor.execute("""
        SELECT w.name AS warehouse_name, p.name AS product_name, ws.quantity
        FROM warehouse_stock ws
        JOIN warehouses w ON ws.warehouse_id = w.id
        JOIN products p ON ws.product_id = p.id
    """)
    stock = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', user=user, products=products, warehouses=warehouses,
                           orders=orders, customers=customers, staff=staff,
                           stock=stock, wh_msg=wh_msg, wh_success=wh_success)

@app.route('/admin/<user_id>/warehouse_stock', methods=['POST'])
def admin_warehouse_stock(user_id):
    stock_msg = None
    stock_success = False
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Validate admin
    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return "Admin not found", 404

    # Get form data
    warehouse_id = request.form['warehouse_id']
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])

    try:
        cursor.execute("""
            SELECT * FROM warehouse_stock 
            WHERE warehouse_id=%s AND product_id=%s
        """, (warehouse_id, product_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE warehouse_stock
                SET quantity = quantity + %s
                WHERE warehouse_id = %s AND product_id = %s
            """, (quantity, warehouse_id, product_id))
        else:
            cursor.execute("""
                INSERT INTO warehouse_stock (warehouse_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (warehouse_id, product_id, quantity))

        conn.commit()
        stock_msg = "✅ Stock updated successfully!"
        stock_success = True

    except Exception as e:
        stock_msg = f"❌ Failed to update stock: {str(e)}"
        stock_success = False

    # Always fetch latest orders, customers, staff, products, warehouses, and stock for full dashboard
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("SELECT * FROM warehouses")
    warehouses = cursor.fetchall()
    cursor.execute("""
        SELECT o.id, o.order_code, o.status, o.order_date, o.delivery_date,
               c.name AS customer_name, c.email, c.city, w.name AS warehouse_name, s.name AS staff_name, o.total_amount
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN warehouses w ON o.warehouse_id = w.id
        LEFT JOIN staff s ON o.staff_id = s.staff_id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()
    for o in orders:
        cursor.execute("""
            SELECT oi.product_id, p.name, oi.quantity, p.unit, p.image
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (o['id'],))
        o['items'] = cursor.fetchall()
    cursor.execute("SELECT customer_id, name, email, phone, address, city, state, zip_code FROM customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT staff_id, name, email, phone, city FROM staff")
    staff = cursor.fetchall()
    cursor.execute("""
        SELECT w.name AS warehouse_name, p.name AS product_name, ws.quantity
        FROM warehouse_stock ws
        JOIN warehouses w ON ws.warehouse_id = w.id
        JOIN products p ON ws.product_id = p.id
    """)
    stock = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        'admin.html',
        user=user,
        warehouses=warehouses,
        products=products,
        stock=stock,
        orders=orders,
        customers=customers,
        staff=staff,
        stock_msg=stock_msg,
        stock_success=stock_success
    )

    
@app.route('/staff/<user_id>/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(user_id, order_id):
    new_status = request.form.get('status')
    if new_status not in ['dispatched', 'out_for_delivery', 'delivered']:
        return "Invalid status", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id = %s AND staff_id = %s", (order_id, user_id))
    order = cursor.fetchone()
    if not order:
        cursor.close()
        conn.close()
        return "Order not found or not assigned to you", 404

    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
    conn.commit()
    cursor.close()
    conn.close()
    return "Order status updated successfully"

@app.route('/customer/<user_id>/orders', methods=['POST'])
def place_order(user_id):
    data = request.json
    products = data.get('products')

    if not products or not isinstance(products, list):
        return jsonify({"error": "Invalid products list"}), 400

    # Validate all quantities are at least 1
    for p in products:
        if int(p.get('quantity', 0)) < 1:
            return jsonify({"error": f"Invalid quantity for product {p.get('product_id', '')}. Must be at least 1."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT city, state FROM customers WHERE customer_id = %s", (user_id,))
    customer = cursor.fetchone()
    if not customer:
        cursor.close()
        conn.close()
        return jsonify({"error": "Customer not found"}), 404

    customer_city = customer[0].strip().lower()
    customer_state = customer[1]

    # City-to-zone mapping for warehouse selection
    ZONE_A_CITIES = [
        "chennai", "tiruvallur", "kanchipuram", "chengalpattu", "ranipet", "vellore", "tirupathur", "tiruvannamalai", "villupuram", "kallakurichi", "cuddalore", "mayiladuthurai", "nagapattinam", "thanjavur", "tiruvarur", "ariyalur", "perambalur", "pudukkottai", "tiruchirappalli"
    ]
    ZONE_B_CITIES = [
        "madurai", "dindigul", "theni", "sivagangai", "ramanathapuram", "virudhunagar", "tirunelveli", "thoothukudi", "kanyakumari", "tenkasi", "coimbatore", "tiruppur", "erode", "namakkal", "karur", "salem", "dharmapuri", "krishnagiri", "nilgiris"
    ]
    warehouse_city = None
    if customer_city in ZONE_A_CITIES:
        warehouse_city = "Chennai"
    elif customer_city in ZONE_B_CITIES:
        warehouse_city = "Madurai"
    else:
        cursor.close()
        conn.close()
        return jsonify({"error": "No warehouse found for customer city/zone"}), 400

    cursor.execute("SELECT id FROM warehouses WHERE city = %s LIMIT 1", (warehouse_city,))
    wh_result = cursor.fetchone()
    if not wh_result:
        cursor.close()
        conn.close()
        return jsonify({"error": "No warehouse found for mapped city"}), 400
    warehouse_id = wh_result[0]

    total_amount = 0
    for p in products:
        cursor.execute("SELECT price FROM products WHERE id = %s", (p['product_id'],))
        price = cursor.fetchone()
        if not price:
            cursor.close()
            conn.close()
            return jsonify({"error": f"Product {p['product_id']} not found"}), 404
        total_amount += price[0] * p['quantity']

    # Calculate transport info
    wh_city_norm = warehouse_city.strip().lower()
    km, cost, time_hours = calculate_transport(wh_city_norm, customer_city)
    if km is None:
        km, cost, time_hours = 0, 0, 0
    order_code = f"ORD{random.randint(10000, 99999)}"
    cursor.execute("""
        INSERT INTO orders (order_code, customer_id, warehouse_id, status, total_amount, distance_km, transport_cost, transport_time_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (order_code, user_id, warehouse_id, 'pending', total_amount, km, cost, time_hours))
    order_id = cursor.lastrowid

    for p in products:
        cursor.execute("SELECT price FROM products WHERE id = %s", (p['product_id'],))
        price = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, p['product_id'], p['quantity'], price * p['quantity']))

        # Check stock in mapped region warehouse only
        cursor.execute("SELECT quantity FROM warehouse_stock WHERE warehouse_id = %s AND product_id = %s", (warehouse_id, p['product_id']))
        qty_needed = p['quantity']
        wh_stock = cursor.fetchone()
        wh_qty = wh_stock[0] if wh_stock else 0
        if wh_qty >= qty_needed:
            # Deduct all from mapped region warehouse
            cursor.execute("""
                UPDATE warehouse_stock
                SET quantity = quantity - %s
                WHERE warehouse_id = %s AND product_id = %s
            """, (qty_needed, warehouse_id, p['product_id']))
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": f"Product {p['product_id']} is out of stock in your region warehouse."}), 400

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Order placed successfully", "order_code": order_code}), 201

# ===== ORDER DETAILS =====
@app.route("/admin/order/<order_id>")
def get_order_details(order_id):
    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT o.*, c.* FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_id = %s
    """, (order_id,))
    order = cur.fetchone()

    cur.execute("""
        SELECT i.* FROM order_items i
        WHERE i.order_id = %s
    """, (order_id,))
    items = cur.fetchall()

    db.close()
    return jsonify({
        "customer": order,
        "status": order["status"],
        "items": items
    })

# ===== STAFF NEAR A CITY =====
@app.route("/admin/staff_near/<city>")
def staff_near(city):
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM staff WHERE city = %s", (city,))
    staff_list = cur.fetchall()
    db.close()
    return jsonify(staff_list)

# ===== ASSIGN STAFF =====
@app.route("/admin/assign_staff/<order_id>", methods=["POST"])
def assign_staff(order_id):
    staff_id = request.json.get("staff_id")
    print(f"[DEBUG] assign_staff called with order_id={order_id}, staff_id={staff_id}")
    db = get_db_connection()
    cur = db.cursor()
    # Set status to 'Order Confirmed' when staff is assigned
    result = cur.execute("UPDATE orders SET staff_id = %s, status = 'Order Confirmed' WHERE id = %s", (staff_id, order_id))
    print(f"[DEBUG] SQL executed, result={result}")
    db.commit()
    db.close()
    return jsonify({"message": "Staff assigned successfully"})




# --- helper: generate order_code ---
def generate_order_code(cursor):
    while True:
        code = f"ORD{random.randint(100000, 999999)}"
        cursor.execute("SELECT id FROM orders WHERE order_code = %s", (code,))
        if not cursor.fetchone():
            return code

# --- API: get products as JSON (optional) ---
@app.route('/api/products')
def api_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, category, price, unit, status, manufacturing_date, expiry_date, image FROM products WHERE status IN ('available', 'In Stock', 'available')")
    prods = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(prods)

# --- Page: place order (customer-facing) ---
@app.route('/place-order')
def place_order_page():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, category, price, unit, status, manufacturing_date, expiry_date, image FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('place_order.html', products=products)

# --- Page: place order (customer-facing) ---
'''@app.route('/place-order')
def place_order_page():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            id, 
            name, 
            category, 
            price, 
            description, 
            status, 
            manufacturing_date,
            image 
        FROM products 
    """)
    
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('place_order.html', products=products)
'''
# --- API Checkout: creates order and order_items ---
@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid payload"}), 400

    customer_id = data.get('customer_id')
    items = data.get('items', [])
    total_amount = data.get('total_amount', 0)

    if not customer_id or not items:
        return jsonify({"success": False, "error": "Missing customer_id or items"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Validate customer exists
    cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "Customer not found"}), 404

    # Zone logic: get customer city
    cursor.execute("SELECT city FROM customers WHERE customer_id = %s", (customer_id,))
    customer_row = cursor.fetchone()
    if not customer_row:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "Customer not found"}), 404
    customer_city = customer_row['city'].strip().lower()
    ZONE_A_CITIES = [
        "chennai", "tiruvallur", "kanchipuram", "chengalpattu", "ranipet", "vellore", "tirupathur", "tiruvannamalai", "villupuram", "kallakurichi", "cuddalore", "mayiladuthurai", "nagapattinam", "thanjavur", "tiruvarur", "ariyalur", "perambalur", "pudukkottai", "tiruchirappalli"
    ]
    ZONE_B_CITIES = [
        "madurai", "dindigul", "theni", "sivagangai", "ramanathapuram", "virudhunagar", "tirunelveli", "thoothukudi", "kanyakumari", "tenkasi", "coimbatore", "tiruppur", "erode", "namakkal", "karur", "salem", "dharmapuri", "krishnagiri", "nilgiris"
    ]
    warehouse_city = None
    if customer_city in ZONE_A_CITIES:
        warehouse_city = "Chennai"
    elif customer_city in ZONE_B_CITIES:
        warehouse_city = "Madurai"
    else:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "No warehouse found for customer city/zone"}), 400

    cursor.execute("SELECT id FROM warehouses WHERE city = %s LIMIT 1", (warehouse_city,))
    wh_result = cursor.fetchone()
    if not wh_result:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": "No warehouse found for mapped city"}), 400
    warehouse_id = wh_result['id']

    # Check stock and deduct only from mapped region warehouse
    for it in items:
        pid = int(it['product_id'])
        qty = int(it['quantity'])
        if qty < 1:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"Invalid quantity for product ID {pid}. Must be at least 1."}), 400
        cursor.execute("SELECT quantity FROM warehouse_stock WHERE warehouse_id = %s AND product_id = %s", (warehouse_id, pid))
        wh_stock = cursor.fetchone()
        wh_qty = wh_stock['quantity'] if wh_stock else 0
        if wh_qty >= qty:
            # Deduct all from mapped region warehouse
            cursor.execute("UPDATE warehouse_stock SET quantity = quantity - %s, updated_on = NOW() WHERE warehouse_id = %s AND product_id = %s", (qty, warehouse_id, pid))
        else:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": f"Product ID {pid} is out of stock in your region warehouse."}), 400

    # create order
    # Calculate transport info
    wh_city_norm = warehouse_city.strip().lower()
    km, cost, time_hours = calculate_transport(wh_city_norm, customer_city)
    if km is None:
        km, cost, time_hours = 0, 0, 0
    order_code = generate_order_code(cursor)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO orders (order_code, customer_id, warehouse_id, status, order_date, total_amount, distance_km, transport_cost, transport_time_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_code, customer_id, warehouse_id, 'pending', now, total_amount, km, cost, time_hours))
        order_id = cursor.lastrowid

        # insert order_items — assumes table exists
        for it in items:
            pid = int(it['product_id'])
            qty = int(it['quantity'])
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s,%s,%s)",
                           (order_id, pid, qty))


        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

    cursor.close()
    conn.close()
    return jsonify({"success": True, "order_id": order_id, "order_code": order_code})

# Tamil Nadu city distances from warehouses
DISTANCES = {
    "madurai": {
        "chennai": 460, "madurai": 0, "coimbatore": 215, "tiruchirappalli": 135, "salem": 230, "tirunelveli": 150, "thoothukudi": 150, "dindigul": 65, "theni": 80, "virudhunagar": 50, "ramanathapuram": 110, "sivagangai": 50, "karur": 120, "namakkal": 170, "erode": 210, "tiruppur": 200, "krishnagiri": 320, "dharmapuri": 270, "kanyakumari": 235, "tenkasi": 160, "thanjavur": 180, "thiruvarur": 210, "nagapattinam": 250, "mayiladuthurai": 270, "cuddalore": 290, "villupuram": 310, "kallakurichi": 320, "tiruvannamalai": 350, "vellore": 400, "kanchipuram": 420, "chengalpattu": 430, "tiruvallur": 440, "ranipet": 410, "tirupathur": 390, "perambalur": 140, "ariyalur": 160, "pudukkottai": 90, "nilgiris": 270
    },
    "chennai": {
        "chennai": 0, "madurai": 460, "coimbatore": 510, "tiruchirappalli": 330, "salem": 340, "tirunelveli": 610, "thoothukudi": 610, "dindigul": 420, "theni": 480, "virudhunagar": 510, "ramanathapuram": 530, "sivagangai": 500, "karur": 390, "namakkal": 350, "erode": 400, "tiruppur": 410, "krishnagiri": 250, "dharmapuri": 220, "kanyakumari": 700, "tenkasi": 620, "thanjavur": 340, "thiruvarur": 360, "nagapattinam": 320, "mayiladuthurai": 280, "cuddalore": 180, "villupuram": 160, "kallakurichi": 190, "tiruvannamalai": 190, "vellore": 140, "kanchipuram": 70, "chengalpattu": 60, "tiruvallur": 40, "ranipet": 120, "tirupathur": 180, "perambalur": 270, "ariyalur": 290, "pudukkottai": 350, "nilgiris": 500
    }
}

def calculate_transport(warehouse, customer_city):
    warehouse = warehouse.lower()
    customer_city = customer_city.lower()
    print(warehouse," ",customer_city)
    print("\n")
    print(DISTANCES[warehouse])
    print(DISTANCES[warehouse][customer_city])
    if warehouse in DISTANCES and customer_city in DISTANCES[warehouse]:
        km = DISTANCES[warehouse][customer_city]
        cost = km * 5
        time_hours = round(km / 60, 2)  # 60 km/h
        return km, cost, time_hours
    return None, None, None



@app.route('/logout')
def logout():
    session.clear()
    return render_template('home.html')

# --- API: Update order status ---
@app.route('/api/update_order_status/<int:order_id>', methods=['POST'])
def api_update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return jsonify({'success': False, 'error': 'No status provided'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- API: Order status history (for customer tracking) ---
@app.route('/api/order_status/<int:order_id>')
def api_order_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status, order_date, delivery_date FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    # Dummy: In real app, you would store each status change with a timestamp
    # Here, we infer steps from status and dates
    status_map = {
        'confirmed': False,
        'shipped': False,
        'out_for_delivery': False,
        'delivered': False
    }
    date_map = {}
    if order['status'] in ['Order Confirmed', 'Shipped', 'Out For Delivery', 'Delivered']:
        status_map['confirmed'] = True
        date_map['confirmed'] = order['order_date']
    if order['status'] in ['Shipped', 'Out For Delivery', 'Delivered']:
        status_map['shipped'] = True
        date_map['shipped'] = order['order_date']
    if order['status'] in ['Out For Delivery', 'Delivered']:
        status_map['out_for_delivery'] = True
        date_map['out_for_delivery'] = order['order_date']
    if order['status'] == 'Delivered':
        status_map['delivered'] = True
        date_map['delivered'] = order['delivery_date']
    return jsonify({'success': True, 'status': status_map, 'dates': date_map})

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)


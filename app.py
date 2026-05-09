# ------------------------------------------------------------
# web_app/app.py - Flask Web Interface (COMPLETE WITH ALL APIs)
# ------------------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, send_file
from functools import wraps
import sys
import os
import re
import secrets
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from languages import set_language, get_language

app = Flask(__name__)

# ==================== SECURITY CONFIGURATION ====================
app.secret_key = secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)

# ==================== EXCHANGE RATES (Base Currency: SYP) ====================
EXCHANGE_RATES = {
    'SYP': 1.0,
    'USD': 15000.0,
    'JOD': 21126.0,
    'EUR': 16350.0,
    'SAR': 4000.0
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'JOD': 'JD',
    'SYP': '£S',
    'EUR': '€',
    'SAR': '﷼'
}

CURRENCY_NAMES = {
    'USD': 'دولار أمريكي',
    'JOD': 'دينار أردني',
    'SYP': 'ليرة سورية',
    'EUR': 'يورو',
    'SAR': 'ريال سعودي'
}

# ==================== SECURITY HEADERS ====================
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# ==================== RATE LIMITING ====================
rate_limit_storage = {}
failed_attempts_storage = {}

def rate_limit(key, limit=10, window=60):
    now = datetime.now()
    if key not in rate_limit_storage:
        rate_limit_storage[key] = []
    rate_limit_storage[key] = [t for t in rate_limit_storage[key] if now - t < timedelta(seconds=window)]
    if len(rate_limit_storage[key]) >= limit:
        return False
    rate_limit_storage[key].append(now)
    return True

def check_failed_attempts(user_id):
    if user_id in failed_attempts_storage:
        attempts, last_attempt = failed_attempts_storage[user_id]
        if attempts >= 5 and datetime.now() - last_attempt < timedelta(minutes=15):
            return False, 15
        elif attempts >= 5:
            del failed_attempts_storage[user_id]
    return True, 0

def record_failed_attempt(user_id):
    if user_id not in failed_attempts_storage:
        failed_attempts_storage[user_id] = [1, datetime.now()]
    else:
        attempts, _ = failed_attempts_storage[user_id]
        failed_attempts_storage[user_id] = [attempts + 1, datetime.now()]

def reset_failed_attempts(user_id):
    if user_id in failed_attempts_storage:
        del failed_attempts_storage[user_id]

# ==================== INPUT VALIDATION ====================
def sanitize_input(text):
    if not text:
        return text
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '`', '(', ')', '[', ']', '{', '}']
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text.strip()

def validate_account_number(account_number):
    return re.match(r'^ACC\d{3}$', account_number) is not None

def validate_amount(amount, max_amount=1000000000):
    try:
        amount = float(amount)
        return amount > 0 and amount <= max_amount
    except (ValueError, TypeError):
        return False

def validate_username(username):
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username) is not None

def validate_password(password):
    return len(password) >= 6

# ==================== AUTHORIZATION HELPER FUNCTIONS ====================
def get_user_accounts(username):
    db_local = Database()
    accounts = db_local.get_all_accounts_with_users()
    db_local.close()
    user_accounts = []
    for acc in accounts:
        if acc[1] == username:
            user_accounts.append(acc[0])
    return user_accounts

def user_owns_account(username, account_number):
    accounts = get_user_accounts(username)
    return account_number in accounts

def get_all_accounts():
    db_local = Database()
    accounts = db_local.get_all_accounts_with_users()
    db_local.close()
    accounts_list = []
    for acc in accounts:
        accounts_list.append({
            'account_number': acc[0],
            'username': acc[1],
            'balance': acc[3]
        })
    return accounts_list

# ==================== LOGGING ====================
import logging
from logging.handlers import RotatingFileHandler

def log_activity(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        if 'user_id' in session:
            app.logger.info(f"USER_ACTION: {session.get('username')} ({session.get('role')}) - {request.method} {request.path}")
        return result
    return decorated_function

if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/web_app.log', maxBytes=10485760, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

db = Database()

# ==================== CSRF PROTECTION ====================
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def validate_csrf_token(token):
    return token and session.get('_csrf_token') == token

# ==================== AUTH DECORATOR ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== CURRENCY CONVERSION HELPER ====================
def convert_currency(amount, from_currency, to_currency):
    try:
        amount = float(amount)
        amount_in_syp = amount * EXCHANGE_RATES.get(from_currency, 1)
        converted = amount_in_syp / EXCHANGE_RATES.get(to_currency, 1)
        return round(converted, 2)
    except:
        return amount

# ==================== ROUTES ====================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
@log_activity
def login():
    client_ip = request.remote_addr
    if not rate_limit(f'login_{client_ip}', limit=5, window=300):
        return render_template('login.html', error="Too many attempts. Please try again later.")
    
    username = sanitize_input(request.form.get('username', ''))
    password = request.form.get('password', '')
    
    if not username or not password:
        return render_template('login.html', error="Username and password are required")
    
    user = db.authenticate(username, password)
    if user:
        session.clear()
        session['user_id'] = user[0]
        session['username'] = username
        session['role'] = user[1]
        session.permanent = True
        session['_csrf_token'] = secrets.token_hex(32)
        session['user_accounts'] = get_user_accounts(username)
        
        app.logger.info(f"LOGIN: {username} ({user[1]}) from IP: {client_ip}")
        return redirect(url_for('dashboard'))
    else:
        app.logger.warning(f"FAILED_LOGIN: {username} from IP: {client_ip}")
        return render_template('login.html', error="Invalid username or password")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                          username=session.get('username'),
                          role=session.get('role'),
                          lang=session.get('language', 'en'),
                          csrf_token=session.get('_csrf_token'),
                          user_accounts=session.get('user_accounts', []))

@app.route('/logout')
@log_activity
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/set_language/<lang>')
def set_language_route(lang):
    if lang in ['en', 'ar']:
        set_language(lang)
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# ==================== CHANGE PASSWORD API ====================
@app.route('/api/change_password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json()
    username = session.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    success, message = db.update_password(username, old_password, new_password)
    return jsonify({'success': success, 'message': message})

# ==================== USER EXTRA INFO API ====================
@app.route('/api/user_info', methods=['GET', 'POST'])
@login_required
def api_user_info():
    username = session.get('username')
    
    if request.method == 'GET':
        cursor = db.get_cursor()
        cursor.execute("SELECT national_id, email, phone, address FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        if result:
            return jsonify({
                'success': True,
                'national_id': result[0] or '',
                'email': result[1] or '',
                'phone': result[2] or '',
                'address': result[3] or ''
            })
        return jsonify({'success': True, 'national_id': '', 'email': '', 'phone': '', 'address': ''})
    
    else:  # POST
        data = request.get_json()
        national_id = sanitize_input(data.get('national_id', ''))
        email = sanitize_input(data.get('email', ''))
        phone = sanitize_input(data.get('phone', ''))
        address = sanitize_input(data.get('address', ''))
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if columns exist, if not add them
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'national_id' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN national_id TEXT")
        if 'email' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if 'phone' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        if 'address' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        
        # Update user info
        cursor.execute("""
            UPDATE users SET national_id = ?, email = ?, phone = ?, address = ?
            WHERE username = ?
        """, (national_id, email, phone, address, username))
        conn.commit()
        
        app.logger.info(f"USER_INFO_UPDATED: {username}")
        return jsonify({'success': True, 'message': 'تم تحديث المعلومات بنجاح'})

# ==================== RATINGS API ====================
@app.route('/api/ratings', methods=['GET'])
def api_get_ratings():
    cursor = db.get_cursor()
    
    # Create ratings table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT username, rating, comment, created_at FROM ratings ORDER BY created_at DESC LIMIT 50")
    ratings = cursor.fetchall()
    
    cursor.execute("SELECT AVG(rating), COUNT(*) FROM ratings")
    avg_result = cursor.fetchone()
    
    ratings_list = []
    for r in ratings:
        ratings_list.append({
            'username': r[0],
            'rating': r[1],
            'comment': r[2],
            'created_at': r[3]
        })
    
    return jsonify({
        'success': True,
        'ratings': ratings_list,
        'average_rating': round(avg_result[0], 2) if avg_result[0] else 0,
        'total_ratings': avg_result[1] if avg_result[1] else 0
    })

@app.route('/api/rate', methods=['POST'])
@login_required
def api_rate():
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')
    username = session.get('username')
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'success': False, 'error': 'تقييم غير صحيح'})
    
    cursor = db.get_cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if user already rated
    cursor.execute("SELECT rating_id FROM ratings WHERE username=?", (username,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE ratings SET rating=?, comment=?, created_at=CURRENT_TIMESTAMP WHERE username=?", 
                       (rating, comment, username))
    else:
        cursor.execute("INSERT INTO ratings (username, rating, comment) VALUES (?, ?, ?)", 
                       (username, rating, comment))
    
    db.get_connection().commit()
    app.logger.info(f"RATING_SUBMITTED: {username} rated {rating}")
    
    return jsonify({'success': True, 'message': 'تم إرسال تقييمك بنجاح'})

# ==================== COMPLAINTS API ====================
@app.route('/api/complaint', methods=['POST'])
@login_required
def api_complaint():
    data = request.get_json()
    complaint_text = sanitize_input(data.get('complaint_text', ''))
    user_id = session.get('user_id')
    
    if not complaint_text:
        return jsonify({'success': False, 'error': 'الرجاء إدخال نص الشكوى'})
    
    cursor = db.get_cursor()
    
    # Create complaints table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')
    
    cursor.execute("INSERT INTO complaints (user_id, complaint_text) VALUES (?, ?)", 
                   (user_id, complaint_text))
    db.get_connection().commit()
    
    app.logger.info(f"COMPLAINT_SUBMITTED: user_id {user_id}")
    return jsonify({'success': True, 'message': 'تم إرسال شكواك بنجاح'})

@app.route('/api/complaints', methods=['GET'])
@login_required
def api_get_complaints():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    cursor = db.get_cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT complaint_id, complaint_text, status, created_at FROM complaints ORDER BY created_at DESC")
    complaints = cursor.fetchall()
    
    complaints_list = []
    for c in complaints:
        complaints_list.append({
            'complaint_id': c[0],
            'complaint_text': c[1],
            'status': c[2],
            'created_at': c[3]
        })
    
    return jsonify({'success': True, 'complaints': complaints_list})

@app.route('/api/complaint/resolve', methods=['POST'])
@login_required
def api_resolve_complaint():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    
    cursor = db.get_cursor()
    cursor.execute("UPDATE complaints SET status='resolved', resolved_at=CURRENT_TIMESTAMP WHERE complaint_id=?", (complaint_id,))
    db.get_connection().commit()
    
    app.logger.info(f"COMPLAINT_RESOLVED: id {complaint_id}")
    return jsonify({'success': True, 'message': 'تم تحديث حالة الشكوى'})

# ==================== PDF STATEMENT API ====================
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import io

@app.route('/api/statement', methods=['GET'])
@login_required
def api_statement():
    account_number = request.args.get('account_number')
    currency = request.args.get('currency', 'SYP')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not validate_account_number(account_number):
        return jsonify({'error': 'Invalid account number'}), 400
    
    # Verify ownership or admin/teller
    role = session.get('role')
    username = session.get('username')
    if role not in ['admin', 'teller'] and not user_owns_account(username, account_number):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get account info
    balance = db.get_balance(account_number)
    if balance is None:
        return jsonify({'error': 'Account not found'}), 404
    
    # Get account owner info
    accounts = db.get_all_accounts_with_users()
    owner_name = ""
    for acc in accounts:
        if acc[0] == account_number:
            owner_name = acc[1]
            break
    
    # Get transaction history
    history = db.get_transaction_history(account_number, limit=100)
    
    # Filter by date if provided
    if date_from:
        history = [t for t in history if t[3] >= date_from]
    if date_to:
        history = [t for t in history if t[3] <= date_to + ' 23:59:59']
    
    # Convert currency
    balance_converted = convert_currency(balance, 'SYP', currency)
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1e3a5f'), alignment=1, spaceAfter=15)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=9, spaceAfter=4)
    
    elements = []
    
    elements.append(Paragraph("🏦 بنك التوفير", title_style))
    elements.append(Paragraph("<b>كشف حساب</b>", title_style))
    elements.append(Spacer(1, 10))
    
    # Account info
    info_data = [
        ["رقم الحساب:", account_number],
        ["اسم صاحب الحساب:", owner_name],
        ["العملة:", currency],
        ["الرصيد الحالي:", f"{balance_converted:,.2f} {currency}"],
        ["تاريخ الكشف:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    ]
    if date_from or date_to:
        info_data.append(["الفترة:", f"{date_from or 'البداية'} إلى {date_to or 'اليوم'}"])
    
    info_table = Table(info_data, colWidths=[50*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    # Transactions table
    if history:
        table_data = [["#", "التاريخ", "النوع", "المبلغ", "الحساب الآخر"]]
        total = 0
        for i, trans in enumerate(history, 1):
            type_ar = {'deposit': 'إيداع', 'withdraw': 'سحب', 'transfer': 'تحويل', 'interest': 'فائدة'}.get(trans[0], trans[0])
            amount_converted = convert_currency(trans[1], 'SYP', currency)
            if trans[0] in ['deposit', 'interest']:
                amount_str = f"+{amount_converted:,.2f}"
                total += amount_converted
            else:
                amount_str = f"-{amount_converted:,.2f}"
                total -= amount_converted
            table_data.append([str(i), trans[3][:16], type_ar, amount_str, trans[2] if trans[2] else "-"])
        
        table_data.append(["", "", "", "", ""])
        table_data.append(["", "", "", f"<b>الإجمالي: {total:,.2f} {currency}</b>", ""])
        
        table = Table(table_data, colWidths=[10*mm, 35*mm, 25*mm, 35*mm, 35*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('BACKGROUND', (0, -2), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("لا توجد عمليات مسجلة في هذه الفترة", normal_style))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<hr/>", normal_style))
    elements.append(Paragraph("<i>هذا كشف حساب تلقائي. يرجى مراجعة البنك لأي استفسار.</i>", normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, 
                     download_name=f"statement_{account_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                     mimetype='application/pdf')

# ==================== SECURE API ROUTES ====================
def validate_api_request(require_ownership=False, account_param='account_number', 
                         from_account_param=None, to_account_param=None):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized', 'code': 401}), 401
    
    role = session.get('role')
    username = session.get('username')
    
    can_proceed, blocked_minutes = check_failed_attempts(session['user_id'])
    if not can_proceed:
        return jsonify({'error': f'Too many failed attempts. Try again in {blocked_minutes} minutes.', 'code': 429}), 429
    
    if request.method in ['POST', 'PUT', 'DELETE']:
        token = request.headers.get('X-CSRF-Token') or request.json.get('_csrf_token')
        if not validate_csrf_token(token):
            app.logger.warning(f"CSRF token mismatch for user: {username}")
            return jsonify({'error': 'Invalid CSRF token', 'code': 403}), 403
    
    client_ip = request.remote_addr
    if not rate_limit(f'api_{session["user_id"]}_{client_ip}', limit=30, window=60):
        return jsonify({'error': 'Rate limit exceeded', 'code': 429}), 429
    
    data = request.get_json() if request.get_json() else {}
    
    if role == 'admin':
        return None
    
    if role == 'teller':
        if from_account_param and data.get(from_account_param):
            app.logger.warning(f"UNAUTHORIZED: Teller {username} attempted transfer")
            record_failed_attempt(session['user_id'])
            return jsonify({'error': 'Tellers cannot perform transfers.', 'code': 403}), 403
        
        if account_param and data.get(account_param):
            return None
        if require_ownership:
            return None
        return None
    
    if require_ownership:
        account_to_check = None
        if account_param and data.get(account_param):
            account_to_check = data.get(account_param)
        elif from_account_param and data.get(from_account_param):
            account_to_check = data.get(from_account_param)
        
        if account_to_check:
            if not user_owns_account(username, account_to_check):
                app.logger.warning(f"UNAUTHORIZED: {username} tried to access {account_to_check}")
                record_failed_attempt(session['user_id'])
                return jsonify({'error': 'Unauthorized: You do not own this account', 'code': 403}), 403
        
        if from_account_param and data.get(from_account_param):
            from_acc = data.get(from_account_param)
            if not user_owns_account(username, from_acc):
                app.logger.warning(f"UNAUTHORIZED: {username} tried to transfer from {from_acc}")
                record_failed_attempt(session['user_id'])
                return jsonify({'error': 'Unauthorized: You can only transfer from your own accounts', 'code': 403}), 403
    
    return None

def record_success(user_id):
    reset_failed_attempts(user_id)

# ==================== API ROUTES ====================
@app.route('/api/balance', methods=['POST'])
@log_activity
def api_balance():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    currency = data.get('currency', 'SYP')
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    balance_syp = db.get_balance(account_number)
    if balance_syp is not None:
        converted_balance = convert_currency(balance_syp, 'SYP', currency)
        record_success(session['user_id'])
        return jsonify({
            'success': True, 
            'balance': converted_balance,
            'balance_syp': balance_syp,
            'currency': currency,
            'currency_symbol': CURRENCY_SYMBOLS.get(currency, ''),
            'currency_name': CURRENCY_NAMES.get(currency, '')
        })
    return jsonify({'success': False, 'error': 'Account not found'})

@app.route('/api/deposit', methods=['POST'])
@log_activity
def api_deposit():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    amount = data.get('amount', 0)
    currency = data.get('currency', 'SYP')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount format'})
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    amount_syp = convert_currency(amount, currency, 'SYP')
    
    if not validate_amount(amount_syp):
        return jsonify({'success': False, 'error': 'Invalid amount'})
    
    balance = db.get_balance(account_number)
    if balance is None:
        return jsonify({'success': False, 'error': 'Account not found'})
    
    new_balance_syp = db.deposit(account_number, amount_syp)
    app.logger.info(f"DEPOSIT: {amount} {currency} ({amount_syp} SYP) to {account_number} by {session.get('username')}")
    record_success(session['user_id'])
    
    new_balance_converted = convert_currency(new_balance_syp, 'SYP', currency)
    
    return jsonify({
        'success': True, 
        'balance': new_balance_converted,
        'balance_syp': new_balance_syp,
        'message': f'Deposit successful: {amount} {currency}',
        'converted_amount': amount_syp,
        'currency': currency
    })

@app.route('/api/withdraw', methods=['POST'])
@log_activity
def api_withdraw():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    amount = data.get('amount', 0)
    currency = data.get('currency', 'SYP')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount format'})
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Amount must be greater than 0'})
    
    amount_syp = convert_currency(amount, currency, 'SYP')
    
    balance_syp = db.get_balance(account_number)
    if balance_syp is None:
        return jsonify({'success': False, 'error': 'Account not found'})
    
    if balance_syp < amount_syp:
        return jsonify({'success': False, 'error': f'Insufficient balance. Your balance: {balance_syp:,.2f} SYP', 'balance': balance_syp})
    
    try:
        limit, withdrawn, remaining = db.get_daily_info(account_number)
        if withdrawn + amount_syp > limit:
            return jsonify({'success': False, 'error': f'Daily limit exceeded! Limit: {limit:,.2f} SYP, Remaining: {remaining:,.2f} SYP'})
    except Exception as e:
        app.logger.error(f"Daily limit check error: {e}")
    
    success, new_balance_syp = db.withdraw(account_number, amount_syp)
    if success:
        app.logger.info(f"WITHDRAW: {amount} {currency} ({amount_syp} SYP) from {account_number} by {session.get('username')}")
        record_success(session['user_id'])
        new_balance_converted = convert_currency(new_balance_syp, 'SYP', currency)
        return jsonify({
            'success': True, 
            'balance': new_balance_converted,
            'balance_syp': new_balance_syp,
            'message': f'Withdrawal successful: {amount} {currency}',
            'converted_amount': amount_syp,
            'currency': currency
        })
    else:
        record_failed_attempt(session['user_id'])
        return jsonify({'success': False, 'error': 'Withdrawal failed.', 'balance': balance_syp})

@app.route('/api/transfer', methods=['POST'])
@log_activity
def api_transfer():
    validation = validate_api_request(require_ownership=True, from_account_param='from_account')
    if validation:
        return validation
    
    data = request.get_json()
    from_account = sanitize_input(data.get('from_account', ''))
    to_account = sanitize_input(data.get('to_account', ''))
    amount = data.get('amount', 0)
    currency = data.get('currency', 'SYP')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount format'})
    
    if not validate_account_number(from_account) or not validate_account_number(to_account):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    if from_account == to_account:
        return jsonify({'success': False, 'error': 'Cannot transfer to the same account'})
    
    amount_syp = convert_currency(amount, currency, 'SYP')
    
    if not validate_amount(amount_syp):
        return jsonify({'success': False, 'error': 'Invalid amount'})
    
    to_balance = db.get_balance(to_account)
    if to_balance is None:
        return jsonify({'success': False, 'error': 'Destination account not found'})
    
    from_balance = db.get_balance(from_account)
    if from_balance < amount_syp:
        return jsonify({'success': False, 'error': f'Insufficient balance. Your balance: {from_balance:,.2f} SYP'})
    
    if amount_syp > 15000000 and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Large transfers require admin approval'})
    
    success, new_balance_syp = db.transfer(from_account, to_account, amount_syp)
    if success:
        app.logger.info(f"TRANSFER: {amount} {currency} ({amount_syp} SYP) from {from_account} to {to_account} by {session.get('username')}")
        record_success(session['user_id'])
        new_balance_converted = convert_currency(new_balance_syp, 'SYP', currency)
        return jsonify({
            'success': True, 
            'balance': new_balance_converted,
            'balance_syp': new_balance_syp,
            'message': 'Transfer successful',
            'currency': currency
        })
    
    record_failed_attempt(session['user_id'])
    return jsonify({'success': False, 'error': 'Transfer failed'})

@app.route('/api/history', methods=['POST'])
@log_activity
def api_history():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    currency = data.get('currency', 'SYP')
    
    history = db.get_transaction_history(account_number)
    transactions = []
    for trans in history:
        amount_converted = convert_currency(trans[1], 'SYP', currency)
        transactions.append({
            'type': trans[0],
            'amount': amount_converted,
            'amount_syp': trans[1],
            'target': trans[2] if trans[2] else '-',
            'date': trans[3],
            'currency': currency
        })
    record_success(session['user_id'])
    return jsonify({'success': True, 'history': transactions})

@app.route('/api/daily_limit', methods=['POST'])
@log_activity
def api_daily_limit():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    currency = data.get('currency', 'SYP')
    
    limit_syp, withdrawn_syp, remaining_syp = db.get_daily_info(account_number)
    
    limit = convert_currency(limit_syp, 'SYP', currency)
    withdrawn = convert_currency(withdrawn_syp, 'SYP', currency)
    remaining = convert_currency(remaining_syp, 'SYP', currency)
    
    return jsonify({
        'success': True, 
        'limit': limit,
        'limit_syp': limit_syp,
        'withdrawn': withdrawn,
        'withdrawn_syp': withdrawn_syp,
        'remaining': remaining,
        'remaining_syp': remaining_syp,
        'currency': currency
    })

@app.route('/api/convert_currency', methods=['POST'])
def api_convert_currency():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    amount = data.get('amount', 0)
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount format'})
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Invalid amount'})
    
    if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
        return jsonify({'success': False, 'error': 'Unsupported currency'})
    
    converted = convert_currency(amount, from_currency, to_currency)
    rate = EXCHANGE_RATES[from_currency] / EXCHANGE_RATES[to_currency]
    
    return jsonify({
        'success': True, 
        'converted': round(converted, 2), 
        'rate': round(rate, 4),
        'from_currency': from_currency,
        'to_currency': to_currency,
        'amount': amount
    })

@app.route('/api/exchange_rates', methods=['GET'])
def api_exchange_rates():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'success': True,
        'rates': EXCHANGE_RATES,
        'symbols': CURRENCY_SYMBOLS,
        'names': CURRENCY_NAMES,
        'base_currency': 'SYP'
    })

@app.route('/api/my_accounts', methods=['GET'])
@login_required
def api_my_accounts():
    role = session.get('role')
    if role == 'admin':
        accounts = get_all_accounts()
        return jsonify({'success': True, 'accounts': accounts})
    elif role == 'teller':
        accounts = get_all_accounts()
        return jsonify({'success': True, 'accounts': accounts})
    else:
        accounts = get_user_accounts(session.get('username'))
        return jsonify({'success': True, 'accounts': accounts})

# ==================== INTEREST API ====================
@app.route('/api/interest_info', methods=['POST'])
@login_required
def api_interest_info():
    validation = validate_api_request(require_ownership=True, account_param='account_number')
    if validation:
        return validation
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    currency = data.get('currency', 'SYP')
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    info = db.get_interest_info(account_number)
    if info:
        balance_converted = convert_currency(info['balance'], 'SYP', currency)
        interest_converted = convert_currency(info['interest_earned'], 'SYP', currency)
        potential_converted = convert_currency(info['potential_interest'], 'SYP', currency)
        
        return jsonify({
            'success': True,
            'balance': balance_converted,
            'balance_syp': info['balance'],
            'interest_earned': interest_converted,
            'interest_earned_syp': info['interest_earned'],
            'potential_interest': potential_converted,
            'potential_interest_syp': info['potential_interest'],
            'days_without_withdrawal': info['days_without_withdrawal'],
            'days_to_next_interest': info['days_to_next_interest'],
            'last_withdrawal_date': info['last_withdrawal_date'],
            'interest_rate': info['interest_rate'],
            'currency': currency,
            'currency_symbol': CURRENCY_SYMBOLS.get(currency, ''),
            'currency_name': CURRENCY_NAMES.get(currency, '')
        })
    return jsonify({'success': False, 'error': 'Account not found'})

# ==================== ADMIN API ROUTES (Accessible by Admin and Teller) ====================
@app.route('/api/admin/accounts', methods=['GET'])
@log_activity
def api_get_all_accounts():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session.get('role') not in ['admin', 'teller']:
        return jsonify({'error': 'Forbidden'}), 403
    
    accounts = db.get_all_accounts_with_users()
    accounts_list = []
    for acc in accounts:
        accounts_list.append({
            'account_number': acc[0],
            'username': acc[1],
            'role': acc[2],
            'balance': acc[3],
            'balance_syp': acc[3],
            'created_at': acc[5] if len(acc) > 5 else ''
        })
    return jsonify({'success': True, 'accounts': accounts_list})

@app.route('/api/admin/users', methods=['GET'])
@log_activity
def api_get_all_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session.get('role') not in ['admin', 'teller']:
        return jsonify({'error': 'Forbidden'}), 403
    
    users = db.get_all_users()
    users_list = []
    for u in users:
        users_list.append({
            'id': u[0],
            'username': u[1],
            'role': u[2],
            'created_at': u[3]
        })
    return jsonify({'success': True, 'users': users_list})

@app.route('/api/admin/report', methods=['GET'])
@log_activity
def api_admin_report():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if session.get('role') not in ['admin', 'teller']:
        return jsonify({'error': 'Forbidden'}), 403
    
    total_balance_syp = db.get_total_balance()
    accounts_count = db.get_accounts_count()
    users_count = db.get_total_users_count()
    stats = db.get_transaction_stats()
    active_accounts = db.get_most_active_accounts()
    
    # Convert stats (Row objects) to serializable format
    stats_list = []
    for stat in stats:
        stats_list.append({
            'type': stat[0],
            'count': stat[1],
            'total': stat[2]
        })
    
    # Convert active_accounts (Row objects) to serializable format
    active_list = []
    for acc in active_accounts:
        active_list.append({
            'account_number': acc[0],
            'count': acc[1]
        })
    
    return jsonify({
        'success': True,
        'total_balance_syp': total_balance_syp,
        'total_balance': total_balance_syp,
        'accounts_count': accounts_count,
        'users_count': users_count,
        'stats': stats_list,
        'active_accounts': active_list
    })

@app.route('/api/admin/backup', methods=['POST'])
@log_activity
def api_backup():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    backup_file = db.backup_database()
    app.logger.info(f"BACKUP: Created {backup_file} by {session.get('username')}")
    return jsonify({'success': True, 'message': f'Backup created: {backup_file}'})

@app.route('/api/admin/set_daily_limit', methods=['POST'])
@log_activity
def api_set_daily_limit():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    limit = data.get('limit', 1000000)
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Invalid account number format'})
    
    try:
        limit = float(limit)
        if limit < 100000 or limit > 100000000:
            return jsonify({'success': False, 'error': 'Daily limit must be between 100,000 and 100,000,000 SYP'})
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid limit value'})
    
    db.set_daily_limit(account_number, limit)
    return jsonify({'success': True, 'message': f'Daily limit set to {limit:,.0f} SYP'})

@app.route('/api/admin/create_user', methods=['POST'])
@log_activity
def api_create_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    role = sanitize_input(data.get('role', 'customer'))
    
    if not validate_username(username):
        return jsonify({'success': False, 'error': 'Username must be 3-20 characters'})
    
    if not validate_password(password):
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
    
    if role not in ['customer', 'teller', 'admin']:
        return jsonify({'success': False, 'error': 'Invalid role'})
    
    success, result = db.create_user(username, password, role)
    if success:
        app.logger.info(f"CREATE_USER: {username} as {role} by {session.get('username')}")
        return jsonify({'success': True, 'message': f'User {username} created successfully'})
    return jsonify({'success': False, 'error': result})

@app.route('/api/admin/delete_user', methods=['POST'])
@log_activity
def api_delete_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    username = sanitize_input(data.get('username', ''))
    
    if username == 'admin':
        return jsonify({'success': False, 'error': 'Cannot delete main admin user'})
    
    if username == session.get('username'):
        return jsonify({'success': False, 'error': 'Cannot delete your own account'})
    
    success, message = db.delete_user(username)
    if success:
        app.logger.info(f"DELETE_USER: {username} by {session.get('username')}")
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message})

@app.route('/api/admin/delete_account', methods=['POST'])
@log_activity
def api_delete_account():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    account_number = sanitize_input(data.get('account_number', ''))
    
    success, message = db.delete_account(account_number)
    if success:
        app.logger.info(f"DELETE_ACCOUNT: {account_number} by {session.get('username')}")
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message})

@app.route('/api/admin/create_account', methods=['POST'])
@log_activity
def api_create_account():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    username = sanitize_input(data.get('username', ''))
    account_number = sanitize_input(data.get('account_number', ''))
    initial_balance = data.get('initial_balance', 0)
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Account number must be ACC001, ACC002, etc.'})
    
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    user_id = user[0]
    success, result = db.create_account(user_id, account_number, initial_balance)
    if success:
        app.logger.info(f"CREATE_ACCOUNT: {account_number} for {username} by {session.get('username')}")
        return jsonify({'success': True, 'message': f'Account {account_number} created successfully'})
    return jsonify({'success': False, 'error': result})

# ==================== TELLER API ROUTES ====================
@app.route('/api/teller/create_user', methods=['POST'])
@log_activity
def api_teller_create_user():
    if 'user_id' not in session or session.get('role') not in ['admin', 'teller']:
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    username = sanitize_input(data.get('username', ''))
    password = data.get('password', '')
    role = sanitize_input(data.get('role', 'customer'))
    
    if not validate_username(username):
        return jsonify({'success': False, 'error': 'Username must be 3-20 characters'})
    
    if not validate_password(password):
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
    
    if role not in ['customer', 'teller']:
        role = 'customer'
    
    success, result = db.create_user(username, password, role)
    if success:
        app.logger.info(f"TELLER_CREATE_USER: {username} as {role} by {session.get('username')}")
        return jsonify({'success': True, 'message': f'User {username} created successfully'})
    return jsonify({'success': False, 'error': result})

@app.route('/api/teller/create_account', methods=['POST'])
@log_activity
def api_teller_create_account():
    if 'user_id' not in session or session.get('role') not in ['admin', 'teller']:
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json()
    username = sanitize_input(data.get('username', ''))
    account_number = sanitize_input(data.get('account_number', ''))
    initial_balance = data.get('initial_balance', 0)
    
    if not validate_account_number(account_number):
        return jsonify({'success': False, 'error': 'Account number must be ACC001, ACC002, etc.'})
    
    user = db.get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    user_id = user[0]
    success, result = db.create_account(user_id, account_number, initial_balance)
    if success:
        app.logger.info(f"TELLER_CREATE_ACCOUNT: {account_number} for {username} by {session.get('username')}")
        return jsonify({'success': True, 'message': f'Account {account_number} created successfully'})
    return jsonify({'success': False, 'error': result})

# ==================== ERROR HANDLERS ====================
@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Forbidden access', 'code': 403}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found', 'code': 404}), 404

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({'error': 'Too many requests. Please try again later.', 'code': 429}), 429

# ==================== RUN APP ====================
if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)

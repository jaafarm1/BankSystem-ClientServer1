# ------------------------------------------------------------
# database.py - Database with SYP as base currency and Interest System
# ------------------------------------------------------------
import sqlite3
from datetime import datetime, date, timedelta
import threading
import hashlib
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

class Database:
    
    def __init__(self, db_name="bank.db"):
        self.db_name = db_name
        self.local = threading.local()
        self.create_tables()
    
    def get_connection(self):
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_name)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection
    
    def get_cursor(self):
        return self.get_connection().cursor()
    
    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table with extra fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                national_id TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Accounts table with interest fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                balance REAL DEFAULT 0,
                daily_limit REAL DEFAULT 1000000,
                last_withdrawal_date TEXT DEFAULT NULL,
                last_interest_date TEXT DEFAULT NULL,
                interest_accrued REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT,
                type TEXT,
                amount REAL,
                target_account TEXT,
                timestamp TEXT,
                FOREIGN KEY (account_number) REFERENCES accounts (account_number)
            )
        ''')
        
        # Ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Complaints table
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
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date(timestamp))")
        
        # Insert demo users
        users = [
            ("admin", hash_password("admin123"), "admin"),
            ("teller", hash_password("teller123"), "teller"),
            ("ahmed", hash_password("123456"), "customer")
        ]
        
        for username, password, role in users:
            try:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                               (username, password, role))
                logger.info(f"Created user: {username}")
            except sqlite3.IntegrityError:
                pass
        
        # Insert demo account for ahmed
        try:
            cursor.execute("SELECT user_id FROM users WHERE username='ahmed'")
            user = cursor.fetchone()
            if user:
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT OR IGNORE INTO accounts (account_number, user_id, balance, last_withdrawal_date, last_interest_date) VALUES (?, ?, ?, ?, ?)",
                               ("ACC001", user[0], 5000000, today, today))
                logger.info("Created demo account ACC001 for ahmed")
        except Exception as e:
            logger.error(f"Error creating demo account: {e}")
        
        conn.commit()
        conn.close()
    
    def authenticate(self, username, password):
        cursor = self.get_cursor()
        cursor.execute("SELECT user_id, role, password FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        
        if result and verify_password(password, result[2]):
            return (result[0], result[1])
        return None
    
    def get_balance(self, account_number):
        cursor = self.get_cursor()
        cursor.execute("SELECT balance FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def deposit(self, account_number, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", 
                       (amount, account_number))
        self.log_transaction(account_number, "deposit", amount)
        conn.commit()
        logger.info(f"Deposited {amount} SYP to {account_number}")
        return self.get_balance(account_number)
    
    def withdraw(self, account_number, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            balance = self.get_balance(account_number)
            if balance is None:
                return False, 0
            
            if balance >= amount:
                cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", 
                               (amount, account_number))
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("UPDATE accounts SET last_withdrawal_date = ? WHERE account_number=?", 
                               (today, account_number))
                cursor.execute("UPDATE accounts SET interest_accrued = 0 WHERE account_number=?", 
                               (account_number,))
                self.log_transaction(account_number, "withdraw", amount)
                conn.commit()
                new_balance = self.get_balance(account_number)
                logger.info(f"Withdrew {amount} SYP from {account_number}")
                return True, new_balance
            else:
                logger.warning(f"Insufficient balance for {account_number}: {balance} < {amount}")
                return False, balance
        except Exception as e:
            logger.error(f"Withdraw error: {e}")
            conn.rollback()
            return False, 0
    
    def transfer(self, from_account, to_account, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            from_balance = self.get_balance(from_account)
            if from_balance is None or from_balance < amount:
                return False, from_balance if from_balance else 0
            
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?", 
                           (amount, from_account))
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?", 
                           (amount, to_account))
            
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("UPDATE accounts SET last_withdrawal_date = ? WHERE account_number=?", 
                           (today, from_account))
            cursor.execute("UPDATE accounts SET interest_accrued = 0 WHERE account_number=?", 
                           (from_account,))
            
            self.log_transaction(from_account, "transfer", amount, to_account)
            conn.commit()
            logger.info(f"Transferred {amount} SYP from {from_account} to {to_account}")
            return True, self.get_balance(from_account)
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            conn.rollback()
            return False, 0
    
    def log_transaction(self, account_number, type, amount, target_account=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO transactions (account_number, type, amount, target_account, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (account_number, type, amount, target_account, timestamp))
        conn.commit()
    
    def get_transaction_history(self, account_number, limit=50):
        cursor = self.get_cursor()
        cursor.execute('''
            SELECT type, amount, target_account, timestamp 
            FROM transactions 
            WHERE account_number=?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (account_number, limit))
        return cursor.fetchall()
    
    def create_user(self, username, password, role):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            hashed_password = hash_password(password)
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (username, hashed_password, role))
            conn.commit()
            logger.info(f"Created user: {username} with role {role}")
            return True, cursor.lastrowid
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, str(e)
    
    def create_account(self, user_id, account_number, initial_balance=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO accounts (account_number, user_id, balance, last_withdrawal_date, last_interest_date) VALUES (?, ?, ?, ?, ?)",
                           (account_number, user_id, initial_balance, today, today))
            conn.commit()
            logger.info(f"Created account {account_number} for user_id {user_id}")
            return True, "Account created successfully"
        except sqlite3.IntegrityError:
            return False, "Account number already exists"
        except Exception as e:
            return False, str(e)
    
    def get_all_users(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT user_id, username, role, created_at FROM users")
        return cursor.fetchall()
    
    def get_user_by_username(self, username):
        cursor = self.get_cursor()
        cursor.execute("SELECT user_id, username, role FROM users WHERE username=?", (username,))
        return cursor.fetchone()
    
    def get_all_accounts_with_users(self):
        cursor = self.get_cursor()
        cursor.execute('''
            SELECT accounts.account_number, users.username, users.role, accounts.balance, 
                   accounts.account_id, accounts.created_at, accounts.last_withdrawal_date, accounts.interest_accrued
            FROM accounts
            JOIN users ON accounts.user_id = users.user_id
            ORDER BY accounts.account_id
        ''')
        return cursor.fetchall()
    
    def get_total_balance(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT SUM(balance) FROM accounts")
        result = cursor.fetchone()
        return result[0] if result[0] else 0
    
    def get_accounts_count(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        return cursor.fetchone()[0]
    
    def get_total_users_count(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    
    def get_transaction_stats(self):
        cursor = self.get_cursor()
        cursor.execute('''
            SELECT type, COUNT(*) as count, SUM(amount) as total
            FROM transactions
            GROUP BY type
        ''')
        return cursor.fetchall()
    
    def get_most_active_accounts(self, limit=5):
        cursor = self.get_cursor()
        cursor.execute('''
            SELECT account_number, COUNT(*) as count
            FROM transactions
            GROUP BY account_number
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_daily_summary(self):
        cursor = self.get_cursor()
        today = date.today().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT type, SUM(amount) as total
            FROM transactions
            WHERE date(timestamp)=?
            GROUP BY type
        ''', (today,))
        return cursor.fetchall()
    
    def delete_account(self, account_number):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM transactions WHERE account_number=?", (account_number,))
            cursor.execute("DELETE FROM accounts WHERE account_number=?", (account_number,))
            conn.commit()
            logger.info(f"Deleted account {account_number}")
            return True, "Account deleted successfully"
        except Exception as e:
            return False, str(e)
    
    def delete_user(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM transactions 
                WHERE account_number IN (
                    SELECT account_number FROM accounts 
                    WHERE user_id=(SELECT user_id FROM users WHERE username=?)
                )
            ''', (username,))
            cursor.execute("DELETE FROM accounts WHERE user_id=(SELECT user_id FROM users WHERE username=?)", (username,))
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
            logger.info(f"Deleted user {username} and all accounts")
            return True, f"User {username} and all their accounts deleted successfully"
        except Exception as e:
            return False, str(e)
    
    def backup_database(self):
        backup_name = f"bank_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(self.db_name, backup_name)
        logger.info(f"Created backup: {backup_name}")
        return backup_name
    
    def update_password(self, username, old_password, new_password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        if not result or not verify_password(old_password, result[0]):
            return False, "Old password is incorrect"
        new_hashed = hash_password(new_password)
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_hashed, username))
        conn.commit()
        logger.info(f"Password updated for {username}")
        return True, "Password changed successfully"
    
    def get_daily_withdrawals(self, account_number):
        cursor = self.get_cursor()
        today = date.today().strftime("%Y-%m-%d")
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE account_number=? AND type='withdraw' AND date(timestamp)=?
        ''', (account_number, today))
        result = cursor.fetchone()
        return result[0] if result[0] else 0
    
    def set_daily_limit(self, account_number, limit):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET daily_limit=? WHERE account_number=?", (limit, account_number))
        conn.commit()
        logger.info(f"Set daily limit for {account_number} to {limit}")
        return True
    
    def get_daily_limit(self, account_number):
        cursor = self.get_cursor()
        cursor.execute("SELECT daily_limit FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        return result[0] if result else 1000000
    
    def get_daily_info(self, account_number):
        limit = self.get_daily_limit(account_number)
        withdrawn = self.get_daily_withdrawals(account_number)
        remaining = max(0, limit - withdrawn)
        return limit, withdrawn, remaining
    
    # ==================== INTEREST FUNCTIONS ====================
    def calculate_interest(self, account_number):
        """Calculate interest for an account based on last withdrawal date"""
        cursor = self.get_cursor()
        
        cursor.execute("SELECT balance, last_withdrawal_date, interest_accrued FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        if not result:
            return 0, 0
        
        balance = result[0]
        last_withdrawal = result[1]
        current_interest = result[2] if result[2] else 0
        
        if last_withdrawal is None or balance <= 0:
            return 0, current_interest
        
        today = datetime.now().date()
        last_withdrawal_date = datetime.strptime(last_withdrawal, "%Y-%m-%d").date()
        days_since_withdrawal = (today - last_withdrawal_date).days
        
        # 9% annual interest rate
        annual_rate = 0.09
        daily_rate = annual_rate / 365
        interest_rate = daily_rate * days_since_withdrawal
        
        # Cap at 9% maximum per year
        max_interest = balance * annual_rate
        calculated_interest = balance * interest_rate
        new_interest = min(calculated_interest, max_interest)
        
        return round(new_interest, 2), current_interest
    
    def apply_interest(self, account_number):
        """Apply calculated interest to account balance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            new_interest, current_interest = self.calculate_interest(account_number)
            
            # Apply interest if it's positive and changed significantly
            if new_interest > 0:
                cursor.execute("UPDATE accounts SET balance = balance + ?, interest_accrued = ? WHERE account_number=?", 
                               (new_interest, new_interest, account_number))
                cursor.execute("UPDATE accounts SET last_interest_date = ? WHERE account_number=?", 
                               (datetime.now().strftime("%Y-%m-%d"), account_number))
                self.log_transaction(account_number, "interest", new_interest)
                conn.commit()
                logger.info(f"Applied {new_interest} SYP interest to {account_number}")
                return True, new_interest
        except Exception as e:
            logger.error(f"Apply interest error for {account_number}: {e}")
            conn.rollback()
            return False, 0
        
        return False, 0
    
    def apply_interest_to_all_accounts(self):
        """Apply interest to all eligible accounts"""
        cursor = self.get_cursor()
        cursor.execute("SELECT account_number FROM accounts WHERE balance > 0")
        accounts = cursor.fetchall()
        
        results = []
        for acc in accounts:
            success, interest = self.apply_interest(acc[0])
            if success:
                results.append((acc[0], interest))
        
        logger.info(f"Applied interest to {len(results)} accounts")
        return results
    
    def get_interest_info(self, account_number):
        """Get interest information for an account"""
        cursor = self.get_cursor()
        cursor.execute("SELECT balance, last_withdrawal_date, interest_accrued FROM accounts WHERE account_number=?", (account_number,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        balance = result[0]
        last_withdrawal = result[1]
        interest_accrued = result[2] if result[2] else 0
        
        if last_withdrawal and balance > 0:
            today = datetime.now().date()
            last_withdrawal_date = datetime.strptime(last_withdrawal, "%Y-%m-%d").date()
            days_without_withdrawal = (today - last_withdrawal_date).days
        else:
            days_without_withdrawal = 0
        
        # Calculate potential interest
        annual_rate = 0.09
        daily_rate = annual_rate / 365
        potential_interest = balance * daily_rate * days_without_withdrawal
        potential_interest = min(potential_interest, balance * annual_rate)
        
        if last_withdrawal and balance > 0:
            last_date = datetime.strptime(last_withdrawal, "%Y-%m-%d").date()
            next_interest_date = last_date + timedelta(days=30)
            days_to_next_interest = max(0, (next_interest_date - datetime.now().date()).days)
        else:
            days_to_next_interest = 0
        
        return {
            'balance': balance,
            'interest_earned': round(interest_accrued, 2),
            'potential_interest': round(potential_interest, 2),
            'days_without_withdrawal': days_without_withdrawal,
            'days_to_next_interest': days_to_next_interest,
            'last_withdrawal_date': last_withdrawal,
            'interest_rate': 9.0
        }
    
    # ==================== USER EXTRA INFO ====================
    def update_user_info(self, username, national_id=None, email=None, phone=None, address=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if national_id is not None:
            updates.append("national_id = ?")
            params.append(national_id)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if address is not None:
            updates.append("address = ?")
            params.append(address)
        
        if updates:
            params.append(username)
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = ?"
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"Updated user info for {username}")
        
        return True
    
    def get_user_info(self, username):
        cursor = self.get_cursor()
        cursor.execute("SELECT national_id, email, phone, address FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        if result:
            return {
                'national_id': result[0] or '',
                'email': result[1] or '',
                'phone': result[2] or '',
                'address': result[3] or ''
            }
        return None
    
    def close(self):
        if hasattr(self.local, 'connection'):
            self.local.connection.close()
            logger.info("Database connection closed")

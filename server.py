# ------------------------------------------------------------
# استيراد المكتبات المطلوبة
# ------------------------------------------------------------
import socket
import threading
import json
import logging
from datetime import datetime
from database import Database

# ------------------------------------------------------------
# إعدادات تسجيل العمليات
# ------------------------------------------------------------
logging.basicConfig(
    filename='bank.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# ------------------------------------------------------------
# أسعار الصرف (لتحويل العملات)
# ------------------------------------------------------------
EXCHANGE_RATES = {
    'USD': 1.0,      # دولار أمريكي
    'JOD': 0.71,     # دينار أردني
    'SYP': 15000.0,  # ليرة سورية
    'EUR': 0.92,     # يورو
    'SAR': 3.75      # ريال سعودي
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

# ------------------------------------------------------------
# كلاس السيرفر الرئيسي
# ------------------------------------------------------------
class BankServer:
    
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.exchange_rates = EXCHANGE_RATES
        self.currency_symbols = CURRENCY_SYMBOLS
        self.currency_names = CURRENCY_NAMES
    
    def start(self):
        """تشغيل السيرفر"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVER] بنك التوفير يعمل على {self.host}:{self.port}")
        print("[SERVER] في انتظار الاتصالات...")
        
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"[SERVER] تم الاتصال من {address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()
    
    def handle_client(self, client_socket):
        """معالجة عميل واحد"""
        db = Database()
        authenticated = False
        user_role = None
        current_username = None
        
        try:
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                request = json.loads(data)
                response = self.process_request(request, authenticated, user_role, current_username, db)
                
                client_socket.send(json.dumps(response).encode('utf-8'))
                
                if request.get('action') == 'login' and response.get('status') == 'success':
                    authenticated = True
                    user_role = response.get('role')
                    current_username = request.get('username')
                    
                elif request.get('action') == 'logout':
                    authenticated = False
                    user_role = None
                    current_username = None
                    break
                    
        except Exception as e:
            print(f"[ERROR] {e}")
            logging.error(f"Error in handle_client: {e}")
        finally:
            db.close()
            client_socket.close()
    
    def process_request(self, request, authenticated, user_role, current_username, db):
        """معالجة الطلبات"""
        action = request.get('action')
        
        # login
        if action == 'login':
            username = request.get('username')
            password = request.get('password')
            user = db.authenticate(username, password)
            if user:
                logging.info(f"Successful login: {username}")
                return {'status': 'success', 'message': 'تم تسجيل الدخول', 'role': user[1]}
            logging.warning(f"Failed login attempt: {username}")
            return {'status': 'error', 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}
        
        # التحقق من المصادقة
        if not authenticated:
            return {'status': 'error', 'message': 'يجب تسجيل الدخول أولاً'}
        
        # عرض الرصيد
        if action == 'balance':
            account_number = request.get('account_number')
            balance = db.get_balance(account_number)
            if balance is not None:
                return {'status': 'success', 'balance': balance}
            return {'status': 'error', 'message': 'رقم الحساب غير صحيح'}
        
        # إيداع
        elif action == 'deposit':
            account_number = request.get('account_number')
            amount = request.get('amount')
            if amount <= 0:
                return {'status': 'error', 'message': 'المبلغ يجب أن يكون أكبر من 0'}
            
            balance = db.get_balance(account_number)
            if balance is None:
                return {'status': 'error', 'message': 'رقم الحساب غير موجود'}
            
            new_balance = db.deposit(account_number, amount)
            logging.info(f"Deposit: {amount} to {account_number}, new balance: {new_balance}")
            return {'status': 'success', 'message': 'تم الإيداع بنجاح', 'balance': new_balance}
        
        # سحب مع التحقق من الحد اليومي
        elif action == 'withdraw':
            account_number = request.get('account_number')
            amount = request.get('amount')
            
            if amount <= 0:
                return {'status': 'error', 'message': 'المبلغ يجب أن يكون أكبر من 0'}
            
            limit, withdrawn, remaining = db.get_daily_info(account_number)
            if withdrawn + amount > limit:
                return {'status': 'error', 'message': f'تجاوزت حد السحب اليومي! الحد المتبقي: {remaining} دينار'}
            
            success, balance = db.withdraw(account_number, amount)
            if success:
                logging.info(f"Withdrawal: {amount} from {account_number}, new balance: {balance}")
                return {'status': 'success', 'message': 'تم السحب بنجاح', 'balance': balance}
            return {'status': 'error', 'message': 'الرصيد غير كاف', 'balance': balance}
        
        # تحويل مع التحقق من الحد اليومي
        elif action == 'transfer':
            from_account = request.get('from_account')
            to_account = request.get('to_account')
            amount = request.get('amount')
            
            limit, withdrawn, remaining = db.get_daily_info(from_account)
            if withdrawn + amount > limit:
                return {'status': 'error', 'message': f'تجاوزت حد السحب اليومي للتحويل! الحد المتبقي: {remaining} دينار'}
            
            success, balance = db.transfer(from_account, to_account, amount)
            if success:
                logging.info(f"Transfer: {amount} from {from_account} to {to_account}")
                return {'status': 'success', 'message': 'تم التحويل بنجاح', 'balance': balance}
            return {'status': 'error', 'message': 'الرصيد غير كاف أو الحساب غير صحيح', 'balance': balance}
        
        # سجل العمليات
        elif action == 'history':
            account_number = request.get('account_number')
            history = db.get_transaction_history(account_number)
            return {'status': 'success', 'history': history}
        
        # إنشاء مستخدم جديد
        elif action == 'create_user':
            if user_role not in ['admin', 'teller']:
                return {'status': 'error', 'message': 'ليس لديك صلاحية لفتح حساب جديد'}
            
            username = request.get('username')
            password = request.get('password')
            role = request.get('role', 'customer')
            
            if role not in ['admin', 'teller', 'customer']:
                return {'status': 'error', 'message': 'دور المستخدم غير صحيح'}
            
            success, result = db.create_user(username, password, role)
            if not success:
                return {'status': 'error', 'message': result}
            
            logging.info(f"New user created: {username} as {role}")
            return {'status': 'success', 'message': f'تم إنشاء المستخدم {username} بنجاح', 'user_id': result}
        
        # إنشاء حساب جديد
        elif action == 'create_account':
            if user_role not in ['admin', 'teller']:
                return {'status': 'error', 'message': 'ليس لديك صلاحية لفتح حساب جديد'}
            
            username = request.get('username')
            account_number = request.get('account_number')
            initial_balance = request.get('initial_balance', 0)
            
            if initial_balance < 0:
                return {'status': 'error', 'message': 'الرصيد الأولي لا يمكن أن يكون سالباً'}
            
            user = db.get_user_by_username(username)
            if not user:
                return {'status': 'error', 'message': f'المستخدم {username} غير موجود'}
            
            user_id = user[0]
            success, result = db.create_account(user_id, account_number, initial_balance)
            if not success:
                return {'status': 'error', 'message': result}
            
            logging.info(f"New account created: {account_number} for {username}")
            return {'status': 'success', 'message': f'تم فتح الحساب {account_number} للمستخدم {username} بنجاح', 'balance': initial_balance}
        
        # عرض جميع المستخدمين
        elif action == 'list_users':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لعرض المستخدمين'}
            
            users = db.get_all_users()
            return {'status': 'success', 'users': users}
        
        # تقرير المدير
        elif action == 'admin_report':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لعرض تقرير الحسابات'}
            
            accounts = db.get_all_accounts_with_users()
            total_balance = db.get_total_balance()
            accounts_count = db.get_accounts_count()
            users_count = db.get_total_users_count()
            stats = db.get_transaction_stats()
            active_accounts = db.get_most_active_accounts()
            daily_summary = db.get_daily_summary()
            
            return {
                'status': 'success',
                'accounts': accounts,
                'total_balance': total_balance,
                'accounts_count': accounts_count,
                'users_count': users_count,
                'stats': stats,
                'active_accounts': active_accounts,
                'daily_summary': daily_summary
            }
        
        # تقرير بالرسوم البيانية (جديد - حسب ملف المشروع)
        elif action == 'graph_report':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لعرض التقرير البياني'}
            
            accounts = db.get_all_accounts_with_users()
            users = db.get_all_users()
            stats = db.get_transaction_stats()
            active_accounts = db.get_most_active_accounts()
            daily_summary = db.get_daily_summary()
            
            return {
                'status': 'success',
                'accounts': accounts,
                'users': users,
                'stats': stats,
                'active_accounts': active_accounts,
                'daily_summary': daily_summary
            }
        
        # حذف حساب
        elif action == 'delete_account':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لحذف حساب'}
            
            account_number = request.get('account_number')
            success, message = db.delete_account(account_number)
            if success:
                logging.info(f"Account deleted: {account_number}")
                return {'status': 'success', 'message': message}
            return {'status': 'error', 'message': message}
        
        # حذف مستخدم
        elif action == 'delete_user':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لحذف مستخدم'}
            
            username = request.get('username')
            if username == 'admin':
                return {'status': 'error', 'message': 'لا يمكن حذف المدير الرئيسي'}
            
            success, message = db.delete_user(username)
            if success:
                logging.info(f"User deleted: {username}")
                return {'status': 'success', 'message': message}
            return {'status': 'error', 'message': message}
        
        # نسخ احتياطي
        elif action == 'backup':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لعمل نسخة احتياطية'}
            
            backup_file = db.backup_database()
            logging.info(f"Backup created: {backup_file}")
            return {'status': 'success', 'message': f'تم إنشاء النسخة الاحتياطية: {backup_file}'}
        
        # تغيير كلمة المرور
        elif action == 'change_password':
            username = request.get('username')
            old_password = request.get('old_password')
            new_password = request.get('new_password')
            
            success, message = db.update_password(username, old_password, new_password)
            if success:
                logging.info(f"Password changed for user: {username}")
            return {'status': 'success' if success else 'error', 'message': message}
        
        # تعيين حد سحب يومي
        elif action == 'set_daily_limit':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لتحديد حد السحب'}
            
            account_number = request.get('account_number')
            limit = request.get('limit')
            
            db.set_daily_limit(account_number, limit)
            logging.info(f"Daily limit set: {limit} for account {account_number}")
            return {'status': 'success', 'message': f'تم تحديد حد السحب اليومي بـ {limit} دينار'}
        
        # معلومات حد السحب اليومي
        elif action == 'get_daily_info':
            account_number = request.get('account_number')
            limit, withdrawn, remaining = db.get_daily_info(account_number)
            return {
                'status': 'success',
                'limit': limit,
                'withdrawn': withdrawn,
                'remaining': remaining
            }
        
        # تصدير تقرير Excel
        elif action == 'export_excel':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لتصدير التقرير'}
            
            accounts = db.get_all_accounts_with_users()
            return {'status': 'success', 'accounts': accounts}
        
        # تحويل العملات
        elif action == 'convert_currency':
            amount = request.get('amount')
            from_currency = request.get('from_currency')
            to_currency = request.get('to_currency')
            
            if amount <= 0:
                return {'status': 'error', 'message': 'المبلغ يجب أن يكون أكبر من 0'}
            
            if from_currency not in self.exchange_rates or to_currency not in self.exchange_rates:
                return {'status': 'error', 'message': 'عملة غير مدعومة'}
            
            amount_in_usd = amount / self.exchange_rates[from_currency]
            converted_amount = amount_in_usd * self.exchange_rates[to_currency]
            
            return {
                'status': 'success',
                'original_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'converted_amount': round(converted_amount, 2),
                'rate': round(self.exchange_rates[to_currency] / self.exchange_rates[from_currency], 4)
            }
        
        # عرض الرصيد بعملات مختلفة
        elif action == 'balance_multiple_currencies':
            account_number = request.get('account_number')
            balance = db.get_balance(account_number)
            
            if balance is None:
                return {'status': 'error', 'message': 'رقم الحساب غير صحيح'}
            
            balances = {}
            for currency, rate in self.exchange_rates.items():
                balances[currency] = round(balance * rate, 2)
            
            return {
                'status': 'success',
                'balance_jod': balance,
                'balances': balances,
                'symbols': self.currency_symbols,
                'names': self.currency_names
            }
        
        # تحديث أسعار الصرف (للمدير فقط)
        elif action == 'update_exchange_rates':
            if user_role != 'admin':
                return {'status': 'error', 'message': 'ليس لديك صلاحية لتحديث أسعار الصرف'}
            
            new_rates = request.get('rates')
            if new_rates:
                for currency, rate in new_rates.items():
                    if currency in self.exchange_rates:
                        self.exchange_rates[currency] = rate
                logging.info(f"Exchange rates updated by admin: {self.exchange_rates}")
                return {'status': 'success', 'message': 'تم تحديث أسعار الصرف بنجاح', 'rates': self.exchange_rates}
            
            return {'status': 'error', 'message': 'البيانات غير صحيحة'}
        
        # الحصول على أسعار الصرف الحالية
        elif action == 'get_exchange_rates':
            return {
                'status': 'success',
                'rates': self.exchange_rates,
                'symbols': self.currency_symbols,
                'names': self.currency_names
            }
        
        return {'status': 'error', 'message': 'عملية غير معروفة'}

# تشغيل السيرفر
if __name__ == '__main__':
    server = BankServer()
    server.start()

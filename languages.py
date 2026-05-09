# ------------------------------------------------------------
# languages.py - Multi-language support for Banking System
# ------------------------------------------------------------

# English translations
EN = {
    # Login screen
    'app_title': 'Banking System',
    'demo_accounts': 'Demo Accounts:',
    'admin': 'admin',
    'teller': 'teller',
    'customer': 'customer',
    'account_note': 'Customer account: ACC001',
    'tip_title': 'Tip: To create a new account:',
    'tip1': '1. Login as admin or teller',
    'tip2': '2. Select User Management -> Create New User',
    'tip3': '3. Then select Account Management -> Create New Account',
    'username': '👤 Username:',
    'password': '🔒 Password:',
    'login_success': 'Login successful!',
    'login_failed': 'Login failed!',
    'welcome': 'Welcome',
    'role': 'Role',
    'enter_account': '🏦 Enter your account number:',
    'logout': 'Logging out...',
    'logged_out': 'Logged out successfully',
    'press_enter': '⏎ Press Enter to continue...',
    'invalid_choice': '❌ Invalid option',
    'connecting_error': '❌ Cannot connect to server. Make sure server is running.',
    
    # NEW KEYS ADDED
    'choose_option': '🔹 Choose option (1-11): ',
    'choose_sub_option': 'Choose / اختر (1-3): ',
    
    # Customer menu
    'check_balance': '1. 💰 Check Balance',
    'deposit': '2. 📥 Deposit',
    'withdraw': '3. 📤 Withdraw',
    'transfer': '4. 🔄 Transfer',
    'history': '5. 📋 Transaction History',
    'multi_currency': '6. 💱 Balance in Multiple Currencies',
    'convert': '7. 💹 Currency Converter',
    'daily_limit': '8. 📊 Daily Limit Info',
    'change_pass': '9. 🔑 Change Password',
    'logout_btn': '10. 🚪 Logout',
    
    # Teller menu
    'check_balance_teller': '1. Check Balance',
    'deposit_teller': '2. Deposit to Account',
    'withdraw_teller': '3. Withdraw from Account',
    'transfer_teller': '4. Transfer Between Accounts',
    'history_teller': '5. Account Transaction History',
    'open_account': '6. Open New Account',
    'create_user': '7. Create New User',
    'multi_currency_teller': '8. Balance in Multiple Currencies',
    'convert_teller': '9. Currency Converter',
    'change_pass_teller': '10. Change Password',
    'logout_teller': '11. Logout',
    
    # Admin menu
    'account_mgmt': '1. Account Management (View - Create - Delete)',
    'user_mgmt': '2. User Management (View - Delete - Create)',
    'full_report': '3. Full Admin Report',
    'graph_report': '4. Graphical Report',
    'backup': '5. Database Backup',
    'set_limit': '6. Set Daily Withdrawal Limit',
    'update_rates': '7. Update Exchange Rates',
    'export_excel': '8. Export Excel Report',
    'currencies': '9. Currencies - Convert & View',
    'change_pass_admin': '10. Change Password',
    'logout_admin': '11. Logout',
    
    # Common messages
    'balance': '✅ Current Balance:',
    'jod': 'JOD',
    'amount': '💰 Amount:',
    'from_account': '🏦 From account:',
    'to_account': '🏦 To account:',
    'account_number': 'Account number:',
    'new_account': 'New account number:',
    'initial_balance': 'Initial balance:',
    'new_username': '👤 New username:',
    'new_password': '🔒 New password:',
    'confirm_password': '✅ Confirm password:',
    'role_type': '📌 Role type:',
    'customer_role': 'Customer',
    'teller_role': 'Teller',
    'admin_role': 'Admin',
    'success': '✅ Success',
    'error': '❌ Error',
    'daily_limit_info': '📊 Daily Limit Info',
    'daily_limit_text': 'Daily Limit:',
    'withdrawn_today': 'Withdrawn Today:',
    'remaining': 'Remaining:',
    'old_password': '🔒 Current password:',
    'new_password_text': '🔑 New password:',
    'confirm_new': '✅ Confirm new password:',
    'password_mismatch': '❌ Passwords do not match',
    'password_changed': '✅ Password changed successfully',
    
    # Account management
    'view_accounts': '1. View All Accounts',
    'create_new_account': '2. Create New Account',
    'delete_account': '3. Delete Account',
    'account_list': '📋 Account List:',
    'no_accounts': '📭 No accounts found',
    'user_must_exist': '📌 Note: User must exist first',
    'available_users': '👤 Available Users:',
    'enter_username': '👤 Username:',
    'enter_account_num': '🏦 Enter account number:',
    'account_created': '✅ Account created successfully',
    'account_deleted': '✅ Account deleted successfully',
    
    # User management
    'view_users': '1. View All Users',
    'delete_user': '2. Delete User',
    'create_new_user': '3. Create New User',
    'user_list': '👤 User List:',
    'no_users': '📭 No users found',
    'cannot_delete_admin': '❌ Cannot delete main admin',
    'user_created': '✅ User created successfully',
    'user_deleted': '✅ User deleted successfully',
    
    # Admin report
    'admin_report_title': '📊 Admin Report',
    'total_users': '👥 Total Users:',
    'total_accounts': '🏦 Total Accounts:',
    'total_balance': '💰 Total Balance:',
    'transaction_stats': '📈 Transaction Statistics:',
    'most_active': '⭐ Most Active Accounts:',
    'transactions': 'transactions',
    
    # Currency
    'balance_jod': '💰 Balance in JOD:',
    'other_currencies': '💱 Balance in other currencies:',
    'from_currency': 'From currency:',
    'to_currency': 'To currency:',
    'available_currencies': '💱 Available currencies: USD, JOD, SYP, EUR, SAR',
    'convert_result': '✅ Conversion result:',
    'exchange_rate': 'Exchange rate:',
    
    # Deposit/Withdraw/Transfer
    'deposit_success': '✅ Deposit successful',
    'withdraw_success': '✅ Withdrawal successful',
    'transfer_success': '✅ Transfer successful',
    'insufficient_balance': '❌ Insufficient balance',
    'invalid_amount': '❌ Invalid amount',
    'account_not_found': '❌ Account not found',
    
    # History
    'history_title': '📋 Transaction History (Last 10):',
    'type': 'Type',
    'date': 'Date',
    'target': 'Target',
    
    # Graph
    'preparing_graph': '📊 Preparing graph report...',
    'graph_error': '❌ Cannot generate graph',
    
    # Backup and Excel
    'creating_excel': '📎 Creating Excel report...',
    'excel_created': '✅ Excel report created successfully',
    'excel_failed': '❌ Export failed',
    'backup_created': '✅ Backup created successfully',
    
    # Exchange rates
    'current_rates': '💱 Current Exchange Rates:',
    'enter_new_rates': '✏️ Enter new rates (leave empty to keep current):',
    'new_rate': 'new rate:',
    'rates_updated': '✅ Exchange rates updated successfully',
    
    # Language selector
    'select_language': '🌐 Select Language / اختر اللغة:',
    'lang_english': '1. English',
    'lang_arabic': '2. العربية',
    'language_changed': '✅ Language changed'
}

# Arabic translations
AR = {
    # Login screen
    'app_title': 'نظام البنك',
    'demo_accounts': 'الحسابات التجريبية:',
    'admin': 'admin',
    'teller': 'teller',
    'customer': 'ahmed',
    'account_note': 'حساب العميل: ACC001',
    'tip_title': '💡 نصيحة: لإنشاء حساب جديد:',
    'tip1': '1. سجل الدخول كـ admin أو teller',
    'tip2': '2. اختر "إدارة المستخدمين" -> "إنشاء مستخدم جديد"',
    'tip3': '3. ثم اختر "إدارة الحسابات" -> "فتح حساب جديد"',
    'username': '👤 اسم المستخدم:',
    'password': '🔒 كلمة المرور:',
    'login_success': 'تم تسجيل الدخول بنجاح!',
    'login_failed': 'فشل تسجيل الدخول!',
    'welcome': 'مرحباً',
    'role': 'الدور',
    'enter_account': '🏦 أدخل رقم حسابك:',
    'logout': 'جاري تسجيل الخروج...',
    'logged_out': 'تم تسجيل الخروج بنجاح',
    'press_enter': '⏎ اضغط Enter للمتابعة...',
    'invalid_choice': '❌ اختيار غير صحيح',
    'connecting_error': '❌ لا يمكن الاتصال بالسيرفر. تأكد من تشغيل السيرفر.',
    
    # NEW KEYS ADDED
    'choose_option': '🔹 اختر العملية (1-11): ',
    'choose_sub_option': 'اختر (1-3): ',
    
    # Customer menu
    'check_balance': '1. 💰 عرض الرصيد',
    'deposit': '2. 📥 إيداع',
    'withdraw': '3. 📤 سحب',
    'transfer': '4. 🔄 تحويل',
    'history': '5. 📋 سجل العمليات',
    'multi_currency': '6. 💱 عرض الرصيد بعملات مختلفة',
    'convert': '7. 💹 تحويل عملات',
    'daily_limit': '8. 📊 معلومات حد السحب اليومي',
    'change_pass': '9. 🔑 تغيير كلمة المرور',
    'logout_btn': '10. 🚪 تسجيل الخروج',
    
    # Teller menu
    'check_balance_teller': '1. عرض الرصيد',
    'deposit_teller': '2. إيداع لحساب',
    'withdraw_teller': '3. سحب من حساب',
    'transfer_teller': '4. تحويل بين حسابات',
    'history_teller': '5. سجل عمليات حساب',
    'open_account': '6. فتح حساب جديد',
    'create_user': '7. إنشاء مستخدم جديد',
    'multi_currency_teller': '8. عرض الرصيد بعملات مختلفة',
    'convert_teller': '9. تحويل عملات',
    'change_pass_teller': '10. تغيير كلمة المرور',
    'logout_teller': '11. تسجيل الخروج',
    
    # Admin menu
    'account_mgmt': '1. إدارة الحسابات (عرض - فتح - حذف)',
    'user_mgmt': '2. إدارة المستخدمين (عرض - حذف - إنشاء)',
    'full_report': '3. تقرير المدير الشامل',
    'graph_report': '4. تقرير بالرسوم البيانية',
    'backup': '5. نسخة احتياطية',
    'set_limit': '6. تحديد حد سحب يومي',
    'update_rates': '7. تحديث أسعار الصرف',
    'export_excel': '8. تصدير تقرير Excel',
    'currencies': '9. عملات - تحويل وعرض',
    'change_pass_admin': '10. تغيير كلمة المرور',
    'logout_admin': '11. تسجيل الخروج',
    
    # Common messages
    'balance': '✅ الرصيد الحالي:',
    'jod': 'دينار',
    'amount': '💰 المبلغ:',
    'from_account': '🏦 من حساب:',
    'to_account': '🏦 إلى حساب:',
    'account_number': 'رقم الحساب:',
    'new_account': 'رقم الحساب الجديد:',
    'initial_balance': 'الرصيد الأولي:',
    'new_username': '👤 اسم المستخدم الجديد:',
    'new_password': '🔒 كلمة المرور:',
    'confirm_password': '✅ تأكيد كلمة المرور:',
    'role_type': '📌 نوع المستخدم:',
    'customer_role': 'عميل',
    'teller_role': 'صراف',
    'admin_role': 'مدير',
    'success': '✅ تم بنجاح',
    'error': '❌ خطأ',
    'daily_limit_info': '📊 معلومات حد السحب اليومي:',
    'daily_limit_text': 'الحد الأقصى اليومي:',
    'withdrawn_today': 'تم سحبه اليوم:',
    'remaining': 'المتبقي:',
    'old_password': '🔒 كلمة المرور الحالية:',
    'new_password_text': '🔑 كلمة المرور الجديدة:',
    'confirm_new': '✅ تأكيد كلمة المرور الجديدة:',
    'password_mismatch': '❌ كلمة المرور غير متطابقة',
    'password_changed': '✅ تم تغيير كلمة المرور بنجاح',
    
    # Account management
    'view_accounts': '1. عرض جميع الحسابات',
    'create_new_account': '2. فتح حساب جديد',
    'delete_account': '3. حذف حساب',
    'account_list': '📋 قائمة الحسابات:',
    'no_accounts': '📭 لا توجد حسابات',
    'user_must_exist': '📌 يجب أن يكون المستخدم موجوداً مسبقاً',
    'available_users': '👤 المستخدمين المتاحين:',
    'enter_username': '👤 اسم المستخدم:',
    'enter_account_num': '🏦 رقم الحساب:',
    'account_created': '✅ تم فتح الحساب بنجاح',
    'account_deleted': '✅ تم حذف الحساب بنجاح',
    
    # User management
    'view_users': '1. عرض جميع المستخدمين',
    'delete_user': '2. حذف مستخدم',
    'create_new_user': '3. إنشاء مستخدم جديد',
    'user_list': '👤 قائمة المستخدمين:',
    'no_users': '📭 لا توجد مستخدمين',
    'cannot_delete_admin': '❌ لا يمكن حذف المدير الرئيسي',
    'user_created': '✅ تم إنشاء المستخدم بنجاح',
    'user_deleted': '✅ تم حذف المستخدم بنجاح',
    
    # Admin report
    'admin_report_title': '📊 تقرير المدير الشامل:',
    'total_users': '👥 عدد المستخدمين:',
    'total_accounts': '🏦 عدد الحسابات:',
    'total_balance': '💰 إجمالي الأرصدة:',
    'transaction_stats': '📈 إحصائيات العمليات:',
    'most_active': '⭐ أكثر الحسابات نشاطاً:',
    'transactions': 'عملية',
    
    # Currency
    'balance_jod': '💰 الرصيد بالدينار:',
    'other_currencies': '💱 الرصيد بالعملات الأخرى:',
    'from_currency': 'من العملة:',
    'to_currency': 'إلى العملة:',
    'available_currencies': '💱 العملات المتاحة: USD, JOD, SYP, EUR, SAR',
    'convert_result': '✅ نتيجة التحويل:',
    'exchange_rate': 'سعر الصرف:',
    
    # Deposit/Withdraw/Transfer
    'deposit_success': '✅ تم الإيداع بنجاح',
    'withdraw_success': '✅ تم السحب بنجاح',
    'transfer_success': '✅ تم التحويل بنجاح',
    'insufficient_balance': '❌ الرصيد غير كاف',
    'invalid_amount': '❌ المبلغ غير صحيح',
    'account_not_found': '❌ الحساب غير موجود',
    
    # History
    'history_title': '📋 سجل العمليات (آخر 10):',
    'type': 'النوع',
    'date': 'التاريخ',
    'target': 'الحساب الآخر',
    
    # Graph
    'preparing_graph': '📊 جاري تحضير التقرير البياني...',
    'graph_error': '❌ لا يمكن إنشاء التقرير البياني',
    
    # Backup and Excel
    'creating_excel': '📎 جاري إنشاء تقرير Excel...',
    'excel_created': '✅ تم إنشاء تقرير Excel بنجاح',
    'excel_failed': '❌ فشل التصدير',
    'backup_created': '✅ تم إنشاء النسخة الاحتياطية',
    
    # Exchange rates
    'current_rates': '💱 أسعار الصرف الحالية:',
    'enter_new_rates': '✏️ أدخل الأسعار الجديدة:',
    'new_rate': 'سعر جديد:',
    'rates_updated': '✅ تم تحديث أسعار الصرف',
    
    # Language selector
    'select_language': '🌐 اختر اللغة / Select Language:',
    'lang_english': '1. English',
    'lang_arabic': '2. العربية',
    'language_changed': '✅ تم تغيير اللغة / Language changed'
}

# Dictionary of available languages
LANGUAGES = {
    'en': EN,
    'ar': AR
}

# Current language (will be set by user)
current_lang = 'en'

def set_language(lang_code):
    """Set the current language"""
    global current_lang
    if lang_code in LANGUAGES:
        current_lang = lang_code
        return True
    return False

def get_language():
    """Get current language code"""
    return current_lang

def t(key):
    """Translate a key to current language"""
    return LANGUAGES[current_lang].get(key, key)

def get_languages_list():
    """Get list of available languages"""
    return list(LANGUAGES.keys())

def get_language_name(lang_code):
    """Get language display name"""
    names = {'en': 'English', 'ar': 'العربية'}
    return names.get(lang_code, lang_code)

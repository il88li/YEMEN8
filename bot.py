import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import db
from dotenv import load_dotenv

load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# حالات المحادثة
CHOOSING_LANGUAGE, WAITING_FOR_FILE, WAITING_FOR_CODE, WAITING_FOR_LIBRARIES = range(4)

# متغيرات مؤقتة لتخزين البيانات
user_sessions = {}

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔧 تشغيل ملف", callback_data="run_file")],
        [InlineKeyboardButton("🚀 خدماتنا", callback_data="our_services")],
    ]
    return InlineKeyboardMarkup(keyboard)

def services_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📁 صنع ملف", callback_data="create_file")],
        [InlineKeyboardButton("📚 تثبيت مكتبات", callback_data="install_libraries")],
        [InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def language_choice_keyboard():
    keyboard = [
        [InlineKeyboardButton("🐍 Python", callback_data="lang_python")],
        [InlineKeyboardButton("🐘 PHP", callback_data="lang_php")],
        [InlineKeyboardButton("↩️ رجوع", callback_data="back_to_services")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    
    welcome_text = f"""
    👋 أهلاً بك {user.first_name}!

    🤖 **بوت إدارة ملفات البوتات**

    🎯 **المميزات:**
    • تشغيل ملفات بوتات Python و PHP
    • إنشاء ملفات بوتات جديدة
    • تثبيت المكتبات المطلوبة
    • إدارة البوتات النشطة

    ⚡ **الحدود:**
    • المستخدم العادي: 3 بوتات نشطة
    • المدير: 10 بوتات نشطة

    اختر من القائمة أدناه 👇
    """
    
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "run_file":
        user = query.from_user
        user_data = db.get_user(user.id)
        
        if not db.can_create_bot(user.id):
            await query.edit_message_text(
                "❌ لقد وصلت إلى الحد الأقصى للبوتات النشطة!\n"
                f"لديك {user_data[4]} بوت نشط من أصل {user_data[5]} مسموح به.",
                reply_markup=main_menu_keyboard()
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="run_python")],
            [InlineKeyboardButton("🐘 PHP", callback_data="run_php")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")],

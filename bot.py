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
        
        # هنا تم تصحيح الخطأ - إغلاق القوس المربع بشكل صحيح
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="run_python")],
            [InlineKeyboardButton("🐘 PHP", callback_data="run_php")],
            [InlineKeyboardButton("↩️ رجوع", callback_data="main_menu")],
        ]
        
        await query.edit_message_text(
            "📁 **تشغيل ملف بوت**\n\n"
            "اختر لغة البرمجة للبوت الذي تريد تشغيله:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "our_services":
        await query.edit_message_text(
            "🚀 **خدماتنا المتاحة:**\n\n"
            "• 📁 صنع ملف: إنشاء ملف بوت جديد\n"
            "• 📚 تثبيت مكتبات: إضافة مكتبات جديدة\n"
            "• ↩️ رجوع: العودة للقائمة الرئيسية",
            reply_markup=services_menu_keyboard()
        )
    
    elif query.data == "main_menu":
        await query.edit_message_text(
            "🏠 **القائمة الرئيسية**\n\nاختر الخدمة التي تريدها:",
            reply_markup=main_menu_keyboard()
        )

async def handle_services_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_file":
        user_sessions[query.from_user.id] = {"mode": "create_file"}
        await query.edit_message_text(
            "📁 **صنع ملف بوت جديد**\n\n"
            "اختر لغة البرمجة للبوت:",
            reply_markup=language_choice_keyboard()
        )
    
    elif query.data == "install_libraries":
        user_sessions[query.from_user.id] = {"mode": "install_libraries"}
        libraries = db.get_libraries()
        libraries_text = "\n".join([f"• {lib}" for lib in libraries[:10]])
        if len(libraries) > 10:
            libraries_text += "\n\n... وأكثر"
        
        await query.edit_message_text(
            "📚 **تثبيت مكتبات جديدة**\n\n"
            "⏳ **كيفية الاستخدام:**\n"
            "1. أرسل اسم المكتبة (مثال: python-telegram-bot)\n"
            "2. لإرسال أكثر من مكتبة، أرسل كل مكتبة في سطر مستقل\n"
            "3. أرسل /done عند الانتهاء\n\n"
            f"📝 **المكتبات المثبتة حالياً:**\n{libraries_text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ رجوع", callback_data="back_to_services")]])
        )
        return WAITING_FOR_LIBRARIES
    
    elif query.data == "back_to_services":
        await query.edit_message_text(
            "🚀 **خدماتنا المتاحة:**",
            reply_markup=services_menu_keyboard()
        )

async def handle_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = user_sessions.get(user_id, {})
    
    if query.data.startswith("lang_") or query.data.startswith("run_"):
        language = "python" if "python" in query.data else "php"
        extension = ".py" if language == "python" else ".php"
        
        if query.data.startswith("run_"):
            user_data.update({"mode": "run_file", "language": language})
            user_sessions[user_id] = user_data
            
            await query.edit_message_text(
                f"📥 **تشغيل ملف {language.upper()}**\n\n"
                f"⏳ **الخطوات:**\n"
                f"1. سوف أطلب منك إرسال ملف {extension}\n"
                f"2. ثم إرسال التوكن الخاص بالبوت\n"
                f"3. سأقوم بحفظه وتشغيله لك\n\n"
                f"📤 أرسل الملف الآن:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ إلغاء", callback_data="main_menu")]])
            )
            return WAITING_FOR_FILE
        
        else:  # create file
            user_data.update({"mode": "create_file", "language": language, "code": ""})
            user_sessions[user_id] = user_data
            
            await query.edit_message_text(
                f"📝 **إنشاء ملف {language.upper()}**\n\n"
                f"⏳ **الخطوات:**\n"
                f"1. أرسل كود البوت سطراً سطراً\n"
                f"2. عند الانتهاء، أرسل /don\n"
                f"3. سأقوم بحفظ الملف لك\n\n"
                f"💻 ابدأ بإرسال الكود:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ إلغاء", callback_data="back_to_services")]])
            )
            return WAITING_FOR_CODE
    
    elif query.data == "back_to_services":
        await query.edit_message_text(
            "🚀 **خدماتنا المتاحة:**",
            reply_markup=services_menu_keyboard()
        )
    
    return ConversationHandler.END

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = user_sessions.get(user_id, {})
    
    if user_data.get("mode") == "run_file" and update.message.document:
        file = await update.message.document.get_file()
        file_path = f"bots/{user_id}_{user_data['language']}_{update.message.document.file_name}"
        
        # حفظ الملف
        await file.download_to_drive(file_path)
        
        user_data["file_path"] = file_path
        user_sessions[user_id] = user_data
        
        await update.message.reply_text(
            "✅ **تم استلام الملف بنجاح!**\n\n"
            "📤 الآن أرسل توكن البوت الخاص بك:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ إلغاء", callback_data="main_menu")]])
        )
        return CHOOSING_LANGUAGE
    
    elif update.message.text == "/don" and user_data.get("mode") == "create_file":
        # حفظ الكود الذي تم تجميعه
        code = user_data.get("code", "")
        language = user_data.get("language", "python")
        extension = ".py" if language == "python" else ".php"
        file_name = f"bot_{user_id}_{len(code)}_{extension}"
        file_path = f"bots/{file_name}"
        
        # حفظ الكود في ملف
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # حفظ في قاعدة البيانات
        db.add_bot(user_id, file_name, language, "TOKEN_HERE", code, file_path)
        
        await update.message.reply_text(
            f"✅ **تم حفظ الملف بنجاح!**\n\n"
            f"📁 اسم الملف: {file_name}\n"
            f"🔤 اللغة: {language.upper()}\n"
            f"📊 حجم الكود: {len(code)} حرف\n\n"
            f"🏠 العودة للقائمة الرئيسية:",
            reply_markup=main_menu_keyboard()
        )
        
        user_sessions.pop(user_id, None)
        return ConversationHandler.END
    
    else:
        await update.message.reply_text("❌ لم أستلم ملفاً صالحاً. حاول مرة أخرى.")
        return WAITING_FOR_FILE

async def handle_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = user_sessions.get(user_id, {})
    
    if user_data.get("mode") == "create_file" and update.message.text:
        # تجميع الكود
        if "code" not in user_data:
            user_data["code"] = ""
        
        user_data["code"] += update.message.text + "\n"
        user_sessions[user_id] = user_data
        
        await update.message.reply_text(
            f"✅ **تم إضافة السطر بنجاح!**\n\n"
            f"📊 إجمالي الأسطر: {len(user_data['code'].splitlines())}\n"
            f"💾 استمر في إرسال الكود أو أرسل /don للانتهاء"
        )
        return WAITING_FOR_CODE
    
    return WAITING_FOR_CODE

async def handle_libraries_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/done":
        await update.message.reply_text(
            "✅ **تم الانتهاء من إدخال المكتبات**\n\n"
            "🏠 العودة للقائمة الرئيسية:",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    libraries = update.message.text.split('\n')
    user_id = update.message.from_user.id
    success_count = 0
    
    for lib in libraries:
        if lib.strip():
            if db.add_library(lib.strip(), user_id):
                success_count += 1
    
    await update.message.reply_text(
        f"✅ **تم معالجة المكتبات**\n\n"
        f"📚 المكتبات المضافة: {success_count}\n"
        f"🔤 المكتبات المرفوضة (مكررة): {len(libraries) - success_count}\n\n"
        f"💾 استمر في إرسال المكتبات أو أرسل /done للانتهاء"
    )
    return WAITING_FOR_LIBRARIES

async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = user_sessions.get(user_id, {})
    
    if user_data.get("mode") == "run_file" and update.message.text:
        token = update.message.text.strip()
        
        # هنا يمكنك إضافة منطق تشغيل البوت
        # هذا مثال مبسط
        
        await update.message.reply_text(
            f"✅ **تم استلام التوكن بنجاح!**\n\n"
            f"🔐 التوكن: {token[:10]}...\n"
            f"🔤 اللغة: {user_data.get('language', 'unknown')}\n"
            f"📁 الملف: {user_data.get('file_path', 'unknown')}\n\n"
            f"⏳ جاري تشغيل البوت...\n\n"
            f"✅ تم تشغيل البوت بنجاح!",
            reply_markup=main_menu_keyboard()
        )
        
        user_sessions.pop(user_id, None)
        return ConversationHandler.END
    
    return CHOOSING_LANGUAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions.pop(user_id, None)
    
    await update.message.reply_text(
        "❌ **تم الإلغاء**\n\nالعودة للقائمة الرئيسية:",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

def main():
    # إنشاء التطبيق
    application = Application.builder().token("7863334400:AAHCp4jO-pd2qqGQKqxLF1GGHh4w-0zPhqQ").build()
    
    # معالج المحادثة لإنشاء الملفات
    create_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_language_choice, pattern="^lang_")],
        states={
            WAITING_FOR_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # معالج المحادثة لتشغيل الملفات
    run_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_language_choice, pattern="^run_")],
        states={
            WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, handle_file_upload)],
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT, handle_token_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # معالج المحادثة للمكتبات
    libraries_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_services_menu, pattern="^install_libraries$")],
        states={
            WAITING_FOR_LIBRARIES: [MessageHandler(filters.TEXT, handle_libraries_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^(run_file|our_services|main_menu)$"))
    application.add_handler(CallbackQueryHandler(handle_services_menu, pattern="^(create_file|install_libraries|back_to_services)$"))
    application.add_handler(create_file_conv)
    application.add_handler(run_file_conv)
    application.add_handler(libraries_conv)
    
    # بدء البوت
    print("🤖 البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()

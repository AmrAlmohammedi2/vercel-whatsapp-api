import io
import cv2
import numpy as np
from yadsl import YADSL
from PIL import Image
import pytesseract
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

def start(update: Update, context: CallbackQueryHandler):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id, text="هذا بوت الاستعلام عن الرصيد، من فضلك ادخل اسم المستخدم")

default_password = "123456"

def solve_captcha(image_bytes):
    """
    دالة لحل الكابتشا تلقائيًا من bytes الصورة
    """
    try:
        # تحويل bytes الصورة إلى صورة PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # تحويل الصورة إلى OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # معالجة الصورة لتحسين دقة OCR
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # تطبيق thresholding لتحسين النص
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # استخدام pytesseract لقراءة النص
        captcha_text = pytesseract.image_to_string(thresh, 
                                                  config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        
        # تنظيف النص من المسافات والرموز غير المرغوب فيها
        captcha_text = ''.join(filter(str.isalnum, captcha_text))
        
        print(f"الكابتشا المقروءة: {captcha_text}")
        return captcha_text.strip()
    
    except Exception as e:
        print(f"خطأ في حل الكابتشا: {e}")
        return None

def username(update: Update, context: CallbackQueryHandler):
    try:
        username_text = update.message.text
        
        # إرسال رسالة للمستخدم أن العملية جارية
        update.message.reply_text("🔍 جاري الاستعلام عن الرصيد...")
        
        yd = YADSL(username=username_text, password=default_password)
        yd.login()
        image_bytes = yd.fetch_captcha()
        
        # إرسال صورة الكابتشا للمستخدم (اختياري)
        update.message.reply_photo(photo=io.BytesIO(image_bytes))
        
        # حل الكابتشا تلقائيًا
        captcha_text = solve_captcha(image_bytes)
        
        if captcha_text and len(captcha_text) >= 3:  # التأكد من أن النص ليس فارغًا أو قصيرًا جدًا
            update.message.reply_text(f"📝 تم قراءة الكابتشا تلقائيًا: {captcha_text}")
            yd.verify(captcha_text)
            data = yd.fetch_data()
            response = "\n".join([f"{k}: {v}" for k, v in data.items()])
            update.message.reply_text(f"📊 معلومات الرصيد:\n{response}")
        else:
            # إذا فشل الحل التلقائي، نطلب من المستخدم إدخال الكابتشا يدويًا
            update.message.reply_text("❌ لم أستطع قراءة الكابتشا تلقائيًا. من فضلك أدخل رمز الكابتشا يدويًا:")
            
            # حفظ البيانات في context لاستخدامها لاحقًا
            context.user_data['yd'] = yd
            context.user_data['username'] = username_text
            
    except Exception as e:
        update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

def handle_manual_captcha(update: Update, context: CallbackQueryHandler):
    """
    معالجة إدخال الكابتشا يدويًا من المستخدم
    """
    try:
        if 'yd' in context.user_data:
            captcha_text = update.message.text.strip()
            yd = context.user_data['yd']
            
            yd.verify(captcha_text)
            data = yd.fetch_data()
            response = "\n".join([f"{k}: {v}" for k, v in data.items()])
            update.message.reply_text(f"📊 معلومات الرصيد:\n{response}")
            
            # تنظيف البيانات المؤقتة
            context.user_data.pop('yd', None)
            context.user_data.pop('username', None)
        else:
            update.message.reply_text("❌ لا توجد عملية استعلام نشطة. استخدم /start للبدء.")
            
    except Exception as e:
        update.message.reply_text(f"❌ خطأ في التحقق: {str(e)}")

def main():
    updater = Updater("6549896644:AAFMjHPGBbG_ENuauHp9NViUrZQ2kNpTHYY", use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, username))
    
    # معالج منفصل لإدخال الكابتشا يدويًا
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^[a-zA-Z0-9]{3,8}$'), handle_manual_captcha))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

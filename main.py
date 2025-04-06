import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests
from bs4 import BeautifulSoup
import schedule
import time
import pandas as pd
import datetime  # <- Añade esto con los otros imports

# Configura logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carga variables de entorno (crea un archivo .env con TU_TOKEN)
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = "ADMIN_CHAT_ID"  # Para recibir reportes

# Datos de afiliados (¡Regístrate en estas plataformas!)
AFFILIATE_LINKS = {
    "workana": "https://www.workana.com/?ref=TU_CODIGO",
    "premise": "https://premise.com/ref/?ref=TU_CODIGO",
    "toloka": "https://toloka.yandex.com/?ref=TU_CODIGO",
    "fiverr": "https://www.fiverr.com/?utm_source=TU_CODIGO"
}

# Manejo de errores
def error_handler(update: Update, context: CallbackContext):
    logger.error(f'Update {update} caused error {context.error}')
    try:
        if update.callback_query:
            update.callback_query.message.reply_text('❌ Ocurrió un error. Por favor, intenta nuevamente.')
    except:
        if update.message:
            update.message.reply_text('❌ Ocurrió un error. Por favor, intenta nuevamente.')

# Scraping de trabajos remotos
def scrape_workana():
    url = "https://www.workana.com/jobs?language=es"
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        jobs = []
        
        for job in soup.find_all('div', class_='project-item')[:5]:
            title = job.find('h2').text.strip()
            budget = job.find('span', class_='budget').text.strip()
            link = "https://www.workana.com" + job.find('a')['href']
            jobs.append({"title": title, "budget": budget, "link": link})
        
        return jobs
    except Exception as e:
        logger.error(f"Error scraping Workana: {e}")
        return []

# Comando /start
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    keyboard = [
        [InlineKeyboardButton("📌 Trabajos Remotos", callback_data='trabajos')],
        [InlineKeyboardButton("📝 Encuestas Pagadas", callback_data='encuestas')],
        [InlineKeyboardButton("📚 Guías Premium", callback_data='guias')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"""¡Hola {user.first_name}! 👋\n
Soy *GanaDineroLA*, tu asistente para ganar dinero en LATAM.""",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Comando /trabajos
def trabajos(update: Update, context: CallbackContext):
    jobs = scrape_workana()
    if not jobs:
        update.message.reply_text("⚠️ No hay trabajos disponibles ahora. Intenta más tarde.")
        return
    
    for job in jobs:
        message = (
            f"*{job['title']}*\n"
            f"💵 *Presupuesto*: {job['budget']}\n"
            f"🔗 [Ver trabajo]({job['link']})\n"
            f"🎯 [Postúlate aquí]({AFFILIATE_LINKS['workana']})"
        )
        update.message.reply_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

# Comando /encuestas
def encuestas(update: Update, context: CallbackContext):
    surveys = [
        {
            "name": "Premise",
            "description": "Encuestas pagadas en USD ($1-$5 cada una)",
            "link": AFFILIATE_LINKS['premise']
        },
        {
            "name": "Toloka",
            "description": "Tareas simples desde tu celular ($0.50-$3)",
            "link": AFFILIATE_LINKS['toloka']
        }
    ]
    
    for survey in surveys:
        update.message.reply_text(
            f"📌 *{survey['name']}*\n"
            f"{survey['description']}\n"
            f"🔗 [Regístrate aquí]({survey['link']})",
            parse_mode='Markdown'
        )

# Comando /guias (Venta de PDF)
def guias(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💰 Comprar Guía ($5)", callback_data='comprar_guia')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "📚 *Guía Premium: Cómo Cobrar en USD desde LATAM*\n"
        "✅ Métodos comprobados (PayPal, Binance, Zinli)\n"
        "✅ Evita bloqueos y comisiones altas\n"
        "✅ Incluye lista de empleadores que pagan en crypto\n\n"
        "Precio: $5 (pago por Binance/PayPal)",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Handler para botones
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    try:
        if query.data == 'trabajos':
            # Para botones inline, usamos query.edit_message_text en lugar de update.message.reply_text
            jobs = scrape_workana()
            if not jobs:
                query.edit_message_text("⚠️ No hay trabajos disponibles ahora. Intenta más tarde.")
                return
            
            for job in jobs:
                message = (
                    f"*{job['title']}*\n"
                    f"💵 *Presupuesto*: {job['budget']}\n"
                    f"🔗 [Ver trabajo]({job['link']})\n"
                    f"🎯 [Postúlate aquí]({AFFILIATE_LINKS['workana']})"
                )
                query.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                
        elif query.data == 'encuestas':
            surveys = [
                {
                    "name": "Premise",
                    "description": "Encuestas pagadas en USD ($1-$5 cada una)",
                    "link": AFFILIATE_LINKS['premise']
                },
                {
                    "name": "Toloka",
                    "description": "Tareas simples desde tu celular ($0.50-$3)",
                    "link": AFFILIATE_LINKS['toloka']
                }
            ]
            
            for survey in surveys:
                query.message.reply_text(
                    f"📌 *{survey['name']}*\n"
                    f"{survey['description']}\n"
                    f"🔗 [Regístrate aquí]({survey['link']})",
                    parse_mode='Markdown'
                )
                
        elif query.data == 'guias':
            keyboard = [
                [InlineKeyboardButton("💰 Comprar Guía ($5)", callback_data='comprar_guia')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                "📚 *Guía Premium: Cómo Cobrar en USD desde LATAM*\n"
                "✅ Métodos comprobados (PayPal, Binance, Zinli)\n"
                "✅ Evita bloqueos y comisiones altas\n"
                "✅ Incluye lista de empleadores que pagan en crypto\n\n"
                "Precio: $5 (pago por Binance/PayPal)",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == 'comprar_guia':
            query.edit_message_text(
                "🛒 *Compra la Guía Premium*\n\n"
                "1. Envía $5 vía Binance a esta dirección:\n"
                "`bNB1q2w3e4r5t6y7u8i9o0p`\n\n"
                "2. Responde con el hash de la transacción.\n"
                "3. Recibirás el PDF en menos de 24h.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en button_handler: {e}")
        query.edit_message_text("❌ Ocurrió un error. Por favor, intenta nuevamente.")
    
# Enviar trabajos automáticos (diarios)
def send_daily_jobs(context: CallbackContext):
    jobs = scrape_workana()
    if jobs:
        for job in context.bot.get_chat_administrators("@GanaDineroLA"):
            try:
                context.bot.send_message(
                    chat_id=job.user.id,
                    text=f"🌟 *Oportunidad Diaria*\n\n{job['title']}\n🔗 {job['link']}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error enviando trabajo a {job.user.id}: {e}")

# Función principal
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    job_queue = updater.job_queue

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("trabajos", trabajos))
    dp.add_handler(CommandHandler("encuestas", encuestas))
    dp.add_handler(CommandHandler("guias", guias))
    dp.add_handler(CallbackQueryHandler(button_handler))

    # Programa el envío diario a las 9 AM
    job_queue.run_daily(
        send_daily_jobs,
        time=datetime.time(hour=9, minute=0, second=0),  # Hora fija
        days=(0, 1, 2, 3, 4, 5, 6)  # Todos los días
    )

    # Inicia el bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
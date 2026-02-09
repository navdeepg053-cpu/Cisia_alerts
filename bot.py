# CEnT-S Telegram Bot - Production Ready Version
# Deploy this to Render.com for FREE 24/7 uptime

import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx
from bs4 import BeautifulSoup
from pymongo import MongoClient
import traceback

# ========== CONFIGURATION ==========
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MONGODB_URI = os.environ.get("MONGODB_URI")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required!")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
db = None
subscribers_collection = None

def init_db():
    """Initialize MongoDB connection."""
    global db, subscribers_collection
    if MONGODB_URI:
        try:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            db = client['cisia_alerts']
            subscribers_collection = db['subscribers']
            subscribers_collection.create_index("chat_id", unique=True)
            logger.info("✅ MongoDB connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}. Using in-memory storage.")
            db = None
    else:
        logger.info("📝 Using in-memory storage (no MONGODB_URI provided)")

# In-memory fallback
subscribers_memory = set()

def add_subscriber(chat_id):
    """Add subscriber to database or memory."""
    subscribers_memory.add(chat_id)
    if subscribers_collection:
        try:
            subscribers_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"chat_id": chat_id, "subscribed": True}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"DB error adding subscriber: {e}")


def remove_subscriber(chat_id):
    """Remove subscriber from database or memory."""
    subscribers_memory.discard(chat_id)
    if subscribers_collection:
        try:
            subscribers_collection.delete_one({"chat_id": chat_id})
        except Exception as e:
            logger.error(f"DB error removing subscriber: {e}")


def get_subscribers():
    """Get all subscribers from database or memory."""
    if subscribers_collection:
        try:
            return {doc["chat_id"] for doc in subscribers_collection.find()}
        except Exception as e:
            logger.error(f"DB error fetching subscribers: {e}")
            return subscribers_memory
    return subscribers_memory

# ========== SCRAPER ==========
CISIA_URL = "https://testcisia.it/calendario.php?tolc=cents&lingua=inglese"
TIMEOUT = 15.0
MAX_RETRIES = 3

async def scrape_cisia():
    """Scrape CISIA for CENT@CASA/CENT@HOME spots with retry logic."""
    spots = []
    
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as http:
                r = await http.get(
                    CISIA_URL,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Connection": "keep-alive"
                    }
                )
                
                if r.status_code != 200:
                    logger.warning(f"CISIA returned status {r.status_code}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                soup = BeautifulSoup(r.text, 'lxml')
                table = soup.find('table')
                
                if not table:
                    logger.warning("No table found in CISIA response")
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 8:
                        try:
                            test_type = cells[0].get_text(strip=True)
                            
                            # Check for CASA or HOME variants
                            if any(keyword in test_type.upper() for keyword in ["CASA", "HOME", "@"]):
                                has_link = cells[6].find('a') is not None
                                
                                spots.append({
                                    "test_type": test_type,
                                    "university": cells[1].get_text(strip=True),
                                    "city": cells[3].get_text(strip=True),
                                    "deadline": cells[4].get_text(strip=True),
                                    "spots": cells[5].get_text(strip=True),
                                    "available": has_link,
                                    "test_date": cells[7].get_text(strip=True) if len(cells) > 7 else "N/A",
                                    "scraped_at": datetime.now().isoformat()
                                })
                        except IndexError:
                            continue
                
                logger.info(f"✅ Scraped {len(spots)} CENT@CASA/HOME sessions")
                return spots
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout attempt {attempt + 1}/{MAX_RETRIES}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"Scrape error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            await asyncio.sleep(2 ** attempt)
    
    logger.error(f"Failed to scrape after {MAX_RETRIES} attempts")
    return []

# ========== BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - send chat ID."""
    try:
        chat_id = update.effective_chat.id
        name = update.effective_user.first_name or "User"
        
        add_subscriber(chat_id)
        
        await update.message.reply_html(
            f"👋 <b>Welcome, {name}!</b>\n\n"
            f"🔔 <b>CENT@CASA/HOME Alerts Bot</b>\n\n"
            f"🔑 Your Chat ID:\n<code>{chat_id}</code>\n\n"
            f"✅ You're now subscribed to CENT@CASA/HOME alerts!\n"
            f"You'll get instant notifications when spots open.\n\n"
            f"Send /help for more commands."
        )
        logger.info(f"✅ New subscriber: {chat_id}")
    except Exception as e:
        logger.error(f"Error in /start: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    try:
        chat_id = update.effective_chat.id
        spots = await scrape_cisia()
        available = [s for s in spots if s["available"]]
        subscribers = get_subscribers()
        
        db_status = "✅ MongoDB" if subscribers_collection else "📝 In-Memory"
        
        await update.message.reply_html(
            f"🤖 <b>Bot Status: ONLINE</b>\n\n"
            f"📊 CENT@CASA/HOME Sessions: {len(spots)}\n"
            f"🟢 Available spots: {len(available)}\n"
            f"👥 Subscribers: {len(subscribers)}\n"
            f"💾 Storage: {db_status}\n\n"
            f"Your ID: <code>{chat_id}</code>"
        )
    except Exception as e:
        logger.error(f"Error in /status: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("❌ Failed to fetch status.")


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /id command."""
    try:
        chat_id = update.effective_chat.id
        await update.message.reply_html(f"🔑 Your Chat ID:\n<code>{chat_id}</code>")
    except Exception as e:
        logger.error(f"Error in /id: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    try:
        await update.message.reply_html(
            "🤖 <b>CENT@CASA/HOME Alert Bot</b>\n\n"
            "<b>Commands:</b>\n"
            "/start - Subscribe & get your Chat ID\n"
            "/status - Check bot status & available spots\n"
            "/id - Show your Chat ID\n"
            "/check - Check for available spots NOW\n"
            "/stop - Unsubscribe from alerts\n"
            "/help - Show this message\n\n"
            "<b>How it works:</b>\n"
            "✅ Bot checks CISIA every 30 seconds\n"
            "🔔 You'll get instant alerts when spots open\n"
            "⏰ No spam - only NEW spots trigger alerts"
        )
    except Exception as e:
        logger.error(f"Error in /help: {e}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""
    try:
        chat_id = update.effective_chat.id
        remove_subscriber(chat_id)
        await update.message.reply_text(
            "🔕 You've been unsubscribed from alerts.\n"
            "Send /start to re-subscribe anytime."
        )
        logger.info(f"❌ Subscriber removed: {chat_id}")
    except Exception as e:
        logger.error(f"Error in /stop: {e}")


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /check command - check spots now."""
    try:
        await update.message.reply_text("🔍 Checking CISIA for available spots...")
        
        spots = await scrape_cisia()
        available = [s for s in spots if s["available"]]
        
        if available:
            msg = "🟢 <b>SPOTS AVAILABLE!</b>\n\n"
            for s in available:
                msg += (
                    f"🏫 <b>{s['university']}</b>\n"
                    f"📍 {s['city']}\n"
                    f"📅 Test Date: {s['test_date']}\n"
                    f"⏰ Deadline: {s['deadline']}\n"
                    f"🎫 Spots: {s['spots']}\n\n"
                )
            msg += "👉 <a href='https://testcisia.it/studenti_tolc/login_sso.php'><b>BOOK NOW</b></a>"
        else:
            msg = f"🔴 <b>No spots currently available</b>\n\nTotal CENT@CASA/HOME sessions: {len(spots)}"
        
        await update.message.reply_html(msg)
    except Exception as e:
        logger.error(f"Error in /check: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("❌ Failed to check spots. Try again later.")


async def handle_any(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any other message."""
    try:
        chat_id = update.effective_chat.id
        await update.message.reply_html(
            f"💬 <b>Message received</b>\n\n"
            f"Your Chat ID: <code>{chat_id}</code>\n"
            f"Send /help for available commands."
        )
    except Exception as e:
        logger.error(f"Error in handle_any: {e}")


# ========== BACKGROUND SCRAPER ==========
last_available = set()

async def check_and_alert(app):
    """Check for new spots and alert subscribers every 30 seconds."""
    global last_available
    
    logger.info("🚀 Background alert checker started")
    
    while True:
        try:
            spots = await scrape_cisia()
            available = {f"{s['university']}|{s['test_date']}" for s in spots if s["available"]}
            
            # Find NEW spots (weren't available before)
            new_spots = available - last_available
            
            subscribers = get_subscribers()
            
            if new_spots and subscribers:
                logger.info(f"🔔 Found {len(new_spots)} NEW spot(s)! Alerting {len(subscribers)} subscribers...")
                
                for spot in spots:
                    key = f"{spot['university']}|{spot['test_date']}"
                    if key in new_spots:
                        msg = (
                            f"🟢 <b>NEW SPOT AVAILABLE!</b>\n\n"
                            f"📌 <b>{spot['test_type']}</b>\n"
                            f"🏫 {spot['university']}\n"
                            f"📍 {spot['city']}\n"
                            f"📅 Test Date: {spot['test_date']}\n"
                            f"⏰ Deadline: {spot['deadline']}\n"
                            f"🎫 Available Spots: {spot['spots']}\n\n"
                            f"👉 <a href='https://testcisia.it/studenti_tolc/login_sso.php'><b>BOOK IMMEDIATELY!</b></a>"
                        )
                        
                        failed_subscribers = []
                        for chat_id in subscribers.copy():
                            try:
                                await app.bot.send_message(chat_id, msg, parse_mode="HTML")
                                logger.debug(f"✅ Alert sent to {chat_id}")
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to send to {chat_id}: {e}")
                                failed_subscribers.append(chat_id)
                        
                        # Remove failed subscribers
                        for chat_id in failed_subscribers:
                            remove_subscriber(chat_id)
            
            last_available = available
            
        except Exception as e:
            logger.error(f"❌ Check error: {e}\n{traceback.format_exc()}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# ========== MAIN ==========
def main():
    """Start the bot."""
    init_db()
    logger.info("🚀 Starting CEnT-S Alert Bot...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any))
    
    # Start background scraper
    async def post_init(application):
        logger.info("📡 Starting background scraper task...")
        asyncio.create_task(check_and_alert(application))
    
    app.post_init = post_init
    
    # Run with webhook or polling
    try:
        if WEBHOOK_URL:
            logger.info(f"🌐 Starting webhook mode: {WEBHOOK_URL}")
            app.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
            )
        else:
            logger.info("📡 Starting polling mode")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
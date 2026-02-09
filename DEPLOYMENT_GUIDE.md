# DEPLOYMENT_GUIDE.md

## 🚀 Complete Deployment Guide for CENT@CASA Alert Bot

### QUICK START - RENDER.COM (5 MINUTES)

1. **Create Telegram Bot**
   - Open Telegram, search `@BotFather`
   - Send `/newbot`
   - Copy your Bot Token

2. **Set Up MongoDB Atlas**
   - Go to mongodb.com/cloud/atlas
   - Create free account and M0 cluster
   - Create database user
   - Copy connection string (replace `<password>`)

3. **Deploy to Render**
   - Go to render.com, sign in with GitHub
   - Click "New +" → "Web Service"
   - Select your Cisia_alerts repo
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `python bot.py`
   - Add Environment Variables:
     ```
     TELEGRAM_BOT_TOKEN=your_token_here
     MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/cisia_alerts?retryWrites=true&w=majority
     PORT=8000
     ```
   - Click Deploy

4. **Start Using**
   - Find your bot in Telegram
   - Send `/start` to subscribe
   - Bot will alert you when spots open!

---

### BOT COMMANDS

- `/start` - Subscribe to alerts
- `/status` - Check available spots
- `/check` - Check now
- `/stop` - Unsubscribe
- `/help` - Show commands

---

### DOCKER SETUP (LOCAL)

```bash
git clone https://github.com/navdeepg053-cpu/Cisia_alerts.git
cd Cisia_alerts
cp .env.example .env
# Edit .env with your values
docker-compose up --build
```

---

### LOCAL PYTHON SETUP

```bash
git clone https://github.com/navdeepg053-cpu/Cisia_alerts.git
cd Cisia_alerts
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python bot.py
```

---

### TROUBLESHOOTING

- **No alerts?** Check you ran `/start` and token is correct
- **DB error?** Bot works without MongoDB (uses memory)
- **Scraper failing?** CISIA website structure may have changed
- **Render build failing?** Check logs in Render dashboard

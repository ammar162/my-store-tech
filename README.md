# AM05 TECH — Full Stack Platform

## 🚀 Features
- 💬 WebSocket realtime notifications (Flask-SocketIO)
- 📧 Email HTML automatique à chaque commande
- 📱 WhatsApp bot (Twilio) — auto-reply avec AI
- 🧠 AI Chatbot (Claude) sur la landing page
- 📊 Dashboard live avec graphiques
- 🔔 Browser notifications + son
- 📦 QR Code sur le reçu

## ⚙️ Installation

```bash
pip install -r requirements.txt
python app.py
```

## 🔧 Configuration (app.py)

```python
# Email (Gmail App Password)
EMAIL_SENDER   = "ton.email@gmail.com"
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
EMAIL_RECEIVER = "ton.email@gmail.com"

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID = "ACxxx..."
TWILIO_AUTH_TOKEN  = "xxx..."
OWNER_WA_TO        = "whatsapp:+212XXXXXXXXX"

# AI Claude
ANTHROPIC_API_KEY = "sk-ant-..."

# Telegram (optionnel)
TELEGRAM_BOT_TOKEN = "xxx..."
TELEGRAM_CHAT_ID   = "xxx..."
```

## 📡 Endpoints

| URL | Description |
|-----|-------------|
| / | Landing page + AI chat |
| /order | POST — nouvelle commande |
| /admin | Dashboard temps réel |
| /api/chat | POST — AI chatbot |
| /api/stats | GET — statistiques |
| /api/orders | GET — liste commandes |
| /api/orders/<id>/status | PATCH — changer statut |
| /webhook/whatsapp | POST — Twilio webhook |

## 📱 WhatsApp Bot Setup (Twilio)

1. Crée un compte sur twilio.com
2. Active le Sandbox WhatsApp
3. Configure le webhook URL: `https://TON_DOMAINE/webhook/whatsapp`
4. Remplis TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN

## 🧠 AI Chatbot Setup

1. Va sur console.anthropic.com
2. Crée une API key
3. Mets-la dans ANTHROPIC_API_KEY
→ Sans API key, le chatbot fonctionne en mode fallback intelligent

## 📁 Structure
```
am05tech/
├── app.py              ← Backend principal
├── requirements.txt
├── orders.json         ← Commandes (auto)
├── orders.csv          ← Export Excel (auto)
├── chat_log.json       ← Logs chats (auto)
├── templates/
│   ├── index.html      ← Landing page + chatbot
│   ├── receipt.html    ← Reçu + QR Code
│   └── admin.html      ← Dashboard live
└── static/
    └── images/         ← logo.png, 1-6.png
```

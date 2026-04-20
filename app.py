"""
AM05 TECH — Backend
✅ Login admin avec code + mot de passe
✅ Préparation de commande avec code unique
✅ Notification WhatsApp instantanée à l'admin
✅ Dashboard admin sécurisé
"""

import json, csv, os, qrcode, base64, requests, threading, smtplib
from io import BytesIO
from datetime import datetime
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# ════════════════════════════════════════════
#  ⚙️  CONFIG
# ════════════════════════════════════════════

OWNER_PHONE    = "212626379109"
ADMIN_CODE     = "AM05"
ADMIN_PASSWORD = "admin2026"

EMAIL_SENDER   = ""
EMAIL_PASSWORD = ""
EMAIL_RECEIVER = ""

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID   = ""

# ════════════════════════════════════════════

app = Flask(__name__)
app.config['SECRET_KEY'] = 'am05tech-secret-2026'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

ORDERS_JSON = 'orders.json'
ORDERS_CSV  = 'orders.csv'
os.makedirs('static/qr_codes', exist_ok=True)

OFFER_LABELS = {
    '1pc':  ('قطعة واحدة', '199 DH', 199),
    '2pcs': ('قطعتان',     '349 DH', 349),
}

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def generate_order_id():
    return f"AM05-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

def generate_prep_code(order_id):
    short = order_id.split('-')[-1] if '-' in order_id else order_id[:4]
    return f"PREP-{short}-{uuid.uuid4().hex[:3].upper()}"

def generate_qr_base64(data):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(data); qr.make(fit=True)
    img = qr.make_image(fill_color="#1d4ed8", back_color="white")
    buf = BytesIO(); img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def load_json(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_json(path, item):
    lst = load_json(path); lst.append(item); save_json(path, lst)

def save_csv(data):
    exists = os.path.isfile(ORDERS_CSV)
    with open(ORDERS_CSV, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=data.keys())
        if not exists: w.writeheader()
        w.writerow(data)

def build_whatsapp_url(order):
    msg = (
        f"🛒 *طلب جديد — AM05 TECH*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *#{order['order_id']}*\n"
        f"👤 *الاسم:* {order['name']}\n"
        f"📞 *الهاتف:* {order['phone']}\n"
        f"🏙️ *المدينة:* {order['city']}\n"
        f"📍 *العنوان:* {order.get('address', '—')}\n"
        f"📦 *العرض:* {order['offer_label']} — {order['price']}\n"
        f"🕐 *التاريخ:* {order['date']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ جاهز للتأكيد والإرسال!"
    )
    encoded = requests.utils.quote(msg)
    return f"https://wa.me/{OWNER_PHONE}?text={encoded}"

def build_whatsapp_prep_url(order):
    prep_code = order.get('prep_code', '—')
    msg = (
        f"📦 *طلبكم جاهز — AM05 TECH* 🎉\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"السلام {order['name']} 👋\n"
        f"طلبكم رقم *#{order['order_id']}* تم تجهيزه!\n\n"
        f"📦 *AirPods Pro 2 — {order['offer_label']}*\n"
        f"💰 *المبلغ:* {order['price']} (الدفع عند الاستلام)\n\n"
        f"🔑 *كود التتبع الخاص بك:* {prep_code}\n\n"
        f"🚚 التوصيل خلال 24-48 ساعة\n"
        f"شكراً على ثقتك في AM05 TECH! 🙏"
    )
    encoded = requests.utils.quote(msg)
    phone212 = '212' + order['phone'][1:] if order['phone'].startswith('0') else order['phone']
    return f"https://wa.me/{phone212}?text={encoded}"

def send_email(order):
    if not EMAIL_SENDER: return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🛒 طلب جديد #{order['order_id']} — {order['name']}"
        msg['From'] = f"AM05 TECH <{EMAIL_SENDER}>"
        msg['To']   = EMAIL_RECEIVER
        msg.attach(MIMEText(f"طلب جديد #{order['order_id']} — {order['name']} — {order['price']}", 'plain', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as s:
            s.login(EMAIL_SENDER, EMAIL_PASSWORD)
            s.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"[Email] ✅ #{order['order_id']}")
    except Exception as e:
        print(f"[Email] ❌ {e}")

def notify_telegram(order):
    if not TELEGRAM_BOT_TOKEN: return
    msg = f"🛒 *طلب جديد #{order['order_id']}*\n👤 {order['name']} · 📞 `{order['phone']}`\n🏙️ {order['city']}\n📦 {order['offer_label']} — *{order['price']}*"
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"[Telegram] ❌ {e}")

def send_all_notifications(order):
    wa_url = build_whatsapp_url(order)
    socketio.emit('new_order', {'order': order, 'wa_url': wa_url})
    send_email(order)
    notify_telegram(order)

# ─────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def order():
    name    = request.form.get('name', '').strip()
    phone   = request.form.get('phone', '').strip()
    city    = request.form.get('city', '').strip()
    address = request.form.get('address', '').strip()
    offer   = request.form.get('offer', '1pc')
    if not all([name, phone, city]):
        return redirect(url_for('index'))
    order_id = generate_order_id()
    now      = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    offer_label, offer_price, _ = OFFER_LABELS.get(offer, ('قطعة واحدة', '199 DH', 199))
    order_data = {
        "order_id": order_id, "date": date_str, "name": name, "phone": phone,
        "city": city, "address": address, "offer": offer,
        "offer_label": offer_label, "price": offer_price,
        "status": "En attente", "prep_code": None,
    }
    append_json(ORDERS_JSON, order_data)
    save_csv(order_data)
    threading.Thread(target=send_all_notifications, args=(order_data,), daemon=True).start()
    qr_b64 = generate_qr_base64(f"AM05 TECH | #{order_id}\n{name} | {phone}\n{city}\n{offer_label} {offer_price}\n{date_str}")
    return render_template('receipt.html',
        order_id=order_id, date_pretty=now.strftime("%d/%m/%Y à %H:%M"),
        name=name, phone=phone, city=city, address=address,
        offer_label=offer_label, offer_price=offer_price,
        qr_b64=qr_b64, wa_url=build_whatsapp_url(order_data))

# ── Admin Login ──

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        code     = request.form.get('code', '').strip()
        password = request.form.get('password', '').strip()
        if code == ADMIN_CODE and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "كود أو كلمة السر غلط ❌"
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin():
    orders  = sorted(load_json(ORDERS_JSON), key=lambda x: x.get('date',''), reverse=True)
    revenue = sum(OFFER_LABELS.get(o.get('offer','1pc'),('','',199))[2] for o in orders)
    return render_template('admin.html', orders=orders, total=len(orders), revenue=revenue)

@app.route('/api/orders/<order_id>/prepare', methods=['POST'])
@admin_required
def prepare_order(order_id):
    orders = load_json(ORDERS_JSON)
    prep_code = None
    wa_url    = None
    for o in orders:
        if o['order_id'] == order_id:
            if not o.get('prep_code'):
                o['prep_code'] = generate_prep_code(order_id)
            o['status'] = 'Préparé'
            prep_code = o['prep_code']
            wa_url    = build_whatsapp_prep_url(o)
            break
    save_json(ORDERS_JSON, orders)
    socketio.emit('order_updated', {'order_id': order_id, 'status': 'Préparé', 'prep_code': prep_code})
    return jsonify({'ok': True, 'prep_code': prep_code, 'wa_url': wa_url})

@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
@admin_required
def update_status(order_id):
    orders = load_json(ORDERS_JSON)
    status = (request.get_json() or {}).get('status', 'En attente')
    for o in orders:
        if o['order_id'] == order_id:
            o['status'] = status; break
    save_json(ORDERS_JSON, orders)
    socketio.emit('order_updated', {'order_id': order_id, 'status': status})
    return jsonify({'ok': True})

@socketio.on('connect')
def on_connect():
    orders  = load_json(ORDERS_JSON)
    revenue = sum(OFFER_LABELS.get(o.get('offer','1pc'),('','',199))[2] for o in orders)
    emit('stats', {'total': len(orders), 'revenue': revenue})

if __name__ == '__main__':
    print("═" * 52)
    print("  🚀  AM05 TECH — Serveur démarré")
    print(f"  🔐  Admin code     → {ADMIN_CODE}")
    print(f"  🔐  Admin password → {ADMIN_PASSWORD}")
    print(f"  🌐  Site   → http://localhost:5000")
    print(f"  📊  Admin  → http://localhost:5000/admin/login")
    print("═" * 52)
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)

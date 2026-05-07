"""Intercambia un code OAuth de MELI por refresh_token y lo manda a Telegram.
Inputs (env):
  CODE          → el code TG-... de MELI
  APP_SECRET    → MELI app secret
  TG_TOKEN/CHAT → Telegram para mandar el refresh_token al usuario
"""
import os, requests, json

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
CODE = os.environ["CODE"].strip()
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")
REDIRECT = "https://oauth.pstmn.io/v1/callback"

# Paso 1: intercambiar code → token
print(f"Intercambiando code: {CODE[:20]}...")
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "authorization_code",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": CODE,
    "redirect_uri": REDIRECT,
}, timeout=20)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

if r.status_code != 200:
    raise SystemExit(f"❌ Falló: {r.text}")

j = r.json()
refresh_token = j["refresh_token"]
access_token = j["access_token"]

# Paso 2: verificar quién es
me = requests.get("https://api.mercadolibre.com/users/me",
                  headers={"Authorization": f"Bearer {access_token}"}, timeout=15).json()
print(f"\n✅ Cuenta autorizada:")
print(f"  user_id:  {me.get('id')}")
print(f"  nickname: {me.get('nickname')}")
print(f"  email:    {me.get('email')}")
print(f"  name:     {me.get('first_name','')} {me.get('last_name','')}")
print(f"  country:  {me.get('country_id')}")
print(f"  reputation: {(me.get('seller_reputation') or {}).get('level_id','-')}")

# Paso 3: mandar refresh_token a Telegram
if TG and TGCID:
    msg = (
        f"🔑 *Nueva cuenta MELI autorizada*\n\n"
        f"*Nickname:* `{me.get('nickname')}`\n"
        f"*User ID:* `{me.get('id')}`\n"
        f"*Email:* `{me.get('email','-')}`\n\n"
        f"*Refresh Token (guarda como GH Secret):*\n"
        f"```\n{refresh_token}\n```\n\n"
        f"Pasos para vincularla al sistema:\n"
        f"1. GitHub → Settings → Secrets → Actions → New secret\n"
        f"2. Name: `MELI_REFRESH_TOKEN_<NOMBRE>`\n"
        f"3. Value: el refresh_token de arriba\n"
        f"4. Avísale al bot para que la agregue al accounts.js"
    )
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
                  timeout=15)
    print("\n📨 Refresh token enviado a Telegram")

print(f"\nREFRESH_TOKEN_BEGIN")
print(refresh_token)
print(f"REFRESH_TOKEN_END")

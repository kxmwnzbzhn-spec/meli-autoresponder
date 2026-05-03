#!/usr/bin/env python3
"""Verifica que el GOOGLE_OAUTH_REFRESH_TOKEN siga valido.
Si falla refresh, manda alerta TG inmediata.
Si esta a <2 dias de expirar, manda recordatorio.
"""
import os, requests, json
from datetime import datetime

CID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
CSEC = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
RT = os.environ["GOOGLE_OAUTH_REFRESH_TOKEN"]
TG_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT = os.environ["TELEGRAM_CHAT_ID"]

def tg(msg):
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  data={"chat_id": TG_CHAT, "parse_mode": "HTML", "text": msg},
                  timeout=20)

# Token original generado: 2026-05-02 ~17:36 CDMX = ~23:36 UTC
# Expira: ~7 dias despues = 2026-05-09 ~23:36 UTC
import time
TOKEN_CREATED_TS = 1778024160  # 2026-05-02 23:36 UTC
EXPIRES_AT = TOKEN_CREATED_TS + 7*24*3600
now = int(time.time())
days_left = (EXPIRES_AT - now) / 86400.0

# Test refresh
r = requests.post("https://oauth2.googleapis.com/token", data={
    "grant_type": "refresh_token",
    "client_id": CID, "client_secret": CSEC,
    "refresh_token": RT,
}, timeout=30)
ok = r.status_code == 200
print(f"refresh status={r.status_code} days_left={days_left:.1f}")

if not ok:
    tg(f"🚨 <b>Drive OAuth EXPIRADO</b>\n\n"
       f"El refresh_token de Drive ya no funciona.\n"
       f"Error: <code>{r.text[:200]}</code>\n\n"
       f"Necesitas re-autorizar:\n"
       f"<a href='https://accounts.google.com/o/oauth2/v2/auth?client_id={CID}&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&prompt=consent'>Re-autorizar aqui</a>\n\n"
       f"Pegame el code que te de y lo guardo.")
elif days_left < 2:
    tg(f"⏰ <b>Drive OAuth caduca pronto</b>\n\n"
       f"Te quedan <b>{days_left:.1f} dias</b> antes de que expire el token de Drive.\n\n"
       f"Re-autoriza aqui:\n"
       f"<a href='https://accounts.google.com/o/oauth2/v2/auth?client_id={CID}&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&prompt=consent'>Click aqui</a>\n\n"
       f"O publica la app en GCP para tokens permanentes.")
else:
    print(f"OK, {days_left:.1f} dias restantes")

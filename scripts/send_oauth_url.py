import os, requests, urllib.parse
CID=os.environ["MELI_APP_ID_NEW"]
REDIRECT="https://meli-webhook.elite-market-1779161651.workers.dev/oauth/callback"
URL=f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={CID}&redirect_uri={urllib.parse.quote(REDIRECT,safe=':/')}"

# Telegram
TG_BOT=os.environ["TELEGRAM_BOT_TOKEN"]; TG_CHAT=os.environ["TELEGRAM_CHAT_ID"]
msg=(
  "🔐 <b>OAuth URL para Adrián — app Asva Inventario MX</b>\n\n"
  "Mándalo tal cual a Adrián. Que clickee 'Conectar mi cuenta' / 'Autorizar'.\n"
  "Después de aprobar verá <i>'method not allowed'</i> en pantalla — eso es normal. "
  "Lo importante es que copie la URL completa de la barra del navegador (con el <code>?code=TG-...</code>) "
  "y te la pase a ti, tú me la pegas a mí.\n\n"
  f"<code>{URL}</code>"
)
r=requests.post(f"https://api.telegram.org/bot{TG_BOT}/sendMessage",
  data={"chat_id":TG_CHAT,"text":msg,"parse_mode":"HTML","disable_web_page_preview":True},timeout=10)
print(f"[TG send] HTTP {r.status_code}")
print(f"client_id length: {len(CID)}")
print(f"OAuth URL sent to TG: ok={r.status_code==200}")

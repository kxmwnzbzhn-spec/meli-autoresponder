"""Intercambia code OAuth de MELI por refresh_token y lo guarda automáticamente
como GitHub Secret en ambos repos (meli-autoresponder + elitemarket-chatbot).
Inputs (env):
  CODE              → code TG-... de MELI
  ACCOUNT_NAME      → nombre interno (ej: RAYMUNDO_MAY)
  MELI_APP_SECRET   → MELI app secret
  REPO_PAT          → PAT con secrets:write a ambos repos
  TG_TOKEN/CHAT     → Telegram para confirmar
"""
import os, requests, json, base64
from nacl import encoding, public

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
CODE = os.environ["CODE"].strip()
ACCOUNT_NAME = os.environ.get("ACCOUNT_NAME", "RAYMUNDO_MAY").strip().upper()
GH_PAT = os.environ.get("REPO_PAT") or os.environ.get("GH_TOKEN_OPS") or os.environ.get("GITHUB_TOKEN")
OWNER = "kxmwnzbzhn-spec"
REPOS = ["meli-autoresponder", "elitemarket-chatbot"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")
REDIRECT = "https://oauth.pstmn.io/v1/callback"

SECRET_NAME = f"MELI_REFRESH_TOKEN_{ACCOUNT_NAME}"

print(f"=== Auth + Save secret: {SECRET_NAME} ===")

# 1. Exchange code → token
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "authorization_code",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "code": CODE,
    "redirect_uri": REDIRECT,
}, timeout=20)
if r.status_code != 200:
    raise SystemExit(f"❌ OAuth fail: {r.text}")
j = r.json()
refresh_token = j["refresh_token"]
access_token = j["access_token"]

me = requests.get("https://api.mercadolibre.com/users/me",
                  headers={"Authorization": f"Bearer {access_token}"}, timeout=15).json()
nickname = me.get("nickname")
user_id = me.get("id")
email = me.get("email")
print(f"✅ Cuenta: {nickname} (uid {user_id}) {email}")

# 2. Encriptar y guardar como secret en cada repo
def encrypt_secret(public_key_b64: str, value: str) -> str:
    pk = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

H = {"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"}
saved_in = []
for repo in REPOS:
    print(f"\n→ {repo}")
    # Get public key
    r = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/public-key",
                     headers=H, timeout=15)
    if r.status_code != 200:
        print(f"  ❌ public-key: HTTP {r.status_code} {r.text[:200]}")
        continue
    pk_data = r.json()
    encrypted_value = encrypt_secret(pk_data["key"], refresh_token)
    body = {"encrypted_value": encrypted_value, "key_id": pk_data["key_id"]}
    # PUT secret
    r2 = requests.put(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/{SECRET_NAME}",
                      headers=H, json=body, timeout=15)
    if r2.status_code in (201, 204):
        print(f"  ✓ Secret {SECRET_NAME} guardado")
        saved_in.append(repo)
    else:
        print(f"  ❌ PUT secret: HTTP {r2.status_code} {r2.text[:200]}")

# 3. Activar cuenta en accounts.js (cambiar active: false → true)
print(f"\n→ Activando {ACCOUNT_NAME} en elitemarket-chatbot/src/accounts.js")
acc_url = f"https://api.github.com/repos/{OWNER}/elitemarket-chatbot/contents/src/accounts.js"
r = requests.get(acc_url, headers=H, timeout=15)
if r.status_code == 200:
    file_data = r.json()
    content = base64.b64decode(file_data["content"]).decode("utf-8")
    sha = file_data["sha"]
    # Buscar la línea del account (por id) y cambiar active:false → active:true (regex genérico)
    import re
    pattern = re.compile(r'(\{\s*id:\s*"' + re.escape(ACCOUNT_NAME) + r'"[^}]*?active:\s*)false', re.DOTALL)
    new_content, n = pattern.subn(r'\1true', content)
    if n == 0:
        print(f"  ⚠️  no encontré entry para id={ACCOUNT_NAME} con active:false")
    if new_content != content:
        upd_body = {
            "message": f"Activate {ACCOUNT_NAME} (secret added)",
            "content": base64.b64encode(new_content.encode()).decode(),
            "sha": sha
        }
        r3 = requests.put(acc_url, headers=H, json=upd_body, timeout=15)
        if r3.status_code in (200, 201):
            print(f"  ✓ accounts.js → active: true")
        else:
            print(f"  ❌ accounts.js update HTTP {r3.status_code} {r3.text[:200]}")
    else:
        print(f"  ⚠️  línea no encontrada (ya estaba activa o accounts.js cambió)")

# 4. Telegram confirm
if TG and TGCID:
    msg = (
        f"✅ *Cuenta {ACCOUNT_NAME} integrada*\n\n"
        f"Nickname: `{nickname}`\n"
        f"User ID: `{user_id}`\n"
        f"Email: `{email}`\n\n"
        f"Secret guardado en: {', '.join(saved_in)}\n"
        f"Estado: active=true en bot\n\n"
        f"_El bot ya la ofrece en la lista al repartidor._"
    )
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
                  timeout=15)
    print("\n📨 Confirmación enviada a Telegram")

print(f"\n{'✅' if len(saved_in) == 2 else '⚠️'} Listo. Saved in: {saved_in}")

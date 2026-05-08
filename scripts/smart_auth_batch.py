"""Procesa lote de codes OAuth: intercambia cada uno, identifica la cuenta por uid,
y guarda secret en ambos repos. Si el uid es nuevo, reporta para que el usuario decida."""
import os, requests, base64
from nacl import encoding, public

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
GH_PAT = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN")
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")
OWNER = "kxmwnzbzhn-spec"
REPOS = ["meli-autoresponder", "elitemarket-chatbot"]
REDIRECT = "https://oauth.pstmn.io/v1/callback"

# Mapeo uid → nombre interno bot (basado en accounts.js + cuentas_meli.md)
UID_TO_BOT = {
    "2681696373": "JUAN",
    "3348766821": "CLARIBEL",
    "1668713481": "ASVA",
    "3338633403": "RAYMUNDO",
    "3355056011": "DILCIE",
    "3358792306": "MILDRED",
    "3367276814": "WILBERT",
    "3009687392": "ANGEL_DAMIAN",
    "3246557656": "ASGARI",
    "3294280577": "RAYMUNDO_MAY",
}

# Codes a procesar (uno por línea, con user_id al final)
CODES = os.environ["CODES"].strip().splitlines()

def encrypt_secret(public_key_b64, value):
    pk = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pk)
    return base64.b64encode(sealed_box.encrypt(value.encode("utf-8"))).decode("utf-8")

H = {"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"}
results = []

for line in CODES:
    code = line.strip().split("code=")[-1] if "code=" in line else line.strip()
    if not code.startswith("TG-"):
        results.append((code[:30], None, None, None, "no es TG- code"))
        continue

    print(f"\n=== Code: {code[:40]}... ===")
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": APP_ID, "client_secret": APP_SECRET,
        "code": code, "redirect_uri": REDIRECT,
    }, timeout=20)

    if r.status_code != 200:
        print(f"  ❌ exchange fail: {r.text[:200]}")
        results.append((code[:30], None, None, None, f"exchange fail {r.status_code}"))
        continue

    j = r.json()
    refresh_token = j["refresh_token"]
    access_token = j["access_token"]
    me = requests.get("https://api.mercadolibre.com/users/me",
                      headers={"Authorization": f"Bearer {access_token}"}, timeout=15).json()
    uid = str(me.get("id"))
    nickname = me.get("nickname")
    email = me.get("email")
    bot_name = UID_TO_BOT.get(uid)

    print(f"  uid={uid} nick={nickname} email={email} → {bot_name or '(NO MAPPED)'}")

    if not bot_name:
        results.append((code[:30], uid, nickname, email, "uid NO MAPPED — agregar manualmente"))
        continue

    # Guardar secret en ambos repos
    secret_name = f"MELI_REFRESH_TOKEN_{bot_name}"
    saved = []
    for repo in REPOS:
        try:
            pk = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/public-key",
                              headers=H, timeout=15).json()
            enc = encrypt_secret(pk["key"], refresh_token)
            r2 = requests.put(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/{secret_name}",
                              headers=H, json={"encrypted_value": enc, "key_id": pk["key_id"]}, timeout=15)
            if r2.status_code in (201, 204):
                saved.append(repo)
                print(f"  ✓ {repo}: {secret_name}")
            else:
                print(f"  ✗ {repo}: HTTP {r2.status_code}")
        except Exception as e:
            print(f"  ✗ {repo}: {e}")

    # Si es JUAN, también guardar como MELI_REFRESH_TOKEN (legacy)
    if bot_name == "JUAN":
        for repo in REPOS:
            try:
                pk = requests.get(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/public-key",
                                  headers=H, timeout=15).json()
                enc = encrypt_secret(pk["key"], refresh_token)
                r2 = requests.put(f"https://api.github.com/repos/{OWNER}/{repo}/actions/secrets/MELI_REFRESH_TOKEN",
                                  headers=H, json={"encrypted_value": enc, "key_id": pk["key_id"]}, timeout=15)
                if r2.status_code in (201, 204):
                    print(f"  ✓ {repo}: MELI_REFRESH_TOKEN (legacy)")
            except: pass

    results.append((code[:30], uid, nickname, email, bot_name + " ✓ saved in " + ",".join(saved)))

# Reporte
print(f"\n{'='*70}\n=== RESULTADO ({len(results)} codes) ===")
for code, uid, nick, email, status in results:
    print(f"  {uid or '?':<12} {nick or '?':<25} {email or '':<32} → {status}")

if TG and TGCID:
    msg = "🔑 *Re-auth batch completado*\n\n"
    for code, uid, nick, email, status in results:
        if "saved" in status:
            msg += f"✅ `{nick}` → {status.split(' ')[0]}\n"
        else:
            msg += f"⚠️  `{nick or '?'}` (uid {uid or '?'}) → {status}\n"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg[:4000]},
                  timeout=15)

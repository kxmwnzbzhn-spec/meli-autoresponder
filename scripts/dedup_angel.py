"""Compara las cuentas ANGEL y ANGEL_DAMIAN. Si apuntan al mismo user_id,
desactiva la duplicada (ANGEL queda inactiva, ANGEL_DAMIAN activa).
"""
import os, requests, base64, re

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT_ANGEL = os.environ.get("MELI_REFRESH_TOKEN_ANGEL", "")
RT_AD = os.environ.get("MELI_REFRESH_TOKEN_ANGEL_DAMIAN", "")
GH_PAT = os.environ.get("REPO_PAT") or os.environ.get("GITHUB_TOKEN")
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

def get_user(rt, label):
    if not rt:
        print(f"  {label}: sin refresh token")
        return None
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type": "refresh_token", "client_id": APP_ID,
        "client_secret": APP_SECRET, "refresh_token": rt
    }, timeout=20).json()
    at = r.get("access_token")
    if not at:
        print(f"  {label}: auth fail {r}")
        return None
    me = requests.get("https://api.mercadolibre.com/users/me",
                      headers={"Authorization": f"Bearer {at}"}, timeout=15).json()
    print(f"  {label}: uid={me.get('id')} nick={me.get('nickname')} email={me.get('email')}")
    return me

print("=== Comparando ANGEL vs ANGEL_DAMIAN ===")
ang = get_user(RT_ANGEL, "ANGEL")
ad = get_user(RT_AD, "ANGEL_DAMIAN")

if not ang or not ad:
    raise SystemExit("❌ Faltan datos")

if ang["id"] == ad["id"]:
    print(f"\n✅ Confirmado: AMBAS apuntan al mismo user_id {ang['id']}")
    print(f"  → Desactivando ANGEL (duplicada). Queda solo ANGEL_DAMIAN.")

    # Update accounts.js: ANGEL active:true → false
    H = {"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"}
    url = "https://api.github.com/repos/kxmwnzbzhn-spec/elitemarket-chatbot/contents/src/accounts.js"
    r = requests.get(url, headers=H, timeout=15)
    file_data = r.json()
    content = base64.b64decode(file_data["content"]).decode("utf-8")
    sha = file_data["sha"]

    # ANGEL: cambiar active:true → active:false
    pattern = re.compile(r'(\{\s*id:\s*"ANGEL"[^}]*?active:\s*)true', re.DOTALL)
    new_content, n = pattern.subn(r'\1false', content)
    if n == 0:
        print("  ⚠️  no encontré ANGEL active:true para desactivar")
    else:
        body = {
            "message": "Disable ANGEL (duplicate of ANGEL_DAMIAN, same user_id)",
            "content": base64.b64encode(new_content.encode()).decode(),
            "sha": sha
        }
        r2 = requests.put(url, headers=H, json=body, timeout=15)
        if r2.status_code in (200, 201):
            print("  ✓ accounts.js → ANGEL active:false")
        else:
            print(f"  ❌ HTTP {r2.status_code} {r2.text[:200]}")

    # Telegram
    if TG and TGCID:
        msg = f"♻️ *Dedup ANGEL → ANGEL_DAMIAN*\n\nMismo user_id: `{ang['id']}`\n\nANGEL desactivada. ANGEL_DAMIAN queda como única."
        requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                      data={"chat_id": TGCID, "parse_mode": "Markdown", "text": msg},
                      timeout=10)
else:
    print(f"\nℹ️  Son cuentas DISTINTAS:")
    print(f"  ANGEL:        uid {ang['id']} ({ang.get('nickname')})")
    print(f"  ANGEL_DAMIAN: uid {ad['id']} ({ad.get('nickname')})")
    print(f"  → Las dos quedan activas.")

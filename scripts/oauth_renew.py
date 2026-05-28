"""Renueva GOOGLE_OAUTH_REFRESH_TOKEN via Device Flow.
Imprime un user_code y una URL para que el dueño autorice.
Hace polling hasta 10 min. Cuando recibe el nuevo refresh_token,
lo escribe al secret GOOGLE_OAUTH_REFRESH_TOKEN del repo (no lo imprime).
"""
import os, sys, time, json, requests, base64

CID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GH_TOKEN = os.environ["GH_PAT"]
REPO = os.environ.get("REPO","kxmwnzbzhn-spec/meli-autoresponder")
SCOPE = "https://www.googleapis.com/auth/drive"

print("=== Solicitando device code ===", flush=True)
r = requests.post("https://oauth2.googleapis.com/device/code",
                  data={"client_id": CID, "scope": SCOPE}, timeout=30)
r.raise_for_status()
dc = r.json()
print(f"\n  Abre esta URL en tu navegador:")
print(f"    >>> {dc['verification_url']} <<<")
print(f"\n  Y captura este código:")
print(f"    >>> {dc['user_code']} <<<")
print(f"\n  (expira en {dc['expires_in']}s, polling cada {dc.get('interval',5)}s)\n", flush=True)

interval = dc.get("interval", 5)
deadline = time.time() + dc["expires_in"]
device_code = dc["device_code"]
CSEC = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]

new_rt = None
while time.time() < deadline:
    time.sleep(interval)
    tr = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": CID, "client_secret": CSEC,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }, timeout=30)
    j = tr.json()
    err = j.get("error")
    if err == "authorization_pending":
        print(".", end="", flush=True); continue
    if err == "slow_down":
        interval += 5; print("(slow_down)", end="", flush=True); continue
    if err:
        print(f"\n  ERROR de Google: {err} — {j.get('error_description','')}")
        sys.exit(1)
    new_rt = j.get("refresh_token")
    if new_rt:
        print("\n  ✅ AUTORIZADO — refresh_token recibido (no se muestra aquí)")
        break
    print(f"\n  RESP inesperada: {j}")
    sys.exit(1)

if not new_rt:
    print("\n  TIMEOUT — no se autorizó a tiempo")
    sys.exit(1)

# Subir al secret usando PyNaCl
print("=== Guardando en secret GOOGLE_OAUTH_REFRESH_TOKEN ===", flush=True)
from nacl import encoding, public
pk = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
                  headers={"Authorization":f"Bearer {GH_TOKEN}"}, timeout=30).json()
key_id = pk["key_id"]
pub = public.PublicKey(pk["key"].encode("utf-8"), encoding.Base64Encoder())
encrypted = base64.b64encode(public.SealedBox(pub).encrypt(new_rt.encode("utf-8"))).decode("utf-8")
put = requests.put(
    f"https://api.github.com/repos/{REPO}/actions/secrets/GOOGLE_OAUTH_REFRESH_TOKEN",
    headers={"Authorization":f"Bearer {GH_TOKEN}","Accept":"application/vnd.github+json"},
    json={"encrypted_value": encrypted, "key_id": key_id}, timeout=30)
put.raise_for_status()
print("  ✅ Secret actualizado")

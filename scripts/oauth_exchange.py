"""Intercambia un authorization code por un refresh_token y lo guarda al secret."""
import os, sys, json, requests, base64

CODE = os.environ["AUTH_CODE"]
CID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
CSEC = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GH_TOKEN = os.environ["GH_PAT"]
REPO = os.environ.get("REPO", "kxmwnzbzhn-spec/meli-autoresponder")

print("=== Intercambiando code por refresh_token ===", flush=True)
r = requests.post("https://oauth2.googleapis.com/token", data={
    "code": CODE,
    "client_id": CID,
    "client_secret": CSEC,
    "redirect_uri": "http://localhost",
    "grant_type": "authorization_code",
}, timeout=30)
if r.status_code != 200:
    print(f"  FAIL HTTP {r.status_code}: {r.text[:300]}")
    sys.exit(1)
j = r.json()
new_rt = j.get("refresh_token")
if not new_rt:
    print(f"  No vino refresh_token. Respuesta: {json.dumps({k:('***' if k=='access_token' else v) for k,v in j.items()})}")
    sys.exit(1)
print("  ✅ refresh_token recibido (no se imprime)")

# Test que el token funcione antes de guardarlo
print("=== Validando token nuevo ===", flush=True)
v = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": CSEC,
    "refresh_token": new_rt, "grant_type": "refresh_token",
}, timeout=30)
if v.status_code != 200:
    print(f"  FAIL validate: {v.status_code} {v.text[:200]}")
    sys.exit(1)
print("  ✅ valida correctamente")

# Subir al secret
print("=== Guardando en secret GOOGLE_OAUTH_REFRESH_TOKEN ===", flush=True)
from nacl import encoding, public
pk = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
                  headers={"Authorization": f"Bearer {GH_TOKEN}"}, timeout=30).json()
key_id = pk["key_id"]
pub = public.PublicKey(pk["key"].encode("utf-8"), encoding.Base64Encoder())
encrypted = base64.b64encode(public.SealedBox(pub).encrypt(new_rt.encode("utf-8"))).decode("utf-8")
put = requests.put(
    f"https://api.github.com/repos/{REPO}/actions/secrets/GOOGLE_OAUTH_REFRESH_TOKEN",
    headers={"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"},
    json={"encrypted_value": encrypted, "key_id": key_id}, timeout=30)
if put.status_code not in (201, 204):
    print(f"  FAIL put: {put.status_code} {put.text[:200]}")
    sys.exit(1)
print("  ✅ Secret actualizado")

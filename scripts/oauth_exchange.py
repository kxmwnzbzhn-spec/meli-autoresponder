"""Intercambia un authorization code por un refresh_token y lo guarda al secret.
Prueba con varios PATs hasta encontrar uno con scope para escribir secrets."""
import os, sys, json, requests, base64

CODE = os.environ["AUTH_CODE"]
CID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
CSEC = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
REPO = os.environ.get("REPO", "kxmwnzbzhn-spec/meli-autoresponder")

print("=== Intercambiando code por refresh_token ===", flush=True)
r = requests.post("https://oauth2.googleapis.com/token", data={
    "code": CODE, "client_id": CID, "client_secret": CSEC,
    "redirect_uri": "http://localhost", "grant_type": "authorization_code",
}, timeout=30)
if r.status_code != 200:
    print(f"  FAIL HTTP {r.status_code}: {r.text[:300]}")
    sys.exit(1)
new_rt = r.json().get("refresh_token")
if not new_rt:
    print(f"  Sin refresh_token. Resp: {r.json()}")
    sys.exit(1)
print("  ✅ refresh_token recibido")

# Validate
v = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CID, "client_secret": CSEC,
    "refresh_token": new_rt, "grant_type": "refresh_token",
}, timeout=30)
if v.status_code != 200:
    print(f"  FAIL validate: {v.status_code} {v.text[:200]}"); sys.exit(1)
print("  ✅ valida correctamente")

# Try each PAT
print("=== Guardando en secret GOOGLE_OAUTH_REFRESH_TOKEN ===", flush=True)
from nacl import encoding, public
pats = []
for nm in ("GH_PAT", "REPO_PAT"):
    v = os.environ.get(nm, "").strip()
    if v: pats.append((nm, v))
ok = False
for nm, tok in pats:
    print(f"  intentando con {nm} ...", flush=True)
    pk_r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key",
                        headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    if pk_r.status_code != 200:
        print(f"    public-key {pk_r.status_code}: {pk_r.text[:200]}"); continue
    pk = pk_r.json()
    if "key_id" not in pk:
        print(f"    sin key_id: {pk}"); continue
    pub = public.PublicKey(pk["key"].encode("utf-8"), encoding.Base64Encoder())
    enc = base64.b64encode(public.SealedBox(pub).encrypt(new_rt.encode("utf-8"))).decode("utf-8")
    put = requests.put(
        f"https://api.github.com/repos/{REPO}/actions/secrets/GOOGLE_OAUTH_REFRESH_TOKEN",
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": enc, "key_id": pk["key_id"]}, timeout=30)
    if put.status_code in (201, 204):
        print(f"  ✅ Secret actualizado con {nm}"); ok = True; break
    print(f"    put {put.status_code}: {put.text[:200]}")
if not ok:
    print("  ❌ Ningún PAT funcionó")
    sys.exit(1)

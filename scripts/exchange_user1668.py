import os, requests, json, sys
from base64 import b64encode
try:
    from nacl import encoding, public
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "-q"])
    from nacl import encoding, public

AUTH_CODE = "TG-6a087e152e62f700016abb6b-1668713481"

# Step 1: Exchange auth code for tokens
print("Step 1: Intercambiando authorization code con Meli...")
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "authorization_code",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "code": AUTH_CODE,
    "redirect_uri": "https://oauth.pstmn.io/v1/callback"
}, timeout=20)

if r.status_code != 200:
    print(f"FAIL exchange: HTTP {r.status_code} - {r.text[:300]}")
    sys.exit(1)

tokens = r.json()
access = tokens["access_token"]
refresh = tokens["refresh_token"]
user_id = tokens["user_id"]
print(f"  ✓ Tokens received. user_id: {user_id}")
print(f"  ✓ access_token length: {len(access)} (no se imprime el valor)")
print(f"  ✓ refresh_token length: {len(refresh)} (no se imprime el valor)")

# Step 2: Validate by hitting /users/me
print("\nStep 2: Validando acceso con /users/me...")
h = {"Authorization": f"Bearer {access}"}
u = requests.get("https://api.mercadolibre.com/users/me", headers=h, timeout=15).json()
print(f"  nickname: {u.get('nickname')}")
print(f"  status:   {u.get('status', {}).get('site_status')}")
print(f"  rep level: {u.get('seller_reputation', {}).get('level_id')}")
print(f"  trans completed: {u.get('seller_reputation', {}).get('transactions', {}).get('completed')}")
print(f"  country: {u.get('country_id')}")

# Step 3: Save refresh_token as GH Secret (no print!)
print("\nStep 3: Guardando refresh_token como GH Secret MELI_REFRESH_TOKEN_USER1668...")
GH_TOKEN = os.environ["GH_TOKEN_PAT"]
H = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}
OWNER = "kxmwnzbzhn-spec"
REPO = "meli-autoresponder"

pk_data = requests.get(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/public-key", headers=H, timeout=10).json()
pk = public.PublicKey(pk_data["key"].encode("utf-8"), encoding.Base64Encoder())
encrypted = b64encode(public.SealedBox(pk).encrypt(refresh.encode("utf-8"))).decode("utf-8")
r = requests.put(
    f"https://api.github.com/repos/{OWNER}/{REPO}/actions/secrets/MELI_REFRESH_TOKEN_USER1668",
    headers=H, json={"encrypted_value": encrypted, "key_id": pk_data["key_id"]}, timeout=10
)
print(f"  PUT secret HTTP {r.status_code} {'✓ STORED' if r.status_code in (201,204) else '✗ FAILED'}")

# Step 4: Cuántos items activos tiene
print("\nStep 4: Items activos de la cuenta...")
ids = []; offset = 0
while True:
    j = requests.get(f"https://api.mercadolibre.com/users/{user_id}/items/search?status=active&limit=50&offset={offset}", headers=h, timeout=20).json()
    res = j.get("results", [])
    if not res: break
    ids.extend(res)
    if len(res) < 50: break
    offset += 50
print(f"  Total items activos: {len(ids)}")

# Step 5: Verificar MLMU3924350150
print("\nStep 5: Buscando listing del producto 35W Azul (MLMU3924350150)...")
for i in range(0, len(ids), 20):
    batch = ids[i:i+20]
    r = requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}&attributes=id,title,price,available_quantity,sold_quantity,user_product_id,permalink", headers=h, timeout=20).json()
    for it in r:
        if it.get("code") == 200:
            b = it["body"]
            if b.get("user_product_id") == "MLMU3924350150":
                print(f"\n  ★ MATCH ENCONTRADO ★")
                print(f"    MLM ID:    {b['id']}")
                print(f"    Title:     {b.get('title')}")
                print(f"    Price:     ${b.get('price')}")
                print(f"    Stock:     {b.get('available_quantity')}")
                print(f"    Vendidas:  {b.get('sold_quantity')}")
                print(f"    URL:       {b.get('permalink')}")

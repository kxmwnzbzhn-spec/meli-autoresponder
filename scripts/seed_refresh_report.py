"""
Regenera (refresh) los refresh_tokens de las 7 cuentas activas contra la app
2008666770714005 e imprime los valores frescos para sembrar la tabla meli_tokens
del ERP. Imprime también user_id (via /users/me) para verificar el mapeo.

NO escribe en disco. Solo imprime entre marcadores SEED_BEGIN / SEED_END.
"""
import os, json, requests

APP_ID  = os.environ.get("MELI_APP_ID", "").strip()
APP_SEC = os.environ.get("MELI_APP_SECRET", "").strip()

# Display name -> env var del secret (las 7 que maneja el ERP)
ACCS = [
    ("WILBERT",  "MELI_REFRESH_TOKEN_WILBERT"),
    ("YIRIAM",   "MELI_REFRESH_TOKEN_YC_NEW"),
    ("JUAN",     "MELI_REFRESH_TOKEN_JUAN"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA",     "MELI_REFRESH_TOKEN_ASVA"),
    ("BREN",     "MELI_REFRESH_TOKEN_BREN"),
]

print(f"APP_ID en uso: {APP_ID}")
print(f"APP_SECRET len: {len(APP_SEC)}")
print("===SEED_BEGIN===")

for name, env in ACCS:
    rt = (os.environ.get(env) or "").strip()
    if not rt:
        print(f"{name}: ERROR secret_vacio ({env})")
        continue
    try:
        r = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": APP_ID,
                "client_secret": APP_SEC,
                "refresh_token": rt,
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
        j = r.json()
    except Exception as e:
        print(f"{name}: ERROR exc {type(e).__name__}: {str(e)[:120]}")
        continue

    if r.status_code != 200 or "access_token" not in j:
        print(f"{name}: ERROR http={r.status_code} body={json.dumps(j)[:180]}")
        continue

    new_rt = j.get("refresh_token") or rt
    at = j["access_token"]

    # Verificar liveness + user_id
    uid = "?"
    try:
        me = requests.get(
            "https://api.mercadolibre.com/users/me",
            headers={"Authorization": f"Bearer {at}"},
            timeout=15,
        )
        if me.status_code == 200:
            uid = str(me.json().get("id"))
        else:
            uid = f"me_http={me.status_code}"
    except Exception as e:
        uid = f"me_exc={type(e).__name__}"

    print(f"{name}: {new_rt}  | user_id={uid}")

print("===SEED_END===")

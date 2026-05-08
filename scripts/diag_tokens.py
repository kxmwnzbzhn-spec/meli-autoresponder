"""Diagnóstico de tokens MELI: para cada cuenta dice si el refresh existe,
qué longitud tiene, y qué error devuelve /oauth/token."""
import os, json, requests
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
ACCS_ENVS=[
    ("Juan","MELI_REFRESH_TOKEN_JUAN"),
    ("JuanFallback","MELI_REFRESH_TOKEN"),
    ("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),
    ("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),
    ("Asva","MELI_REFRESH_TOKEN_ASVA"),
    ("Mildred","MELI_REFRESH_TOKEN_MILDRED"),
    ("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),
    ("Bren","MELI_REFRESH_TOKEN_BREN"),
    ("Yc_New","MELI_REFRESH_TOKEN_YC_NEW"),
]
print(f"APP_SECRET length: {len(APP_SECRET) if APP_SECRET else 0}")
print()
for nombre, env_name in ACCS_ENVS:
    rt = os.environ.get(env_name) or ""
    if not rt:
        print(f"[{nombre:14}] {env_name:32} VACÍO o no seteado")
        continue
    print(f"[{nombre:14}] {env_name:32} len={len(rt)}  prefix={rt[:10]}...")
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
                          data={"grant_type":"refresh_token",
                                "client_id":APP_ID,
                                "client_secret":APP_SECRET,
                                "refresh_token":rt}, timeout=10)
        print(f"                 status={r.status_code}")
        try:
            j = r.json()
            if "access_token" in j:
                print(f"                 OK  access={j['access_token'][:15]}...  new_refresh={(j.get('refresh_token') or '')[:15]}...")
            else:
                print(f"                 ERR body={json.dumps(j)[:200]}")
        except:
            print(f"                 body raw={r.text[:200]}")
    except Exception as e:
        print(f"                 EXC {type(e).__name__}: {str(e)[:100]}")
    print()

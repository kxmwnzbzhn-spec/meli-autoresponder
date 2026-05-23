import os, requests
IID = "MLM2950790167"
CID = os.environ["MELI_APP_ID"]; CS = os.environ["MELI_APP_SECRET"]
RT  = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}, timeout=20).json()
AT = r["access_token"]
H = {"Authorization": f"Bearer {AT}", "Content-Type":"application/json"}

it = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H, timeout=20).json()
if "error" in it and not it.get("id"):
    print(f"NOT_FOUND {IID}: {it.get('error')} / {it.get('message')}")
    raise SystemExit(0)
print(f"FOUND {IID}: title={it.get('title')!r} status={it.get('status')} seller={it.get('seller_id')}")

# 1) pausar si está activo (requisito para poder cerrar)
if it.get("status") == "active":
    rp = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={"status":"paused"}, timeout=20)
    print(f"  pause: {rp.status_code}")

# 2) cerrar
rc = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={"status":"closed"}, timeout=20)
print(f"  close: {rc.status_code} {('' if rc.status_code==200 else rc.text[:200])}")

# 3) eliminar
rd = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={"deleted":"true"}, timeout=20)
print(f"  delete: {rd.status_code} {('' if rd.status_code==200 else rd.text[:200])}")

fin = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H, timeout=20).json()
print(f"FINAL status={fin.get('status')} deleted={fin.get('deleted')}")
print("OK_DONE")

import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Todas Go 4 de Claribel
IDS=["MLM5224043294","MLM2880882839","MLM5223660600","MLM2880903119","MLM2880882857"]

# Primero revisar estado de envio
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    sh=it.get("shipping",{})
    fs=sh.get("free_shipping")
    mode=sh.get("mode")
    print(f"{iid} | {it.get('title')[:50]} | mode={mode} free_shipping={fs}")

print("\n=== Forzando envio gratis ===")
for iid in IDS:
    body={"shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]}}
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=20)
    print(f"{iid}: {r.status_code} {r.text[:150] if r.status_code>=400 else 'OK'}")
    time.sleep(0.5)

# Verificar
print("\n=== Verificando ===")
for iid in IDS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    sh=it.get("shipping",{})
    print(f"{iid} | free_shipping={sh.get('free_shipping')} mode={sh.get('mode')}")

import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"user_id: {USER_ID}")

CLAIM_ID="2000012579902645"
# Listar claims activos del usuario
print("\n=== LISTAR CLAIMS ===")
for path in [f"/post-purchase/v1/claims/search?stage=claim&status=opened",
             f"/post-purchase/v1/claims/search",
             f"/v1/claims/search?resource=order",
             f"/post-purchase/v2/claims/search"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  {path}: {rp.status_code}")
    if rp.status_code==200:
        j=rp.json()
        print(f"    paging={j.get('paging')} count={len(j.get('data') or j.get('results') or [])}")
        for c in (j.get("data") or j.get("results") or [])[:5]:
            print(f"      id={c.get('id')} stage={c.get('stage')} status={c.get('status')} resource_id={c.get('resource_id')}")
        break

# Intentar GET al claim con diferentes formatos
print(f"\n=== GET CLAIM {CLAIM_ID} ===")
for path in [f"/post-purchase/v1/claims/{CLAIM_ID}",
             f"/post-purchase/v2/claims/{CLAIM_ID}",
             f"/post-purchase/v1/claims/{CLAIM_ID}/messages",
             f"/v1/claims/{CLAIM_ID}",
             f"/mediations/{CLAIM_ID}",
             f"/mediations/{CLAIM_ID}/messages"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    if rp.status_code!=404:
        print(f"  {path}: {rp.status_code}")
        print(f"    {rp.text[:1500]}")

# Enviar mensaje al claim (intentar varios patrones)
MSG="Hola. Confirmo que el producto enviado es ORIGINAL JBL. En la descripcion de la publicacion se indica claramente que este modelo NO es compatible con la app movil de la marca - funciona como bocina Bluetooth estandar. Quedo atento a cualquier evidencia de defecto para coordinar garantia. Gracias."

print("\n=== ENVIAR MENSAJE ===")
for path in [f"/post-purchase/v1/claims/{CLAIM_ID}/messages",
             f"/post-purchase/v2/claims/{CLAIM_ID}/messages",
             f"/claims/{CLAIM_ID}/messages",
             f"/mediations/{CLAIM_ID}/messages",
             f"/post-purchase/v1/claims/{CLAIM_ID}/claim_messages"]:
    for body in [{"message":MSG},{"text":MSG},{"message":{"message":MSG}}]:
        rp=requests.post(f"https://api.mercadolibre.com{path}",headers=H,json=body,timeout=15)
        if rp.status_code!=404:
            print(f"  {path}: {rp.status_code} {rp.text[:300]}")

import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

CLAIM_ID="2000012579902645"

# Obtener detalle del reclamo
print(f"=== CLAIM {CLAIM_ID} ===")
for path in [f"/post-purchase/v2/claims/{CLAIM_ID}",
             f"/post-purchase/v1/claims/{CLAIM_ID}",
             f"/v1/claims/{CLAIM_ID}",
             f"/claims/{CLAIM_ID}"]:
    rp=requests.get(f"https://api.mercadolibre.com{path}",headers=H,timeout=15)
    print(f"  GET {path}: {rp.status_code}")
    if rp.status_code==200:
        d=rp.json()
        print(json.dumps(d,ensure_ascii=False)[:2500])
        CLAIM=d
        break
else:
    print("!!! no encontrado")
    exit(1)

# Mensaje de respuesta
MSG=("Hola, buen dia. Muchas gracias por su compra.\n\n"
     "Confirmo que el producto enviado es ORIGINAL JBL. "
     "En la descripcion de la publicacion se indica claramente que este modelo NO es compatible con la aplicacion movil de la marca.\n\n"
     "Le comparto la referencia exacta del punto de la descripcion:\n"
     "\"NO incluye compatibilidad con app movil. Funciona como bocina Bluetooth estandar.\"\n\n"
     "Quedo atento a cualquier duda tecnica o evidencia de defecto, y en ese caso con gusto coordinamos el proceso de garantia.\n\n"
     "Gracias por su comprension.")

# Intentar enviar mensaje al claim
print("\n=== RESPONDER ===")
body={"message":MSG}
for path in [f"/post-purchase/v2/claims/{CLAIM_ID}/messages",
             f"/post-purchase/v1/claims/{CLAIM_ID}/messages",
             f"/claims/{CLAIM_ID}/messages"]:
    rp=requests.post(f"https://api.mercadolibre.com{path}",headers=H,json=body,timeout=20)
    print(f"  POST {path}: {rp.status_code}")
    print(f"    {rp.text[:500]}")
    if rp.status_code in (200,201):
        break

# Si el claim esta en messages, buscar el resource_id / message thread
# MELI usa ahora "/messages/claim/{claim_id}/packs/{pack_id}/sellers/{seller_id}"
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"\nuser_id: {USER_ID}")

# Buscar el pack_id del claim
if "resource_id" in CLAIM:
    pack_id=CLAIM["resource_id"]
    order_id=CLAIM.get("resource_id")
    print(f"pack/order id: {pack_id}")
    # Intentar mensajeria post-venta
    for path in [f"/messages/packs/{pack_id}/sellers/{USER_ID}",
                 f"/messages/action_guide/packs/{pack_id}/option"]:
        rp=requests.post(f"https://api.mercadolibre.com{path}",headers=H,json={"from":{"user_id":str(USER_ID)},"text":MSG},timeout=15)
        print(f"  {path}: {rp.status_code} {rp.text[:300]}")

import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]
print(f"user_id: {USER_ID} nickname: {me.get('nickname')}")

CLAIM_ID="2000012579902645"

# 1) Obtener detalle del claim
print(f"\n=== GET CLAIM {CLAIM_ID} ===")
d=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}",headers=H,timeout=15).json()
print(json.dumps(d,ensure_ascii=False,indent=2)[:3000])
RESOURCE_ID=d.get("resource_id")
PARENT_ID=d.get("parent_id")
STAGE=d.get("stage")
STATUS=d.get("status")
TYPE=d.get("type")

# 2) Obtener mensajes existentes
print(f"\n=== MESSAGES ===")
mh=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",headers=H,timeout=15)
print(f"  status: {mh.status_code}")
msgs=mh.json() if mh.status_code==200 else {}
print(f"  count: {len(msgs) if isinstance(msgs,list) else 'N/A'}")
if isinstance(msgs,list):
    for m in msgs[-5:]:
        print(f"    from={m.get('sender_role')} at={m.get('date_created')} text={str(m.get('message'))[:200]}")
elif isinstance(msgs,dict):
    print(json.dumps(msgs,ensure_ascii=False)[:800])

# 3) Respuesta blindada
MSG=("Hola, buen dia. Agradezco su compra y comprension.\n\n"
     "Confirmo que el producto enviado es 100% ORIGINAL JBL, adquirido por canales autorizados. "
     "En la descripcion de la publicacion se indica claramente que este modelo NO es compatible con la app movil de la marca (Portable by JBL), ya que es un modelo que funciona como bocina Bluetooth estandar y no incorpora conectividad con aplicacion.\n\n"
     "Le invito a revisar nuevamente la descripcion de la publicacion donde se especifica este punto antes de la compra.\n\n"
     "Si presenta cualquier defecto de fabricacion comprobable con video, con gusto coordinamos el proceso de garantia correspondiente.\n\n"
     "Quedo atento.\nGracias.")

# 4) Intentar enviar mensaje via multiples endpoints
print(f"\n=== SEND MESSAGE ===")
sent=False
# A) POST a /post-purchase/v1/claims/{id}/messages
rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
    headers=H,json={"message":MSG},timeout=15)
print(f"  A) POST claims/{CLAIM_ID}/messages: {rp.status_code}")
print(f"    {rp.text[:400]}")
if rp.status_code in (200,201): sent=True

# B) POST a /v1/claims/{id}/answer
if not sent:
    rp=requests.post(f"https://api.mercadolibre.com/v1/claims/{CLAIM_ID}/answer",
        headers=H,json={"answer":MSG,"response":MSG},timeout=15)
    print(f"  B) POST v1/claims/{CLAIM_ID}/answer: {rp.status_code}")
    print(f"    {rp.text[:400]}")
    if rp.status_code in (200,201): sent=True

# C) POST a /post-purchase/v1/claims/{id}/actions/expected
if not sent:
    actions=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/expected_resolutions",
        headers=H,timeout=15)
    print(f"  C) expected_resolutions: {actions.status_code}")
    print(f"    {actions.text[:500]}")

# D) Messaging post-venta (si hay pack_id / order)
if RESOURCE_ID:
    print(f"\n=== PACK MESSAGING (resource={RESOURCE_ID}) ===")
    # obtener order info para conseguir pack_id
    o=requests.get(f"https://api.mercadolibre.com/orders/{RESOURCE_ID}",headers=H,timeout=15).json()
    pack_id=o.get("pack_id") or RESOURCE_ID
    buyer_id=(o.get("buyer") or {}).get("id")
    print(f"  pack_id={pack_id} buyer={buyer_id}")
    rp=requests.post(f"https://api.mercadolibre.com/messages/packs/{pack_id}/sellers/{USER_ID}",
        headers=H,
        json={"from":{"user_id":str(USER_ID)},
              "to":{"user_id":str(buyer_id)} if buyer_id else {},
              "text":MSG},timeout=15)
    print(f"  messages pack: {rp.status_code} {rp.text[:400]}")
    if rp.status_code in (200,201): sent=True

print(f"\n=== RESULT: sent={sent} ===")

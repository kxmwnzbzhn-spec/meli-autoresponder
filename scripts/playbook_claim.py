import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

CLAIM_ID="5501400150"

# 1) Traer detalles del claim
c=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}",headers=H,timeout=15).json()
print("=== CLAIM DETAILS ===")
print(f"id: {c.get('id')}")
print(f"reason: {c.get('reason_id')}")
print(f"status: {c.get('status')}/{c.get('stage')}")
print(f"type: {c.get('type')}")
print(f"resource_id: {c.get('resource_id')}")
print(f"resource: {c.get('resource')}")
print(f"fulfilled: {c.get('fulfilled')}")
print(f"players:")
for p in c.get("players",[]):
    print(f"  {p.get('role')} user={p.get('user_id')} actions={[a.get('action') for a in p.get('available_actions',[])]}")

# 2) Traer mensajes previos
m=requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",headers=H,timeout=15).json()
print(f"\n=== MENSAJES ({len(m.get('messages',[])) if isinstance(m,dict) else '?'}) ===")
if isinstance(m,dict):
    for msg in m.get("messages",[])[:10]:
        print(f"  {msg.get('date_created','')[:19]} | {msg.get('sender_role')}: {msg.get('message','')[:200]}")
else:
    print(m)

# 3) Traer orden asociada
rid=c.get("resource_id")
if rid:
    o=requests.get(f"https://api.mercadolibre.com/orders/{rid}",headers=H,timeout=15).json()
    print(f"\n=== ORDER {rid} ===")
    print(f"total: ${o.get('total_amount')}")
    items=o.get("order_items") or []
    for it in items:
        print(f"  item: {(it.get('item') or {}).get('title','')[:60]}")
    print(f"buyer: {(o.get('buyer') or {}).get('nickname')} id={(o.get('buyer') or {}).get('id')}")

# 4) Enviar mensaje al comprador (mandatory action)
MENSAJE="""Hola! Lamento mucho el inconveniente con tu compra.

Queremos resolver esto de la mejor forma posible. Por favor cuentanos:
1. ¿Que situacion estas experimentando con el producto?
2. ¿El producto llego correctamente o presenta algun defecto de funcionamiento?
3. ¿Quieres devolucion, reemplazo, o reembolso?

Responderemos en menos de 2 horas habiles con la mejor solucion.

Si el producto tiene defecto de funcionamiento (no enciende, no pairea, etc) procederemos con el reemplazo o reembolso inmediato.

Saludos cordiales,
Equipo de Soporte Sonix Mx"""

r=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",headers=H,json={"message":MENSAJE},timeout=20)
print(f"\n=== ENVIO MENSAJE ===")
print(f"{r.status_code}: {r.text[:500]}")

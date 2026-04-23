import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]

PACK_ID="2000012579902645"
BUYER_ID="21502445"
CLAIM_ID="5501400150"

MSGS=[
    ("Buen dia. Le transcribo literalmente el aviso visible en la publicacion ANTES de su compra: "
     "\"IMPORTANTE: este modelo NO es compatible con la aplicacion JBL Portable ni con Auracast; su operacion es Bluetooth estandar, un dispositivo a la vez.\" "
     "La no compatibilidad con la app no es defecto, es una caracteristica tecnica informada. Al comprar usted acepto estos terminos."),
    ("Sobre autenticidad: la bocina es JBL Go 4 original, caja sellada, numero de serie y codigo de barras oficiales. "
     "Puede verificar en jbl.com.mx (seccion verificar producto), llamar a JBL Mexico 01-800-005-5252, o peritaje tecnico Harman. "
     "Si cualquier canal oficial determina que no es autentica, procedere con reembolso total."),
    ("Ofrezco 3 opciones para cerrar: A) Si la bocina funciona por Bluetooth, caso resuelto (no hay defecto). "
     "B) Si hay defecto real con video, aplica garantia 30 dias. "
     "C) Devolucion voluntaria a sus expensas, reembolso tras verificar estado y accesorios completos. "
     "Solicito a Mercado Libre cerrar el reclamo: no hay defecto, no hay inautenticidad, el aviso fue publicado. Gracias."),
]

# Intentar multiples endpoints para messaging
print(f"=== ENVIAR MENSAJES ===")
sent=0
for i,msg in enumerate(MSGS,1):
    print(f"\n--- MSG {i} ---")
    success=False
    
    # 1) Packs messaging (post-venta)
    body={"from":{"user_id":str(USER_ID)},"to":{"user_id":str(BUYER_ID)},"text":msg}
    rp=requests.post(f"https://api.mercadolibre.com/messages/packs/{PACK_ID}/sellers/{USER_ID}",
        headers=H,json=body,timeout=20)
    print(f"  packs: {rp.status_code}  {rp.text[:250]}")
    if rp.status_code in (200,201):
        success=True
    
    # 2) Action guide packs
    if not success:
        rp=requests.post(f"https://api.mercadolibre.com/messages/action_guide/packs/{PACK_ID}/option",
            headers=H,json={"option_id":"SEND_MESSAGE","text":msg},timeout=20)
        print(f"  action_guide: {rp.status_code} {rp.text[:200]}")
        if rp.status_code in (200,201): success=True
    
    # 3) PUT en lugar de POST al claim messages
    if not success:
        rp=requests.put(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
            headers=H,json={"message":msg},timeout=20)
        print(f"  PUT claim msg: {rp.status_code} {rp.text[:200]}")
        if rp.status_code in (200,201): success=True
    
    # 4) Claim messages endpoint v2
    if not success:
        rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v2/claims/{CLAIM_ID}/messages",
            headers=H,json={"message":msg},timeout=20)
        print(f"  v2 claim msg: {rp.status_code} {rp.text[:200]}")
        if rp.status_code in (200,201): success=True
    
    # 5) Mediation
    if not success:
        rp=requests.post(f"https://api.mercadolibre.com/mediations/{CLAIM_ID}/messages",
            headers=H,json={"message":msg},timeout=20)
        print(f"  mediation msg: {rp.status_code} {rp.text[:200]}")
        if rp.status_code in (200,201): success=True
    
    if success:
        sent+=1
        time.sleep(6)
    else:
        print(f"  !! MSG {i} no enviado")
        break

print(f"\n=== TOTAL enviados: {sent}/{len(MSGS)} ===")

import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID=me["id"]

CLAIM_ID="5501400150"

# 3 mensajes escalonados de defensa
MSGS=[
    # 1) Cita textual de la descripción — defensa principal
    ("Estimado comprador, le transcribo literalmente el aviso que aparecia en la descripcion de la publicacion antes de su compra:\n\n"
     "\"IMPORTANTE: este modelo NO es compatible con la aplicacion JBL Portable ni con Auracast; su operacion es Bluetooth estandar, un dispositivo a la vez.\"\n\n"
     "Este texto estuvo publicado y visible al momento de confirmar su compra. Al completar el pago usted acepto estas condiciones. "
     "La no compatibilidad con la app NO constituye un defecto ni un incumplimiento - es una caracteristica tecnica del modelo que fue claramente informada. "
     "Por favor revise nuevamente la publicacion donde se reitera este punto en mayusculas."),
    
    # 2) Validación de originalidad del producto
    ("Respecto a la originalidad del producto: la bocina enviada es JBL Go 4 genuina, con caja original sellada, "
     "numero de serie verificable en el codigo SN impreso en la caja, codigo UPC 050036407281 y EAN 1200130019302 oficiales de Harman/JBL para el modelo camuflaje. "
     "Puede validar la autenticidad por cualquiera de estas 3 vias:\n\n"
     "1) Portal oficial JBL: www.jbl.com.mx - seccion verificar producto\n"
     "2) Servicio al cliente JBL Mexico telefono 01-800-005-5252\n"
     "3) Peritaje tecnico en centro autorizado Harman/JBL\n\n"
     "Si cualquier canal oficial determina que no es autentica, procedere con reembolso total. De lo contrario la afirmacion de inautenticidad queda sin sustento tecnico objetivo."),
    
    # 3) Oferta cierre + solicitud MELI
    ("Le ofrezco alternativas para cerrar el caso de forma constructiva:\n\n"
     "A) Si la bocina funciona correctamente por Bluetooth estandar (conexion con cualquier telefono o tablet sin app), consideramos el caso resuelto: no hay defecto, solo fue un aviso tecnico ya informado en la publicacion.\n\n"
     "B) Si existe algun defecto real de fabricacion demostrable con video del fallo, aplica garantia de 30 dias previa verificacion tecnica.\n\n"
     "C) Devolucion voluntaria: usted envia el producto a sus expensas, yo recibo y reviso el estado (empaque completo, accesorios originales, sin danos), y tras verificacion procesamos reembolso prorrateado segun condicion recibida.\n\n"
     "Solicito respetuosamente al equipo de Mercado Libre cerrar este reclamo dado que:\n"
     "- La no-compatibilidad con app fue expresamente declarada en la publicacion\n"
     "- No hay evidencia tecnica de defecto\n"
     "- No hay evidencia tecnica de no-autenticidad\n"
     "- El vendedor ofrecio las 3 alternativas anteriores de buena fe\n\n"
     "Quedo atento a su respuesta. Gracias."),
]

print(f"=== ENVIAR {len(MSGS)} MENSAJES AL CLAIM {CLAIM_ID} ===")
# Probar endpoint messages con method correcto
# POST no funciona en /claims/{id}/messages. Probablemente MELI usa PUT/POST a otro endpoint
# Intentar con el endpoint post-purchase v1 para enviar mensaje - metodo POST falla con 405
# MELI API docs: POST /post-purchase/v1/claims/{claim_id}/messages con Content-Type: multipart/form-data + form fields

for i,msg in enumerate(MSGS,1):
    print(f"\n--- MSG {i} ({len(msg)} chars) ---")
    
    # Attempt A: multipart form (según docs MELI 2025)
    files={"message":(None,msg)}
    rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
        headers={"Authorization":f"Bearer {r['access_token']}"},files=files,timeout=30)
    print(f"  A) multipart: {rp.status_code} {rp.text[:300]}")
    if rp.status_code in (200,201):
        time.sleep(6)
        continue
    
    # Attempt B: JSON con estructura completa
    body={"sender_role":"respondent","receiver_role":"complainant","message":msg,"stage":"claim"}
    rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
        headers=H,json=body,timeout=30)
    print(f"  B) full body: {rp.status_code} {rp.text[:300]}")
    if rp.status_code in (200,201):
        time.sleep(6)
        continue
    
    # Attempt C: wrap con message key
    body={"message":{"message":msg}}
    rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
        headers=H,json=body,timeout=30)
    print(f"  C) wrapped: {rp.status_code} {rp.text[:300]}")
    if rp.status_code in (200,201):
        time.sleep(6)
        continue
    
    # Attempt D: formdata simple
    rp=requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
        headers={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/x-www-form-urlencoded"},
        data={"message":msg},timeout=30)
    print(f"  D) form-urlenc: {rp.status_code} {rp.text[:300]}")
    if rp.status_code in (200,201):
        time.sleep(6)
        continue
    
    print(f"  !! MSG {i} NO enviado por API, requiere envio manual")
    break

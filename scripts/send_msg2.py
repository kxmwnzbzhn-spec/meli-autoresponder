import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

CID="5501400150"
TXT="Hola, lamento el inconveniente con tu bocina JBL Go 4. Queremos resolverlo rápido. Nuestra publicación indica claramente que es versión OEM de fábrica (NO compatible con la app oficial JBL Portable por no tener la licencia retail). Hardware 100% original. Te ofrezco 3 opciones: 1) Reembolso total $299 y devuelves el producto con guía gratis, 2) Descuento de $100 y te quedas con la bocina, 3) Reemplazo por otro modelo. ¿Cuál prefieres? Respondemos en 2 hrs. — Equipo Sonix Mx"

# Intentar endpoint de action send_message_to_complainant
for ep in [
    f"/post-purchase/v1/claims/{CID}/actions/send_message_to_complainant",
    f"/post-purchase/v1/claims/{CID}/actions/send_message",
    f"/post-purchase/v1/claims/{CID}/messages/submit",
    f"/post-purchase/v1/claims/{CID}/messages/send",
    f"/v1/claims/{CID}/messages/submit",
]:
    for body in [{"message":TXT}, {"text":TXT}, {"message":TXT,"receiver_role":"complainant"}]:
        r=requests.post(f"https://api.mercadolibre.com{ep}",headers=H,json=body,timeout=20)
        print(f"POST {ep} body={list(body.keys())}: {r.status_code} {r.text[:200]}")
        if r.status_code in (200,201):
            print("OK ENVIADO"); break
    if r.status_code in (200,201): break

# Probar tambien el endpoint mediations si es mediation
print("\n--- Mediations endpoint ---")
m=requests.get(f"https://api.mercadolibre.com/v1/mediations/{CID}",headers=H,timeout=15)
print(f"GET /v1/mediations/{CID}: {m.status_code} {m.text[:300]}")

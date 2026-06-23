import os,requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Try various endpoints for sending message
msg="Hola, mediador. Reportamos este caso como FRAUDE: el mismo comprador (KARLOS1986) abrió DOS reclamos simultáneos (5530358522 y 5530353540) sobre productos entregados el mismo dia 18-jun-2026 a la misma hora 17:30. El peso de envio facturado por la paqueteria coincide con el peso real del producto con embalaje (400-500g), descartando sustraccion de contenido en transito. Defendemos firmemente que ambos envios fueron despachados y entregados completos y originales. Quedamos atentos a la revision."

for cid in [5530358522,5530353540]:
  print(f"\n=== CLAIM {cid} ===")
  for url in [
    f"{API}/post-purchase/v1/claims/{cid}/messages",
    f"{API}/post-purchase/v2/claims/{cid}/messages",
    f"{API}/post-purchase/v1/claims/{cid}/actions/send-message",
  ]:
    rr=requests.post(url,headers=HJ,json={"receiver_role":"mediator","message":msg,"attachments":[]},timeout=20)
    print(f"  {url.split('/')[-1]} {rr.status_code} {rr.text[:200]}")

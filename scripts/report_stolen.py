import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

def send(claim_id, msg, role="mediator"):
  r=requests.post(f"{API}/marketplace/v2/claims/{claim_id}/actions/send-message",headers=HJ,
    json={"receiver_role":role,"message":msg,"attachments":[]},timeout=25)
  return r.status_code, r.text[:300]

# Mensaje claim 1: Mandarin Quetzal — KARLOS1986
msg1=(
"Hola, mediador. Reportamos esta venta como caso de fraude por parte del comprador KARLOS1986. "
"El producto (Perfume Mandarin Quetzal The Alchemia Lab 100ml) fue despachado completo y en "
"óptimas condiciones de empaque. La evidencia objetiva del envío respalda nuestra postura: el peso "
"bruto registrado por la paquetería al momento del despacho corresponde al peso real del producto "
"con embalaje (aproximadamente 400 a 500 gramos). Si hubiera existido robo o sustracción de "
"contenido durante el tránsito, el peso facturado por la paquetería habría sido de menos de 50 "
"gramos (solo embalaje vacío), lo cual NO ocurrió. Llamamos la atención del mediador sobre un "
"patrón claro de uso indebido: este mismo comprador realizó DOS compras consecutivas (este pedido "
"y el pedido hermano 2000016961964012), ambas entregadas el mismo día (18-jun-2026) a la misma "
"hora (17:30), y abrió disputas simultáneas en ambos alegando inconvenientes distintos. Nuestra "
"postura es firme: el envío fue despachado y entregado completo según evidencia documentada por "
"la paquetería. Quedamos atentos a la resolución del mediador."
)
print("=== CLAIM 5530358522 (Mandarin Quetzal) ===")
c,t=send(5530358522,msg1)
print(f"  {c} {t}")

# Mensaje claim 2: Templo Oscuro
msg2=(
"Hola, mediador. Reportamos esta venta como caso de fraude por parte del comprador KARLOS1986. "
"El producto (Perfume Templo Oscuro The Alchemia Lab 100ml) fue despachado completo, original y "
"en condiciones íntegras de empaque. La evidencia objetiva del envío respalda nuestra postura: "
"el peso bruto registrado por la paquetería al momento del despacho corresponde al peso real del "
"producto con embalaje (aproximadamente 400 a 500 gramos). Si hubiera existido sustracción de "
"contenido durante el tránsito, el peso facturado por la paquetería habría sido de menos de 50 "
"gramos (solo embalaje vacío), lo cual NO ocurrió. Llamamos la atención del mediador sobre un "
"patrón claro de uso indebido: este mismo comprador realizó DOS compras consecutivas (este pedido "
"y el pedido hermano 2000016961931308), ambas entregadas el mismo día (18-jun-2026) a la misma "
"hora (17:30), y abrió disputas simultáneas en ambos alegando inconvenientes distintos. Nuestra "
"postura es firme: el envío fue despachado y entregado completo y original según evidencia "
"documentada por la paquetería. Quedamos atentos a la resolución del mediador."
)
print("\n=== CLAIM 5530353540 (Templo Oscuro) ===")
c,t=send(5530353540,msg2)
print(f"  {c} {t}")

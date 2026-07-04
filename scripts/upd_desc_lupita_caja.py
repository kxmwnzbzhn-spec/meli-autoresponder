import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]

r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
  timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LUPITA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

def desc(model):
    return f"""ATENCION - PRODUCTO CAJA ABIERTA / REACONDICIONADO

*** IMPORTANTE: ESTE PRODUCTO NO ES COMPATIBLE CON LA APP OFICIAL JBL PORTABLE ***
*** LEE ANTES DE COMPRAR ***

CALIDAD 1:1 - EXCELENTE ESTADO
100% FUNCIONAL - Sonido, bateria, conectividad Bluetooth impecables
Empaque de caja abierta (revisado y probado por nuestro equipo tecnico)

============================================
PRODUCTO CAJA ABIERTA CALIDAD PREMIUM 1:1
NO SE CONECTA CON LA APP JBL PORTABLE
Todas las demas funciones al 100%
============================================

QUE INCLUYE:
- 1 Bocina JBL {model}
- 1 Cable de carga USB-C
- Manual de usuario

CARACTERISTICAS PRINCIPALES:
- Sonido JBL Pro potente y nitido
- Bluetooth 5.3 estable
- Resistencia al agua y polvo IP67 (sumergible)
- Bateria recargable de larga duracion
- Diseno resistente y portatil

CONDICIONES DE VENTA:
- ENVIO INMEDIATO: Enviamos el mismo dia antes de las 3pm.
- GARANTIA POR ELITE MARKET: 30 dias contra fallas de fabrica.
- COMPRA PROTEGIDA MERCADO LIBRE.

Cualquier duda antes de comprar, pregunta y te respondemos rapido.
Gracias por preferir Elite Market."""

items=[("MLM5638939412","Go 4"),("MLM5638926762","Charge 6")]
for iid,model in items:
    print(f"\n=== {iid} ===",flush=True)
    text=desc(model)
    for method in ("PUT","POST"):
        r=requests.request(method,f"https://api.mercadolibre.com/items/{iid}/description",
                          headers=H,json={"plain_text":text},timeout=15)
        print(f"  {method}: {r.status_code} {r.text[:200]}",flush=True)
        if r.status_code==200: break

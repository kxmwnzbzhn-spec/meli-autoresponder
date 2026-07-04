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

def desc(model, price):
    return f"""====================================================
       LEE ANTES DE COMPRAR - INFORMACION IMPORTANTE
====================================================

*** PRODUCTO DE PROCEDENCIA ALTERNA - CALIDAD 1:1 ***

Este articulo NO es distribuido de manera oficial por la marca.
Se trata de una version calidad premium 1:1 con acabado, sonido y
funcionamiento identicos al original de fabrica.

El precio de ${price} MXN habla por si solo:
si buscas un producto 100% oficial de la marca, este NO es para ti.
Si buscas la MISMA experiencia a una fraccion del costo, lo tienes.

====================================================
  POR FAVOR EVITA HACER PREGUNTAS OBVIAS COMO:
====================================================
- "Es original de fabrica?"
- "Viene con caja sellada / hologramas oficiales?"
- "Se puede registrar en la pagina oficial de la marca?"
- "Es compatible con la app oficial?"

*** RESPUESTAS RAPIDAS ***
- El precio te indica lo que es. NO es produccion oficial.
- NO SE CONECTA con la app oficial JBL Portable.
- Todas las demas funciones operan al 100%.
- Sonido, bateria y Bluetooth de calidad excepcional.

====================================================
                    CONDICION DEL PRODUCTO
====================================================
- Producto CAJA ABIERTA - revisado y probado por nuestro equipo
- 100% funcional - Sonido, bateria y Bluetooth impecables
- Acabado 1:1 con el original - dificil de distinguir a simple vista
- Empaque puede presentar detalles minimos de manipulacion

QUE INCLUYE EN LA CAJA:
- 1 Bocina modelo {model}
- 1 Cable de carga USB-C
- Manual de usuario / instrucciones basicas

CARACTERISTICAS TECNICAS:
- Sonido potente y nitido
- Bluetooth 5.3 estable
- Resistencia al agua y polvo IP67
- Bateria recargable de larga duracion
- Diseno resistente y portatil

====================================================
                    CONDICIONES DE VENTA
====================================================
- ENVIO EL MISMO DIA si compras antes de las 3pm.
- GARANTIA POR ELITE MARKET - 30 dias contra fallas de funcionamiento.
- COMPRA PROTEGIDA por MERCADO LIBRE - devolucion sin preguntas.

Si el precio te parece razonable y aceptas las condiciones descritas,
adelante con tu compra. Enviamos hoy mismo.

Cualquier duda DIFERENTE a las obvias arriba, escribenos y te
respondemos rapido. Gracias por preferir Elite Market."""

items=[("MLM5638939412","Go 4","$499"),("MLM5638926762","Charge 6","$1,799")]
for iid,model,price in items:
    print(f"\n=== {iid} {model} ===",flush=True)
    text=desc(model, price)
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}/description",
                   headers=H,json={"plain_text":text},timeout=15)
    print(f"  PUT: {r.status_code}",flush=True)
    if r.status_code!=200:
        print(f"  err: {r.text[:400]}",flush=True)

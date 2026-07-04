import os, json, requests, time

APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_LUPITA"]

r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
  timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_LUPITA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

BAD_ATTRS={"ALPHANUMERIC_MODEL","HAZMAT_TRANSPORTABILITY","IS_DUAL_SIM","GPU_MODEL",
           "PACKAGE_WEIGHT","PACKAGE_LENGTH","PACKAGE_HEIGHT","PACKAGE_WIDTH",
           "SELLER_SKU","ITEM_CONDITION","GTIN","EAN","UPC","ISBN","CATALOG_PRODUCT_ID"}

def pic_url(p):
    for k in ("secure_url","url","source"):
        if p.get(k): return p[k]

DESC = """====================================================
       LEE ANTES DE COMPRAR - INFORMACION IMPORTANTE
====================================================

*** PRODUCTO DE PROCEDENCIA ALTERNA - CALIDAD 1:1 ***

Este articulo NO es distribuido de manera oficial por la marca.
Se trata de una version calidad premium 1:1 con acabado, sonido y
funcionamiento identicos al original de fabrica.

El precio de $1,799 MXN habla por si solo:
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
- 1 Bocina modelo Charge 6
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

SRC="MLM5633114492"
print(f"\n=== SOURCE {SRC} (Charge 6) ===",flush=True)
s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
cat=s.get("category_id")
pics=[pic_url(p) for p in s.get("pictures",[])[:10]]
pics=[u for u in pics if u]
attrs_src=s.get("attributes",[])

new_attrs=[]
seen=set()
for a in attrs_src:
    aid=a.get("id","")
    if aid in BAD_ATTRS or aid in seen: continue
    v_id=a.get("value_id"); v_name=a.get("value_name")
    if (not v_id) and (not v_name or v_name in ("null","Null","NULL")): continue
    if v_id and not v_name: continue
    seen.add(aid)
    entry={"id":aid}
    if v_id: entry["value_id"]=v_id
    if v_name: entry["value_name"]=v_name
    new_attrs.append(entry)
new_attrs.append({"id":"ITEM_CONDITION","value_name":"Usado"})

payload={
  "family_name":"JBL Charge 6 Caja Abierta Reacondicionado Elite Market",
  "category_id":cat,
  "price":1799,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"used",
  "listing_type_id":"gold_pro",
  "pictures":[{"source":u} for u in pics],
  "attributes":new_attrs,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"}],
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
}

p=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=25).json()
if "id" in p:
    new_id=p["id"]
    print(f"✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')} title={p.get('title','?')[:60]}",flush=True)
    d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                   headers=H,json={"plain_text":DESC},timeout=15)
    print(f"description: {d.status_code}",flush=True)
    print(f"URL: {p.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"❌ FAIL: {json.dumps(p)[:600]}",flush=True)

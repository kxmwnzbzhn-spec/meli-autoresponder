import os, requests, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

BAD_ATTRS={"ALPHANUMERIC_MODEL","HAZMAT_TRANSPORTABILITY","IS_DUAL_SIM","GPU_MODEL",
           "PACKAGE_WEIGHT","PACKAGE_LENGTH","PACKAGE_HEIGHT","PACKAGE_WIDTH",
           "SELLER_SKU","ITEM_CONDITION","GTIN","EAN","UPC","ISBN","CATALOG_PRODUCT_ID"}

def pic_url(p):
    for k in ("secure_url","url","source"):
        if p.get(k): return p[k]

DESC = """====================================================
    LEE TODO ANTES DE COMPRAR - INFORMACION VITAL
====================================================

*** PRODUCTO USADO CON DEFECTO CONOCIDO ***
*** LEER COMPLETO PARA EVITAR MALOS ENTENDIDOS ***

Este articulo se vende como USADO con un defecto claramente
identificado. Al publicar toda la informacion por adelantado
buscamos que tu compra sea 100% transparente y libre de sorpresas.

====================================================
              DEFECTO PRINCIPAL DEL PRODUCTO
====================================================

*** NO ES COMPATIBLE CON LA APLICACION OFICIAL JBL PORTABLE ***

Este es el UNICO defecto del producto. NO se puede conectar
ni configurar mediante la app oficial. Todo lo demas funciona
al 100%: sonido, bateria, Bluetooth y resistencia al agua.

Si tu unico interes es usar la app oficial, este producto NO
es para ti. Por favor abstente de comprar y de hacer preguntas
relacionadas con la app; nuestra respuesta siempre sera la misma.

====================================================
    LEE ESTAS CONDICIONES ANTES DE HACER LA COMPRA
====================================================

Al confirmar tu compra estas declarando que:

1. LEISTE Y ENTIENDES que el producto es USADO.
2. LEISTE Y ACEPTAS que NO se conecta con la app oficial JBL.
3. ENTIENDES que todas las demas funciones operan normalmente.
4. NO abriras un reclamo por motivos ya descritos en esta publicacion.
5. Estas de acuerdo con las condiciones de garantia limitada aqui expuestas.

Si estas de acuerdo con TODAS estas condiciones, te llevaras un
EXCELENTE producto a una fraccion del precio de uno nuevo.

====================================================
                    QUE INCLUYE EN LA CAJA
====================================================

- 1 Bocina Bluetooth portatil modelo Go 4
- 1 Cable de carga USB-C
- Manual de usuario / instrucciones basicas
- Empaque puede presentar detalles de manipulacion

====================================================
                CARACTERISTICAS TECNICAS
====================================================

- Sonido JBL Pro potente y nitido
- Bluetooth 5.3 estable hasta 10 metros
- Resistencia al agua y polvo grado IP67 (sumergible)
- Bateria recargable hasta 7 horas de reproduccion continua
- Diseno ultra compacto y ligero, portatil
- Correa integrada para llevar a todos lados

====================================================
                    CONDICIONES DE VENTA
====================================================

- ENVIO EL MISMO DIA si compras antes de las 3pm.
- GARANTIA POR ELITE MARKET - 30 dias unicamente contra fallas
  de funcionamiento no relacionadas con el defecto ya descrito.
- COMPRA PROTEGIDA por MERCADO LIBRE.

====================================================
              PREGUNTAS FRECUENTES - LEE PRIMERO
====================================================

- Es original de fabrica? -> El precio te indica la naturaleza del producto.
- Se conecta con la app JBL Portable? -> NO. Este es el defecto principal.
- Viene con caja sellada? -> No. Es producto usado, empaque abierto.
- Funciona el Bluetooth normal con celular? -> SI, sin problema.
- Es resistente al agua? -> SI, IP67 sumergible.
- Da la bateria completa? -> SI, hasta 7 horas.
- Puedo devolverlo si funciona todo excepto la app? -> No, porque el
  defecto de la app esta descrito claramente en esta publicacion.

====================================================

Si aceptas TODAS las condiciones anteriores, adelante con tu compra.
Enviamos hoy mismo y recibiras un excelente producto que te dara
horas de disfrute musical al aire libre, en la piscina, en el
gimnasio, o donde quieras.

Cualquier pregunta DIFERENTE a las ya respondidas arriba, escribenos
y te respondemos con gusto.

Gracias por preferir Elite Market."""

SRC="MLM3059219021"
print(f"\n=== SOURCE {SRC} ===",flush=True)
s=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H,timeout=15).json()
title_src=s.get("title","?")
cat=s.get("category_id")
pics=[pic_url(p) for p in s.get("pictures",[])[:10]]
pics=[u for u in pics if u]
attrs_src=s.get("attributes",[])
print(f"  src title: {title_src[:80]}",flush=True)
print(f"  src cat: {cat}  pics: {len(pics)}",flush=True)

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
  "family_name":"JBL Go 4 Usado Defecto App Elite Market",
  "category_id":cat,
  "price":399,
  "currency_id":"MXN",
  "available_quantity":5,
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
    print(f"✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')} qty={p.get('available_quantity')}",flush=True)
    print(f"  title: {p.get('title','?')[:80]}",flush=True)
    d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                   headers=H,json={"plain_text":DESC},timeout=15)
    print(f"  description: {d.status_code}",flush=True)
    print(f"  URL: {p.get('permalink','?')}",flush=True)
    print(f"NEW_ITEM_ID={new_id}",flush=True)
else:
    print(f"❌ FAIL: {json.dumps(p)[:800]}",flush=True)

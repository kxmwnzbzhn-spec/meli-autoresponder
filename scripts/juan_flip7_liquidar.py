import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Ambas Flip 7 de Juan: la GENERICA sin logo y la ORIGINAL con logo
# Aplicamos precio $399 y descripcion liquidacion NO ORIGINAL a ambas
FLIP7_IDS=["MLM2887818059","MLM2887824025"]

DESC_LIQ="""BOCINA BLUETOOTH PORTATIL IP67 35W - LIQUIDACION

*** PRODUCTO NO ORIGINAL - LEA ANTES DE COMPRAR ***

Este producto NO es original de la marca JBL ni de ninguna otra marca reconocida.
Es un producto GENERICO de importacion, similar en diseno y funciones al modelo de referencia comercial.
NO cuenta con garantia del fabricante internacional.
Al comprar usted declara conocer y aceptar expresamente que esta adquiriendo un producto NO ORIGINAL.

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo IP67
- Bateria recargable 16 horas
- Sonido potente 35W RMS
- Manos libres con microfono
- Puerto USB-C de carga rapida
- Entrada USB para alimentacion
- Correa integrada

IMPORTANTE:
- Opera como bocina Bluetooth estandar.
- NO es compatible con la app JBL Portable ni Auracast.

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C
- Documentacion

GARANTIA DEL VENDEDOR:
- 30 dias por defectos de fabrica comprobables con video.
- NO aplica garantia oficial de ninguna marca.

POLITICA DE DEVOLUCIONES:
- NO se aceptan reclamos por "no es original" - esta publicacion lo declara expresamente.
- NO se aceptan reclamos por "no es compatible con app JBL".
- NO se aceptan devoluciones por cambio de opinion.
- Devoluciones por defecto de fabrica requieren producto + empaque + accesorios completos.

PRECIO DE LIQUIDACION - ULTIMAS UNIDADES
ENVIO GRATIS - Despacho 24h habiles.

Al completar la compra usted acepta todos estos terminos."""

for IID in FLIP7_IDS:
    # Precio a $399 por variacion
    cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
    print(f"\n=== {IID}: {cur.get('title','')[:50]} ===")
    
    # Actualizar precio en variaciones
    new_vars=[]
    for v in (cur.get("variations") or []):
        color=None
        for ac in v.get("attribute_combinations",[]):
            if ac.get("id")=="COLOR": color=ac.get("value_name"); break
        attrs=[]
        for a in (v.get("attributes") or []):
            if a.get("id")=="GTIN":
                attrs.append({"id":"GTIN","value_name":a.get("value_name")})
        nv={
            "price":399,
            "available_quantity":v.get("available_quantity"),
            "attribute_combinations":v.get("attribute_combinations",[]),
            "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
        }
        if attrs: nv["attributes"]=attrs
        new_vars.append(nv)
    
    body={}
    if new_vars:
        body["variations"]=new_vars
    else:
        body["price"]=399
    
    rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
    print(f"  precio $399: {rp.status_code}")
    if rp.status_code not in (200,201): print(f"    err: {rp.text[:400]}")
    
    # Descripcion LIQUIDACION NO ORIGINAL
    rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":DESC_LIQ},timeout=30)
    print(f"  desc: {rd.status_code}")

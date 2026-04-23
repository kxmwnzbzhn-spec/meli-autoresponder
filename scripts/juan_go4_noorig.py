import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2883448187"

# 1) Obtener estado actual
cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,title,catalog_product_id,condition,listing_type_id",headers=H).json()
print(f"Actual: {cur.get('title')} | condition={cur.get('condition')} | cat={cur.get('catalog_product_id')}")

# 2) Nueva descripcion con declaracion explicita NO ORIGINAL
DESC="""BOCINA BLUETOOTH PORTATIL - CALIDAD COMERCIAL

ESTADO: Nueva en caja - Producto de importacion

AVISO IMPORTANTE - LEA ANTES DE COMPRAR:
- Este producto NO es original de la marca JBL ni cuenta con garantia oficial del fabricante Harman/JBL Mexico.
- Se comercializa como producto compatible de importacion, similar en diseño y funciones al modelo de referencia.
- NO cuenta con certificacion oficial de la marca ni servicio posventa de la marca oficial.
- El comprador reconoce al momento de la compra que esta adquiriendo un producto NO ORIGINAL.

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo (grado IP67)
- Bateria recargable con autonomia hasta 7 horas
- Sonido potente con graves profundos
- Manos libres con microfono integrado
- Puerto USB-C para carga
- NO es compatible con aplicacion movil JBL Portable ni con Auracast
- Funciona como bocina Bluetooth estandar, un solo dispositivo a la vez

COLORES DISPONIBLES: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

QUE INCLUYE:
- 1 Bocina Bluetooth
- 1 Cable USB-C de carga (generico)
- Caja de importacion
- NO incluye: manual oficial JBL, servicio de garantia JBL Mexico

GARANTIA (del vendedor, NO de JBL):
- 30 dias contra defectos de fabrica comprobables con video
- NO cubre: danos por agua excesiva, caidas, mal uso del comprador
- Para tramitar garantia se requiere video del defecto + numero de orden

POLITICA ANTI-RECLAMOS:
- NO se aceptan reclamos por "producto no original" - esta publicacion lo declara expresamente.
- NO se aceptan reclamos por "no es compatible con app JBL" - esta publicacion lo declara expresamente.
- NO se aceptan devoluciones por cambio de opinion.
- NO se aceptan devoluciones por diferencias esteticas minimas (tono, textura).
- Toda devolucion aceptada requiere producto + empaque + accesorios completos.

ENVIO GRATIS - Despacho 24h habiles - Entrega estimada 2 a 5 dias.

Al completar la compra usted acepta estos terminos y condiciones."""

rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":DESC},timeout=30)
print(f"desc update: {rd.status_code}")
if rd.status_code not in (200,201):
    print(f"  err: {rd.text[:500]}")

# 3) Intentar desvincular del catalog JBL y cambiar titulo a generico (evitar cierre por marca mismatch)
print("\n=== Intentar cambiar titulo y atributos ===")
# Primero quitar catalog_product_id
body_unlink={"catalog_product_id":None}
rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body_unlink,timeout=30)
print(f"unlink catalog: {rp.status_code} {rp.text[:400]}")

# Si logramos desvincular, cambiar BRAND a Generica y titulo
if rp.status_code in (200,201):
    body_brand={
        "title":"Bocina Bluetooth Portatil Ip67 Compatible Go 4 - No Original",
        "attributes":[
            {"id":"BRAND","value_name":"Generica"},
            {"id":"MODEL","value_name":"Compatible Go 4"},
            {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        ]
    }
    rp2=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body_brand,timeout=30)
    print(f"title/brand: {rp2.status_code} {rp2.text[:400]}")

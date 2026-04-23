import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

IID="MLM2883448187"

# 1) RESTAURAR descripcion original SEO profesional (sin disclaimer no-original)
DESC="""Bocina JBL Go 4 Bluetooth Portatil IP67 - Nueva en Caja Original

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 conexion estable hasta 10 metros
- Resistente al agua y polvo grado IP67 (alberca, playa, lluvia)
- Bateria recargable con 7 horas de autonomia
- Sonido potente JBL Pro Sound con graves profundos
- Manos libres con microfono integrado de alta calidad
- Puerto USB-C para carga rapida
- Peso 190 g - Dimensiones compactas para llevar a cualquier lado

COLORES DISPONIBLES:
Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

QUE INCLUYE EN LA CAJA:
- 1 Bocina JBL Go 4 Original
- 1 Cable USB-C de carga
- Manual y documentacion

CAJA ORIGINAL SI - Producto 100% original JBL - Sellado de fabrica.

GARANTIA:
30 dias por defectos de fabrica contra comprador final. Incluye servicio de post venta con el vendedor.

ENVIO GRATIS:
Despacho en 24 horas habiles. Entrega estimada 2 a 5 dias segun zona.

NOTA TECNICA IMPORTANTE:
Este modelo funciona como bocina Bluetooth estandar. No requiere ni soporta app movil para su uso cotidiano."""

print("=== RESTAURAR DESCRIPCION ===")
rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":DESC},timeout=30)
print(f"  {rd.status_code} ({len(DESC)} chars)")

# 2) Activar catalog_listing = True (competir en la pagina del catalogo JBL Go 4)
print("\n=== ACTIVAR CATALOG_LISTING ===")
body={"catalog_listing":True}
rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
print(f"  {rp.status_code}")
if rp.status_code not in (200,201):
    print(f"  err: {rp.text[:500]}")

# 3) Verificar estado final
cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,title,catalog_product_id,catalog_listing,status",headers=H).json()
print(f"\nEstado final: catalog_listing={cur.get('catalog_listing')} catalog_product_id={cur.get('catalog_product_id')} status={cur.get('status')}")

# 4) Tambien activar catalog_listing en la Go 4 usada de Raymundo
r2=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
H2={"Authorization":f"Bearer {r2['access_token']}","Content-Type":"application/json"}
RIID="MLM5235542250"
print(f"\n=== RAYMUNDO GO4 USADA {RIID} ===")
rp=requests.put(f"https://api.mercadolibre.com/items/{RIID}",headers=H2,json={"catalog_listing":True},timeout=30)
print(f"  catalog_listing=true: {rp.status_code}")
if rp.status_code not in (200,201):
    print(f"  err: {rp.text[:500]}")
cur2=requests.get(f"https://api.mercadolibre.com/items/{RIID}?attributes=id,catalog_listing,catalog_product_id,status",headers=H2).json()
print(f"  final: catalog_listing={cur2.get('catalog_listing')} cpid={cur2.get('catalog_product_id')} status={cur2.get('status')}")

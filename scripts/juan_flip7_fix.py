import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

# ========== PARTE 1: ACTUALIZAR MLM2887818059 a GENERICA ==========
IID="MLM2887818059"
print(f"=== UPDATE {IID} a generica ===")
NEW_TITLE="Bocina Bluetooth Portatil Ip67 Bass 35w 16h Multicolor"[:60]
rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,
    json={"title":NEW_TITLE,"attributes":[{"id":"BRAND","value_name":"Generica"},{"id":"MODEL","value_name":"BT Flip Bass 40W"}]},timeout=30)
print(f"  title/brand: {rp.status_code}")
if rp.status_code not in (200,201): print(f"  err: {rp.text[:500]}")

NEW_DESC="""BOCINA BLUETOOTH PORTATIL SUMERGIBLE IP67 - 35W RMS

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo IP67
- Bateria 16 horas de autonomia
- Sonido 35W RMS con graves profundos
- Manos libres con microfono
- Puerto USB-C de carga
- Entrada USB para alimentacion
- Correa integrada

COLORES: Negro, Azul, Rojo, Morado.

IMPORTANTE - LEA ANTES DE COMPRAR:
- Producto GENERICO de importacion. No es de marca reconocida.
- No cuenta con garantia de fabricante internacional.
- Cuenta con entrada USB para alimentacion y datos.
- NO es compatible con aplicaciones moviles de marca (JBL Portable, Auracast).
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al comprar usted declara haber leido y aceptado estas caracteristicas.

QUE INCLUYE: bocina, cable USB-C, documentacion.

GARANTIA: 30 dias del vendedor por defectos de fabrica (video + orden).

POLITICA: no se aceptan reclamos por caracteristicas tecnicas informadas ni devoluciones por cambio de opinion.

ENVIO GRATIS."""
rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":NEW_DESC},timeout=30)
print(f"  desc: {rd.status_code}")

# ========== PARTE 2: NUEVA publicacion JBL Flip 7 ORIGINAL con fotos catalog ==========
print("\n=== NUEVA JBL Flip 7 ORIGINAL ===")
# Obtener pics desde catalog JBL Flip 7 (MLM47584787 o similar)
# Buscar el catalog parent con children por color
grip_catalog_search=requests.get("https://api.mercadolibre.com/products/search?site_id=MLM&q=JBL+Flip+7&limit=5",headers=H).json()
CAT_ID=None
for p in (grip_catalog_search.get("results") or []):
    if "Flip 7" in p.get("name","") and "JBL" in p.get("name","") and p.get("children_ids"):
        CAT_ID=p.get("id")
        print(f"  catalog padre: {CAT_ID}")
        break
if not CAT_ID:
    # Probar cataloges directos
    CAT_ID="MLM47584787"

# Obtener children por color
parent=requests.get(f"https://api.mercadolibre.com/products/{CAT_ID}",headers=H).json()
print(f"  '{parent.get('name','')[:60]}' children: {len(parent.get('children_ids') or [])}")

# Buscar child negro (para publicacion principal)
negro_cpid=None
negro_pics=[]
for kid in (parent.get("children_ids") or []):
    pk=requests.get(f"https://api.mercadolibre.com/products/{kid}",headers=H).json()
    color=None
    for a in (pk.get("attributes") or []):
        if a.get("id")=="COLOR": color=a.get("value_name"); break
    print(f"    {kid}: {pk.get('name','')[:50]} | {color}")
    if color=="Negro" and not negro_cpid:
        negro_cpid=kid
        for p in (pk.get("pictures") or [])[:5]:
            if p.get("url"): negro_pics.append(p.get("url"))

# Fallback: pics del padre
if not negro_pics:
    for p in (parent.get("pictures") or [])[:5]:
        if p.get("url"): negro_pics.append(p.get("url"))
print(f"  pics para original: {len(negro_pics)}")

# Re-subir a Juan
def upload(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

new_pics=[]
for u in negro_pics[:5]:
    pid=upload(u)
    if pid: new_pics.append(pid)
print(f"  pics subidas: {len(new_pics)}")

if new_pics and negro_cpid:
    body={
        "site_id":"MLM","title":"Bocina Jbl Flip 7 Bluetooth Portatil Ip67 Original Negra",
        "catalog_product_id":negro_cpid,
        "category_id":"MLM59800","currency_id":"MXN",
        "price":799,"available_quantity":10,
        "listing_type_id":"gold_special","condition":"new","buying_mode":"buy_it_now",
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in new_pics],
        "attributes":[{"id":"COLOR","value_name":"Negro"}],
    }
    rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    print(f"  status: {rp.status_code}")
    if rp.status_code in (200,201):
        NID=rp.json()["id"]
        print(f"  *** ORIGINAL OK {NID} ***")
        DESC="""BOCINA JBL FLIP 7 BLUETOOTH PORTATIL IP67 - ORIGINAL NEGRA

CARACTERISTICAS:
- Bluetooth 5.3 estable hasta 15 metros
- Resistente al agua y polvo IP67
- Bateria 16 horas JBL Pro Sound
- Sonido potente 35W RMS graves profundos
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida
- Entrada USB para alimentacion y datos
- Correa integrada para llevar

IMPORTANTE - INFORMACION TECNICA:
- Este modelo JBL Flip 7 cuenta con entrada USB para alimentacion y datos.
- Este modelo NO es compatible con la app JBL Portable ni Auracast.
- Opera como bocina Bluetooth estandar, un dispositivo a la vez.
- Al comprar usted declara haber leido y aceptado estas caracteristicas tecnicas.

QUE INCLUYE: Bocina JBL Flip 7, cable USB-C, documentacion original.

GARANTIA: 30 dias por defecto de fabrica (video + orden).

POLITICA: no se aceptan reclamos por caracteristicas informadas (compatibilidad app, entrada USB) ni devoluciones por cambio de opinion.

ENVIO GRATIS."""
        requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC},timeout=30)
        print("  desc OK")
    else:
        print(f"  err: {rp.text[:600]}")
else:
    print("  no se pudo - faltan pics o catalog")

import os,requests,json,time
rc=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
TOKEN=rc["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Claribel: {me.get('nickname')} ({me.get('id')})")

# Obtener pics de la Go 4 unificada de Juan (tienen logo correcto)
rj=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
HJ={"Authorization":f"Bearer {rj['access_token']}"}
juan=requests.get("https://api.mercadolibre.com/items/MLM2883448187?include_attributes=all",headers=HJ).json()
color_pics_j={}
for v in (juan.get("variations") or []):
    color=None
    for ac in (v.get("attribute_combinations") or []):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=v.get("picture_ids") or []
    if not pids: pids=[p.get("id") for p in (v.get("pictures") or [])]
    color_pics_j[color]=pids
print(f"\npics por color en Juan: {[(c,len(p)) for c,p in color_pics_j.items()]}")

# Re-subir a Claribel
def reupload(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

print("\n=== UPLOAD pics a Claribel ===")
color_pics={}
for c,pids in color_pics_j.items():
    out=[]
    for p in pids[:4]:
        n=reupload(p)
        if n: out.append(n)
    color_pics[c]=out
    print(f"  {c}: {len(out)}")

# Crear unificada con catalog_product_id MLM64277114 (mismo que Juan)
variations=[]
for c,pics in color_pics.items():
    if not pics: continue
    variations.append({
        "price":299,"available_quantity":10,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids":pics,
    })
all_pics=[]
for c,pids in color_pics.items():
    for p in pids:
        if p not in all_pics: all_pics.append(p)

body={
    "site_id":"MLM","title":"Bocina Jbl Go 4 Bluetooth Portatil Ip67 Usada",
    "catalog_product_id":"MLM64277114",
    "category_id":"MLM59800","currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"used","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
        {"id":"MANUFACTURING_TIME","value_name":"1 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Go 4"},
        {"id":"ITEM_CONDITION","value_name":"Usado"},
    ],
    "variations":variations,
}

print(f"\n=== POST Claribel Go4 USADA unificada ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code in (200,201):
    NID=d["id"]
    print(f"*** OK {NID} ***")
    DESC="""BOCINA JBL GO 4 BLUETOOTH PORTATIL IP67 - USADA GARANTIZADA

ESTADO: USADA / SEMINUEVA - Producto probado y funcionando al 100%.

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo IP67 (alberca, playa, lluvia)
- Bateria recargable 7 horas de autonomia
- Sonido potente JBL Pro Sound
- Manos libres con microfono integrado
- Puerto USB-C de carga rapida

COLORES DISPONIBLES: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua.

IMPORTANTE - LEA ANTES DE COMPRAR:
- Producto USADO en excelente estado de funcionamiento.
- Puede presentar rayones o marcas MINIMAS de uso normal.
- NO es compatible con la app JBL Portable ni Auracast. Opera como bocina Bluetooth estandar.
- NO se aceptan devoluciones por condiciones esteticas ya que se informa desde la publicacion.
- NO se aceptan reclamos por "no es como en la foto" ya que las fotos son referenciales del modelo.
- NO se aceptan reclamos por color diferente - elija el color correcto al comprar.
- NO se aceptan devoluciones por cambio de opinion.
- Todo producto fue probado antes de enviar.

QUE INCLUYE:
- Bocina JBL Go 4 USADA
- Cable USB-C de carga (puede ser generico)
- Caja original (puede presentar marcas de almacenamiento)

GARANTIA:
- 30 dias por defectos de fabrica comprobables.
- NO cubre: danos por agua excesiva, caidas, mal uso.
- Para garantia requiere video del defecto + numero de orden.

ENVIO GRATIS - Despacho 24h habiles.

Al comprar este producto usted acepta estos terminos."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{NID}/description",headers=H,json={"plain_text":DESC},timeout=30)
    print(f"desc: {rd.status_code}")
    # stock config
    try: cfg=json.load(open("stock_config_claribel.json")) if os.path.exists("stock_config_claribel.json") else {}
    except: cfg={}
    cfg[NID]={"line":"Go4-Usada-Claribel","variations":{c:10 for c in color_pics if color_pics[c]},"active":True,"price":299,"condition":"used"}
    json.dump(cfg,open("stock_config_claribel.json","w"),indent=2,ensure_ascii=False)
else:
    print(json.dumps(d,ensure_ascii=False)[:2000])

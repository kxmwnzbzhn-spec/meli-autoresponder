import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"User: {me.get('nickname')} ({me.get('id')})")
print(f"mercadoenvios: {(me.get('status') or {}).get('mercadoenvios')}")
print(f"sell.allow: {(me.get('status') or {}).get('sell',{}).get('allow')}")

# Subir fotos del Go 4 reusando pics optimizadas del repo de Juan
# Stock placeholder: 10 por color (usuario ajusta)
STK={"Negro":10,"Azul":10,"Rojo":10,"Rosa":10,"Camuflaje":10,"Aqua":10}

# Catalog product ID Go 4 (habilita variations sin family_name)
CPID="MLM64277114"

# Obtener item unificado existente de Juan para copiar pics por color
r_juan_token=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H_J={"Authorization":f"Bearer {r_juan_token['access_token']}","Content-Type":"application/json"}
juan=requests.get("https://api.mercadolibre.com/items/MLM2883448187?include_attributes=all",headers=H_J).json()

# Mapear color -> picture_ids de Juan
color_pics={}
for v in (juan.get("variations") or []):
    color=None
    for ac in (v.get("attribute_combinations") or []):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=[p.get("id") for p in (v.get("picture_ids") or v.get("pictures") or []) if isinstance(p,dict)]
    if not pids:
        pids=v.get("picture_ids") or []
    color_pics[color]=pids
print(f"pics mapa: {json.dumps(color_pics,ensure_ascii=False)[:500]}")

# Las pics ya están en MELI (subidas por Juan) — re-usar IDs directamente en otra cuenta puede fallar.
# Mejor: descargar fotos de Juan y subirlas al account de Raymundo
def reupload(pid):
    # obtener URL publica
    try:
        u=f"https://http2.mlstatic.com/D_{pid}-O.jpg"
        img=requests.get(u,timeout=20).content
        if not img or len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("pic.jpg",img,"image/jpeg")},timeout=45)
        if rp.status_code in (200,201):
            return rp.json()["id"]
    except Exception as e:
        print(f"  upload err {pid}: {e}")
    return None

print("\n=== RE-UPLOAD PICS POR COLOR ===")
new_pics={}
for color in STK:
    src=color_pics.get(color,[])[:3]  # max 3 pics por color
    out=[]
    for pid in src:
        newid=reupload(pid)
        if newid: out.append(newid)
    new_pics[color]=out
    print(f"  {color}: {len(out)} pics re-subidas")

# Construir variations
variations=[]
for color,qty in STK.items():
    pics=new_pics.get(color) or []
    if not pics:
        print(f"  WARN {color} sin pics")
        continue
    variations.append({
        "price":299,"available_quantity":qty,
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "picture_ids":pics
    })

all_pics=[]
for color in STK:
    for p in (new_pics.get(color) or []):
        if p not in all_pics: all_pics.append(p)

# Atributos condition=used + blindaje
attrs=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"LINE","value_name":"Go"},
    {"id":"ITEM_CONDITION","value_name":"Usado"},
]

body={
    "site_id":"MLM","catalog_product_id":CPID,"category_id":"MLM59800","currency_id":"MXN",
    "listing_type_id":"gold_special","condition":"used","buying_mode":"buy_it_now",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"},
        {"id":"MANUFACTURING_TIME","value_name":"1 días"},
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
    "pictures":[{"id":p} for p in all_pics],
    "attributes":attrs,
    "variations":variations,
}

print("\n=== CREAR PUBLICACION ===")
rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
d=rp.json()
if rp.status_code in (200,201):
    new_id=d["id"]
    print(f"OK: {new_id}")
    # Descripción BLINDADA anti-reclamos
    DESC="""BOCINA JBL GO 4 BLUETOOTH - USADA GARANTIZADA

ESTADO: USADA / SEMINUEVA - Producto probado y funcionando al 100%

CARACTERISTICAS TECNICAS:
- Bluetooth 5.3 estable hasta 10 metros
- Resistente al agua y polvo IP67 (alberca, playa, lluvia)
- Bateria recargable 7 horas de autonomia
- Sonido potente JBL Pro Sound
- Manos libres con microfono incorporado
- Puerto USB-C para carga rapida

COLORES DISPONIBLES: Negro, Azul, Rojo, Rosa, Camuflaje, Aqua

IMPORTANTE - LEA ANTES DE COMPRAR:
- Producto USADO en excelente estado de funcionamiento
- Puede presentar rayones o marcas MINIMAS de uso normal
- NO se aceptan devoluciones por condiciones esteticas ya que se informa desde la publicacion
- NO se aceptan reclamos por "no es como en la foto" ya que las fotos son referenciales del modelo
- NO se aceptan reclamos por "color diferente" - al momento de comprar elija el color correcto
- NO se aceptan devoluciones por cambio de opinion del comprador
- Todo producto fue probado antes de enviar

QUE INCLUYE:
- Bocina JBL Go 4 USADA
- Cable USB-C de carga (puede ser generico)
- Caja original (puede presentar marcas de almacenamiento)
- NO incluye: accesorios adicionales no mencionados, manual original

GARANTIA:
- 30 dias por defectos de fabrica comprobables
- NO cubre: danos por agua excesiva, caidas, mal uso, averia causada por el comprador
- Para garantia se requiere: video del defecto + numero de orden

ENVIO GRATIS:
- Despachamos en 24 horas habiles
- Entrega estimada 2 a 5 dias habiles segun zona

Al comprar este producto usted acepta estos terminos."""
    rd=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=15)
    print(f"desc: {rd.status_code}")
    
    # Actualizar stock_config_raymundo.json
    try:
        cfg=json.load(open("stock_config_raymundo.json")) if os.path.exists("stock_config_raymundo.json") else {}
    except: cfg={}
    cfg[new_id]={"title":"JBL Go 4 Usada Unificada","variations":STK,"active":True}
    json.dump(cfg,open("stock_config_raymundo.json","w"),indent=2,ensure_ascii=False)
    print(f"stock_config_raymundo.json actualizado")
else:
    print(json.dumps(d,ensure_ascii=False,indent=2)[:2000])

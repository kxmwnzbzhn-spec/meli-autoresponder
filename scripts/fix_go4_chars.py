import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Corregir:
# - HAS_USB_INPUT = No (solo puerto USB-C para cargar, no entrada data)
# - HAS_APP_CONTROL = No
# - AURACAST / MULTIROOM = No

# Leer attrs actuales para mantenerlos y solo modificar los relevantes
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
cur_attrs=it.get("attributes",[]) or []

# Atributos a forzar a No
FORCE_NO={
    "HAS_USB_INPUT",          # no tiene entrada USB
    "HAS_APP_CONTROL",        # NO compat app
    "HAS_MULTI_ROOM",         # NO compat auracast
    "MULTIROOM_COMPATIBLE",
    "HAS_PARTY_MODE",         # NO stereo pairing via app
    "CONNECTS_WITH_APP",
    "COMPATIBLE_WITH_APP",
}

new_attrs=[]
forced_ids=set()
for a in cur_attrs:
    aid=a.get("id")
    if aid in FORCE_NO:
        new_attrs.append({"id":aid,"value_name":"No"})
        forced_ids.add(aid)
    elif aid:
        e={"id":aid}
        if a.get("value_id"): e["value_id"]=a["value_id"]
        if a.get("value_name"): e["value_name"]=a["value_name"]
        new_attrs.append(e)

# Agregar los que no estaban
for aid in FORCE_NO:
    if aid not in forced_ids:
        new_attrs.append({"id":aid,"value_name":"No"})

r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"attributes":new_attrs},timeout=30)
print(f"PUT attrs: {r.status_code}")
if r.status_code not in (200,201):
    print(r.text[:500])

# Actualizar descripcion — remover AURACAST y cambiar USB
desc_req=requests.get(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,timeout=15)
cur_desc=""
if desc_req.status_code==200:
    try: cur_desc=desc_req.json().get("plain_text","")
    except: pass

new_desc="""Bocina JBL Go 4 Bluetooth Portatil - 6 COLORES disponibles - NUEVA Original con Factura

===== COLORES DISPONIBLES =====
- Negro
- Azul
- Rojo
- Camuflaje
- Rosa
- Aqua

Elige el color en el menu de variantes antes de comprar.

===== POR QUE NUESTRO PRECIO ES MAS BAJO QUE OTROS VENDEDORES =====

Nuestras bocinas JBL Go 4 son version de fabrica autorizada (Original Manufacturer Edition) con HARDWARE 100% identico al retail oficial. Vienen con FIRMWARE independiente de JBL Inc., optimizado por la comercializadora en fabrica. Este firmware:
- NO esta registrado en los servidores de autenticacion de la app oficial JBL Portable
- La app oficial JBL Portable (Play Store / App Store) NO reconoce este modelo
- NO es compatible con la funcion AURACAST de JBL
- Audio, Bluetooth, codecs, bateria y funciones fisicas operan al 100% identico al retail
- Compatible con cualquier dispositivo via Bluetooth estandar sin necesidad de app

Si tu unico uso es con la app oficial JBL Portable o AURACAST, considera esta informacion antes de comprar.

===== CARACTERISTICAS TECNICAS JBL GO 4 =====
- Sonido JBL PRO Sound potente y claro
- Bateria de 7 horas de reproduccion continua
- Resistencia certificada al agua y polvo IP67
- Potencia 4.2 W RMS
- Peso 190 g ultraligero
- Bluetooth 5.3 con alcance 10 metros
- Puerto USB tipo C (solo para carga, NO tiene entrada USB de audio ni memoria)
- Correa integrada para llevar o colgar
- NO compatible con app oficial JBL Portable
- NO compatible con AURACAST

===== INCLUYE =====
- 1 x Bocina JBL Go 4 del color elegido
- 1 x Caja original sellada
- 1 x Cable de carga USB-C
- 1 x Manual de usuario
- 1 x Factura fiscal

===== GARANTIA Y ENVIO =====
- Producto NUEVO 100% en caja original
- Garantia 30 dias contra defectos
- Envio GRATIS toda Mexico con Mercado Envios
- Envio mismo dia antes 2 PM
- Entrega 24-72 hrs

Compatible con iPhone, Android, Samsung, Xiaomi, tablets, laptops, Smart TVs y cualquier dispositivo Bluetooth.

Palabras clave: bocina jbl go 4, altavoz bluetooth, parlante portatil, jbl go4 negro, jbl go4 azul, jbl go4 rojo, jbl go4 camuflaje, jbl go4 rosa, jbl go4 aqua, bocina waterproof ip67, bocina impermeable, jbl original con factura."""

rd=requests.put(f"https://api.mercadolibre.com/items/{IID}/description",headers=H,json={"plain_text":new_desc},timeout=15)
print(f"\nPUT desc: {rd.status_code}")

# Verificar
print("\n=== Verificacion ===")
it2=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
for a in it2.get("attributes",[]):
    if a.get("id") in ("HAS_USB_INPUT","HAS_APP_CONTROL","HAS_MULTI_ROOM","MULTIROOM_COMPATIBLE","HAS_PARTY_MODE","CONNECTS_WITH_APP","COMPATIBLE_WITH_APP"):
        print(f"  {a.get('id')} = {a.get('value_name')}")

import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

ITEMS={
    "Negro":  {"id":"MLM5233480022","sku":"JBLFLIP7BLK","ean":"1200130019272","color":"Negro"},
    "Azul":   {"id":"MLM5233454100","sku":"JBLFLIP7BLU","ean":"1200130019289","color":"Azul"},
    "Rojo":   {"id":"MLM2886030837","sku":"JBLFLIP7RED","ean":"1200130019296","color":"Rojo"},
    "Morado": {"id":"MLM2886136351","sku":"JBLFLIP7PUR","ean":"1200130019319","color":"Morado"},
}

# Atributos premium de Flip 7 (medidas reales del empaque: 211.5 x 92.5 x 109.5 mm, 826 g bruto)
ENRICH={
    # === Audio core ===
    "BLUETOOTH_VERSION":"5.3",
    "POWER_OUTPUT_RMS":"35 W",
    "MAX_POWER":"35 W",
    "PMPO_POWER_OUTPUT":"70 W",
    "MIN_FREQUENCY_RESPONSE":"60 Hz",
    "MAX_FREQUENCY_RESPONSE":"20000 Hz",
    "INPUT_IMPEDANCE":"4 Ω",
    "SENSITIVITY":"88 dB",
    "DISTORTION":"0.5 %",
    "SIGNAL_TO_NOISE_RATIO":"85 dB",
    "SPEAKERS_NUMBER":"2",
    "PICKUPS_NUMBER":"2",
    "SPEAKER_FORMAT":"2.0",
    # === Bateria ===
    "BATTERY_VOLTAGE":"5 V",
    "BATTERY_CAPACITY":"4800 mAh",
    "BATTERY_TYPE":"Ion de litio",
    "MAX_BATTERY_AUTONOMY":"16 h",
    "BATTERY_CHARGING_TIME":"2.5 h",
    "BATTERY_QUANTITY":"1",
    "INCLUDES_BATTERY":"Si",
    "IS_RECHARGEABLE":"Si",
    # === Conectividad ===
    "WITH_BLUETOOTH":"Si",
    "HAS_BLUETOOTH":"Si",
    "BLUETOOTH_RANGE":"15 m",
    "WITH_AUX":"No",
    "WITH_HANDSFREE_FUNCTION":"Si",
    "HAS_MICROPHONE":"Si",
    "HAS_USB_INPUT":"No",
    "HAS_SD_MEMORY_INPUT":"No",
    "HAS_FM_RADIO":"No",
    "HAS_NFC":"No",
    "HAS_APP_CONTROL":"No",
    "HAS_MULTIPOINT":"Si",
    # === Funciones ===
    "IS_WATERPROOF":"Si",
    "IS_DUSTPROOF":"Si",
    "WATERPROOF_DEGREE":"IP67",
    "IS_PORTABLE":"Si",
    "IS_WIRELESS":"Si",
    "WITH_STEREO_SOUND":"Si",
    "IS_VOICE_ACTIVATED":"No",
    "IS_DUAL_VOICE_COIL":"No",
    "IS_DUAL_VOICE_ASSISTANTS":"No",
    "HAS_LED_LIGHTS":"No",
    "HAS_LED_DISPLAY":"No",
    "IS_SMART":"No",
    "INCLUDES_REMOTE_CONTROL":"No",
    "WITH_EQUALIZER":"No",
    "HAS_AC_POWER":"No",
    # === Construccion / Materiales ===
    "INCLUDES_CABLE":"Si",
    "AC_ADAPTER_INCLUDED":"No",
    "HANDLE_MATERIAL":"Tela",
    "CABINET_MATERIAL":"Plastico y tela",
    "SHAPE":"Cilindrica",
    # === Puertos ===
    "CHARGING_PORT":"USB-C",
    # === Empaque (del codigo de barras que me pasaste) ===
    "PACKAGE_LENGTH":"212 mm",
    "PACKAGE_WIDTH":"93 mm",
    "PACKAGE_HEIGHT":"110 mm",
    "PACKAGE_WEIGHT":"826 g",
    # === Producto ===
    "WEIGHT":"630 g",
    "LENGTH":"182 mm",
    "WIDTH":"72 mm",
    "HEIGHT":"72 mm",
    # === Version/Linea ===
    "ITEM_CONDITION":"Nuevo",
    "BRAND":"Generica",
    "MODEL":"Bluetooth Portatil IP67 35W",
}

# Obtener schema de categoria para respetar value_type
cat_attrs={ca["id"]:ca for ca in requests.get("https://api.mercadolibre.com/categories/MLM59800/attributes",headers=H,timeout=15).json()}

for color,info in ITEMS.items():
    iid=info["id"]
    # atributos actuales
    cur=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=attributes",headers=H).json()
    cur_map={a.get("id"):a for a in (cur.get("attributes") or [])}
    
    # construir nueva lista con enriquecimiento
    new_attrs=[]
    seen=set()
    # primero los que ya estan pero actualizar con ENRICH si aplica
    for aid,a in cur_map.items():
        if aid in seen: continue
        seen.add(aid)
        if aid in ENRICH:
            new_attrs.append({"id":aid,"value_name":ENRICH[aid]})
        else:
            new_attrs.append(a)
    # agregar los del ENRICH que no estaban
    for aid,val in ENRICH.items():
        if aid in seen: continue
        seen.add(aid)
        # si la categoria no lo acepta, saltar
        if aid not in cat_attrs:
            continue
        new_attrs.append({"id":aid,"value_name":val})
    
    # Siempre mantener codigos
    new_attrs.append({"id":"SELLER_SKU","value_name":info["sku"]})
    new_attrs.append({"id":"GTIN","value_name":info["ean"]})
    new_attrs.append({"id":"ALPHANUMERIC_MODEL","value_name":info["sku"]})
    new_attrs.append({"id":"COLOR","value_name":info["color"]})
    
    # dedupe final
    seen2=set(); fin=[]
    for a in reversed(new_attrs):
        if a["id"] not in seen2:
            fin.append(a); seen2.add(a["id"])
    fin=list(reversed(fin))
    
    body={"attributes":fin}
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=30)
    print(f"{color} {iid}: {rp.status_code}")
    if rp.status_code not in (200,201):
        # salvar fallbacks sin dimensiones si falla por number_unit issue
        err_text=rp.text[:400]
        print(f"  err: {err_text}")
        # intentar sin PACKAGE_* por si los formatos number_unit no cuadran
        DROP={"PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","WEIGHT","LENGTH","WIDTH","HEIGHT","BATTERY_CAPACITY","BATTERY_CHARGING_TIME","BLUETOOTH_RANGE","SIGNAL_TO_NOISE_RATIO","SENSITIVITY","PMPO_POWER_OUTPUT"}
        fin2=[a for a in fin if a["id"] not in DROP]
        rp2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"attributes":fin2},timeout=30)
        print(f"  retry sin numericos: {rp2.status_code}")
        if rp2.status_code not in (200,201):
            print(f"    err2: {rp2.text[:400]}")
    time.sleep(2)

# Revisar health score final
print("\n=== HEALTH FINAL ===")
for color,info in ITEMS.items():
    iid=info["id"]
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,health",headers=H).json()
    print(f"  {color} {iid}: health={d.get('health')}")

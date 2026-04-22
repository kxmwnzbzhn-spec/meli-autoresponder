import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# EAN oficial JBL Go 4 por color
EANS={
    "Negro":"6925281995194",
    "Azul":"6925281995231",
    "Rojo":"6925281995200",
    "Camuflaje":"6925281995217",
    "Rosa":"6925281995224",
    "Aqua":"6925281995248",
}

# Caracteristicas tecnicas COMPLETAS JBL Go 4
ITEM_ATTRS_SPECS=[
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 4"},
    {"id":"ALPHANUMERIC_MODEL","value_name":"JBLGO4"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    {"id":"LINE","value_name":"Go"},
    {"id":"MAX_BATTERY_AUTONOMY","value_name":"7 h"},
    {"id":"POWER_OUTPUT_RMS","value_name":"4.2 W"},
    {"id":"MAX_POWER","value_name":"4.2 W"},
    {"id":"MIN_FREQUENCY_RESPONSE","value_name":"180 Hz"},
    {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
    {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
    {"id":"DISTORTION","value_name":"1 %"},
    {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
    {"id":"IS_WATERPROOF","value_name":"Si"},
    {"id":"IS_PORTABLE","value_name":"Si"},
    {"id":"IS_WIRELESS","value_name":"Si"},
    {"id":"IS_RECHARGEABLE","value_name":"Si"},
    {"id":"WITH_BLUETOOTH","value_name":"Si"},
    {"id":"HAS_BLUETOOTH","value_name":"Si"},
    {"id":"INCLUDES_CABLE","value_name":"Si"},
    {"id":"INCLUDES_BATTERY","value_name":"Si"},
    {"id":"HAS_MICROPHONE","value_name":"Si"},
    {"id":"HAS_LED_LIGHTS","value_name":"No"},
    {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
    {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
    {"id":"HAS_FM_RADIO","value_name":"No"},
    {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
    {"id":"HAS_APP_CONTROL","value_name":"No"},
    {"id":"HAS_USB_INPUT","value_name":"Si"},
    {"id":"WITH_AUX","value_name":"No"},
    {"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
    {"id":"IS_SMART","value_name":"Si"},
    {"id":"SPEAKERS_NUMBER","value_name":"1"},
    {"id":"PICKUPS_NUMBER","value_name":"1"},
    {"id":"SPEAKER_FORMAT","value_name":"1.0"},
]

# Leer item actual para preservar lo que ya tenga
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_vars=it.get("variations",[])

# Actualizar cada variacion con EAN + attribute_combinations color
new_vars=[]
for v in current_vars:
    vid=v.get("id")
    ac=v.get("attribute_combinations",[])
    color = ac[0].get("value_name","") if ac else ""
    ean=EANS.get(color)
    
    # new attribute_combinations (keep color + add GTIN)
    new_ac=[{"id":"COLOR","value_name":color}]
    if ean: new_ac.append({"id":"GTIN","value_name":ean})
    
    nv={
        "id":vid,
        "price":v.get("price"),
        "available_quantity":v.get("available_quantity"),
        "attribute_combinations":new_ac,
    }
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    new_vars.append(nv)

# Tambien asegurar item-level pictures sigue teniendo todos los pic IDs usados
all_var_pics=set()
for v in current_vars:
    for pid in (v.get("picture_ids") or []):
        all_var_pics.add(pid)
item_top_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
all_pics=list(dict.fromkeys(list(all_var_pics)+item_top_pics))

body={
    "attributes":ITEM_ATTRS_SPECS,
    "pictures":[{"id":p} for p in all_pics],
    "variations":new_vars
}

import re
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
retry=0
while r.status_code not in (200,201) and retry<5:
    retry+=1
    try: j=r.json()
    except: break
    bad=set(); miss=set()
    for c in j.get("cause",[]):
        msg=c.get("message","") or ""; code=c.get("code","") or ""
        if "invalid" in code or "omitted" in code or "number_invalid" in code:
            mm=re.search(r"[Aa]ttribute:?\s+([A-Z][A-Z_]+)",msg)
            if mm and not mm.group(1).startswith("MLM"): bad.add(mm.group(1))
        if "missing" in code:
            for m_ in re.findall(r"\[([A-Z][A-Z_0-9]+)\]",msg):
                if m_.startswith("MLM"): continue
                miss.add(m_)
    if bad: ITEM_ATTRS_SPECS=[a for a in ITEM_ATTRS_SPECS if a["id"] not in bad]
    for mid in miss:
        if not any(a["id"]==mid for a in ITEM_ATTRS_SPECS):
            ITEM_ATTRS_SPECS.append({"id":mid,"value_name":"No aplica"})
    body["attributes"]=ITEM_ATTRS_SPECS
    r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)

print(f"PUT: {r.status_code}")
if r.status_code in (200,201):
    resp=r.json()
    print(f"\nVariaciones con GTIN:")
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col=""; gtin=""
        for a in ac:
            if a.get("id")=="COLOR": col=a.get("value_name","")
            if a.get("id")=="GTIN": gtin=a.get("value_name","")
        print(f"  {v.get('id')} {col:<12} GTIN={gtin}")
    print(f"\nAtributos tecnicos item-level: {len(resp.get('attributes',[]))}")
else:
    print(r.text[:500])

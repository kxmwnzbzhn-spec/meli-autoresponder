import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Spec per item (JBL specs publicly known)
SPECS={
  "MLM5525982716": {  # JBL Go 4 usada caja abierta
    "model":"Go 4","line":"Go","brand":"JBL",
    "bluetooth_v":"5.3","battery_h":7,"watts":4.2,
    "weight_g":190,"width_mm":94,"height_mm":75,"depth_mm":42,
    "gtin":"6925281982989"
  },
  "MLM3025553813": {  # JBL Charge 6 reacond
    "model":"Charge 6","line":"Charge","brand":"JBL",
    "bluetooth_v":"5.4","battery_h":24,"watts":45,
    "weight_g":970,"width_mm":228,"height_mm":98,"depth_mm":98,
    "gtin":"6925281987564"
  },
  "MLM5525381774": {  # JBL Clip 5 usada caja abierta
    "model":"Clip 5","line":"Clip","brand":"JBL",
    "bluetooth_v":"5.3","battery_h":12,"watts":7,
    "weight_g":285,"width_mm":134,"height_mm":86,"depth_mm":46,
    "gtin":"6925281986956"
  }
}

# Get MLM59800 attribute schema
ats=requests.get(f"{API}/categories/MLM59800/attributes",headers=H,timeout=15).json()
valid_ids={a["id"]:a for a in ats}
print(f"MLM59800 attrs available: {len(valid_ids)}")

for iid,spec in SPECS.items():
  print(f"\n=== {iid} ({spec['model']}) ===")
  g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
  current_attrs={a["id"]:a.get("value_name") for a in g.get("attributes",[])}
  print(f"  current attrs set: {len([v for v in current_attrs.values() if v])}/{len(current_attrs)}")
  
  # Build full attr set
  new_attrs=[]
  candidates=[
    ("BRAND", spec["brand"]),
    ("MODEL", spec["model"]),
    ("LINE", spec["line"]),
    ("ITEM_CONDITION", "Usado"),
    ("CONNECTION_TYPE", "Inalámbrica"),
    ("MAIN_COLOR", "Multicolor"),
    ("COLOR", "Multicolor"),
    ("WITH_BLUETOOTH", "Sí"),
    ("BLUETOOTH_VERSION", spec["bluetooth_v"]),
    ("IS_WATER_RESISTANT", "Sí"),
    ("WATER_PROOF_GRADE", "IP67"),
    ("IS_PORTABLE", "Sí"),
    ("IS_RECHARGEABLE", "Sí"),
    ("POWER_SOURCE", "Batería"),
    ("INPUT_VOLTAGE", "5 V"),
    ("SOUND_OUTPUT_POWER", f"{spec['watts']} W"),
    ("BATTERY_LIFE", f"{spec['battery_h']} h"),
    ("AUDIO_INPUT_TYPES", "Bluetooth"),
    ("WEIGHT", f"{spec['weight_g']} g"),
    ("WIDTH", f"{spec['width_mm']} mm"),
    ("HEIGHT", f"{spec['height_mm']} mm"),
    ("DEPTH", f"{spec['depth_mm']} mm"),
    ("PACKAGE_LENGTH", f"{spec['height_mm']+20} mm"),
    ("PACKAGE_WEIGHT", f"{spec['weight_g']+100} g"),
    ("INCLUDES_BUILT_IN_MICROPHONE", "No"),
    ("WITH_USB_INPUT", "No"),
    ("HAS_AUXILIARY_INPUT", "No"),
    ("WITH_FM_RADIO", "No"),
    ("WITH_RGB_LIGHT", "No"),
    ("WITH_VOICE_ASSISTANT", "No"),
    ("WIRELESS_TECHNOLOGIES", "Bluetooth"),
    ("ITEM_INSTALLATION_TYPE", "Portátil"),
    ("GTIN", spec["gtin"]),
  ]
  for aid,val in candidates:
    if aid in valid_ids:
      new_attrs.append({"id":aid,"value_name":val})
  
  print(f"  sending {len(new_attrs)} attrs")
  p=requests.put(f"{API}/items/{iid}",headers=HJ,json={"attributes":new_attrs},timeout=30)
  print(f"  PUT: {p.status_code}")
  if p.status_code>=400:
    # parse warnings/errors to identify problematic attrs
    try:
      err=p.json()
      for c in err.get("cause",[]):
        print(f"    {c.get('code')}: {c.get('message','')[:200]}")
    except: print(f"    raw: {p.text[:500]}")
  else:
    # Verify by re-fetching
    g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    set_attrs=[a for a in g2.get("attributes",[]) if a.get("value_name")]
    print(f"  ✅ now {len(set_attrs)} attrs filled")

import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Per-item complete spec
ITEMS={
  "MLM5525982716": {  # JBL Go 4
    "model":"Go 4","line":"Go","alpha_model":"GO4",
    "main_color_id":"2450295","main_color":"Negro",
    "bt_version":"5.3","battery_h":7,"watts":4.2,
    "weight_g":190,"width_mm":94,"height_mm":75,"depth_mm":42,
    "gtin":"6925281982989"
  },
  "MLM3025553813": {  # JBL Charge 6
    "model":"Charge 6","line":"Charge","alpha_model":"CHARGE6",
    "main_color_id":"2450295","main_color":"Negro",
    "bt_version":"5.4","battery_h":24,"watts":45,
    "weight_g":970,"width_mm":228,"height_mm":98,"depth_mm":98,
    "gtin":"6925281987564"
  },
  "MLM5525381774": {  # JBL Clip 5
    "model":"Clip 5","line":"Clip","alpha_model":"CLIP5",
    "main_color_id":"2450295","main_color":"Negro",
    "bt_version":"5.3","battery_h":12,"watts":7,
    "weight_g":285,"width_mm":134,"height_mm":86,"depth_mm":46,
    "gtin":"6925281986956"
  }
}

ats=requests.get(f"{API}/categories/MLM59800/attributes",headers=H,timeout=15).json()
valid={a["id"]:a for a in ats}

for iid,spec in ITEMS.items():
  print(f"\n=== {iid} ({spec['model']}) ===")
  g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
  current={a.get("id"):(a.get("value_name") or a.get("value_id")) for a in g.get("attributes",[])}
  filled=sum(1 for v in current.values() if v)
  total=len(current)
  print(f"  before: {filled}/{total} filled")
  
  # Build attrs to PATCH (only add missing OR overwrite key ones)
  to_set=[]
  # MAIN_COLOR (list with value_id)
  if not current.get("MAIN_COLOR"):
    to_set.append({"id":"MAIN_COLOR","value_id":spec["main_color_id"],"value_name":spec["main_color"]})
  # COLOR (free string)
  if not current.get("COLOR") and "COLOR" in valid:
    to_set.append({"id":"COLOR","value_name":spec["main_color"]})
  # BLUETOOTH_VERSION (probably free string)
  if not current.get("BLUETOOTH_VERSION") and "BLUETOOTH_VERSION" in valid:
    to_set.append({"id":"BLUETOOTH_VERSION","value_name":spec["bt_version"]})
  # WIRELESS_TECHNOLOGIES
  if not current.get("WIRELESS_TECHNOLOGIES") and "WIRELESS_TECHNOLOGIES" in valid:
    to_set.append({"id":"WIRELESS_TECHNOLOGIES","value_name":"Bluetooth"})
  # MAX_FREQUENCY_RESPONSE / MIN_FREQUENCY_RESPONSE (already present in Go4, skip)
  # SOUND_OUTPUT_POWER alt key
  if not current.get("SOUND_OUTPUT_POWER") and "SOUND_OUTPUT_POWER" in valid:
    to_set.append({"id":"SOUND_OUTPUT_POWER","value_name":f"{spec['watts']} W"})
  # COMPATIBLE_DEVICES
  if not current.get("COMPATIBLE_DEVICES") and "COMPATIBLE_DEVICES" in valid:
    to_set.append({"id":"COMPATIBLE_DEVICES","value_name":"Celulares,Tablets,Notebooks,PC"})
  # INCLUDES_USB_CABLE
  if not current.get("INCLUDES_USB_CABLE") and "INCLUDES_USB_CABLE" in valid:
    to_set.append({"id":"INCLUDES_USB_CABLE","value_name":"Sí"})
  # ITEM_INSTALLATION_TYPE
  if not current.get("ITEM_INSTALLATION_TYPE") and "ITEM_INSTALLATION_TYPE" in valid:
    to_set.append({"id":"ITEM_INSTALLATION_TYPE","value_name":"Portátil"})
  
  print(f"  adding {len(to_set)} attrs:")
  for a in to_set: print(f"    + {a['id']} = {a.get('value_name','')}")
  
  if to_set:
    p=requests.put(f"{API}/items/{iid}",headers=HJ,json={"attributes":to_set},timeout=30)
    print(f"  PUT: {p.status_code}")
    if p.status_code>=400:
      try:
        err=p.json()
        for c in err.get("cause",[]):
          print(f"    {c.get('code','')}: {c.get('message','')[:180]}")
      except: print(f"    raw: {p.text[:400]}")
    else:
      # verify
      g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
      f2=sum(1 for a in g2.get("attributes",[]) if a.get("value_name") or a.get("value_id"))
      print(f"  ✅ after: {f2} attrs filled (gain: +{f2-filled})")
  else:
    print("  nothing new to add (already complete)")

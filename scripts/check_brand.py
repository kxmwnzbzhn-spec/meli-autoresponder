import os, requests, json
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
import time
for a in range(4):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tok=r.json(); AT=tok["access_token"]; print(f"[ROTATED RT] {tok['refresh_token']}")
H={"Authorization":f"Bearer {AT}"}

# Brand attribute spec
a=requests.get("https://api.mercadolibre.com/categories/MLM171894/attributes",headers=H,timeout=15).json()
for at in a:
  if at.get("id")=="BRAND":
    print("BRAND attribute:")
    print(json.dumps(at,indent=2)[:3000])
    break

# Test publishing with different brands quickly via validate
TITLE_BASE="Aceite Capilar Premium Brillo Y Nutricion 100ml Importado"
def build(brand):
  return {
    "title":TITLE_BASE,
    "category_id":"MLM171894",
    "price":1199,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":[{"source":"https://http2.mlstatic.com/D_NQ_NP_734138-MLU74911148706_032024-F.jpg"}],
    "attributes":[
      {"id":"BRAND","value_name":brand},
      {"id":"MODEL","value_name":"Premium Hair Oil"},
      {"id":"CONSISTENCY","value_name":"Aceite"},
      {"id":"NET_VOLUME","value_name":"100 mL"},
      {"id":"NET_WEIGHT","value_name":"100 g"},
      {"id":"UNITS_PER_PACK","value_name":"1"},
      {"id":"GTIN","value_name":"3474636397495"},
      {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    ],
  }
H2={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
brands_to_try=["L'Oréal Professionnel","L'Oréal","Wella","Schwarzkopf Professional","Redken","Tresemmé","Pantene","Sin marca","Otra"]
for brand in brands_to_try:
  v=requests.post("https://api.mercadolibre.com/items/validate",headers=H2,json=build(brand),timeout=20)
  result="OK"
  if v.status_code>=300:
    try:
      j=v.json(); errs=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      if errs:
        result="ERR: "+errs[0].get("code","")+" - "+errs[0].get("message","")[:80]
      else:
        result="warnings only"
    except: result=v.text[:120]
  print(f"  brand='{brand}': {result}")

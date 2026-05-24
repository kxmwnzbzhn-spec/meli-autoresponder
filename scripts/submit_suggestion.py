import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}
PICS = ["897724-MLM112154514469_052026","840560-MLM112155272235_052026",
        "751916-MLM111152110628_052026","606658-MLM112155475559_052026"]

variants = {
 "A_values_value_name": [
    {"id":"BRAND","values":[{"value_name":"The Alchemia Lab"}]},
    {"id":"PERFUME_NAME","values":[{"value_name":"Flor De Nopal"}]},
    {"id":"UNIT_VOLUME","values":[{"value_name":"100 mL"}]},
 ],
 "B_uv_struct": [
    {"id":"BRAND","values":[{"value_name":"The Alchemia Lab"}]},
    {"id":"PERFUME_NAME","values":[{"value_name":"Flor De Nopal"}]},
    {"id":"UNIT_VOLUME","values":[{"value_struct":{"number":100,"unit":"mL"}}]},
 ],
 "C_brandname_only_values": [
    {"id":"BRAND","values":[{"value_name":"The Alchemia Lab"}]},
    {"id":"PERFUME_NAME","values":[{"value_name":"Flor De Nopal"}]},
 ],
 "D_value_name_plus_struct": [
    {"id":"BRAND","value_name":"The Alchemia Lab"},
    {"id":"PERFUME_NAME","value_name":"Flor De Nopal"},
    {"id":"UNIT_VOLUME","value_struct":{"number":100,"unit":"mL"}},
 ],
}

def post(attrs):
    body={"domain_id":DOM,"catalog_product_id":CPID,"type":"edit","attributes":attrs,
          "pictures":[{"id":p} for p in PICS]}
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    try: j=r.json()
    except: j=r.text
    return r.status_code,j

for name,attrs in variants.items():
    code,j=post(attrs)
    cause=""
    if isinstance(j,dict):
        cs=j.get("cause") or []
        cause=" | ".join(f"{c.get('code')}:{c.get('message','')[:70]}" for c in cs) if cs else json.dumps(j,ensure_ascii=False)[:200]
    print(f"[{name:26}] http={code} {cause}")
    if code<300:
        print("  >>> SUCCESS:", json.dumps(j,ensure_ascii=False)[:300]); break
print("DONE")

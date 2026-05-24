import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}

PICS = ["897724-MLM112154514469_052026","840560-MLM112155272235_052026",
        "751916-MLM111152110628_052026","606658-MLM112155475559_052026"]
NOTES = ["Madera ámbar","Almizcle blanco","Azafrán Mexicano","Azúcar Cristalizada",
         "Caramelo Tostado","Cedro Blanco De Atlas","Flor De Nopal","Jazmín sambac",
         "Maderas Secas","Resina De Copal"]

singles = [
    {"id":"BRAND","value_name":"The Alchemia Lab"},
    {"id":"LINE","value_name":"Mexico En La Piel"},
    {"id":"PERFUME_NAME","value_name":"Flor De Nopal"},
    {"id":"VERSION","value_name":"Original"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"APPLICATION_FORMAT","value_name":"Spray"},
    {"id":"IS_REFILLABLE","value_name":"Sí"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"ORIGIN_COUNTRY","value_name":"México"},
    {"id":"RELEASE_YEAR","value_name":"2025"},
    {"id":"IS_CRUELTY_FREE","value_name":"Sí"},
    {"id":"IS_VEGAN","value_name":"No"},
    {"id":"IS_ALCOHOL_FREE","value_name":"No"},
    {"id":"IS_SET","value_name":"No"},
    {"id":"INCLUDES_CASE","value_name":"Sí"},
]
mpn      = [{"id":"MPN","value_name":"TAL-FDN-100ML"}]
families = [{"id":"OLFACTORY_FAMILIES","value_name":"Gourmand"}]
notes_v  = [{"id":"OLFACTORY_NOTES","values":[{"value_name":n} for n in NOTES]}]
notes_s  = [{"id":"OLFACTORY_NOTES","value_name":", ".join(NOTES)}]
core     = [{"id":"BRAND","value_name":"The Alchemia Lab"},
            {"id":"PERFUME_NAME","value_name":"Flor De Nopal"},
            {"id":"UNIT_VOLUME","value_name":"100 mL"}]

attempts = [
    ("full(values-notes)", singles+families+notes_v+mpn),
    ("full(string-notes)", singles+families+notes_s+mpn),
    ("singles+fam+mpn",    singles+families+mpn),
    ("singles+mpn",        singles+mpn),
    ("singles",            singles),
    ("core+mpn",           core+mpn),
    ("core",               core),
]

def post(attrs, with_pics=True):
    body={"domain_id":DOM,"catalog_product_id":CPID,"type":"edit","attributes":attrs}
    if with_pics: body["pictures"]=[{"id":p} for p in PICS]
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=40)
    try: j=r.json()
    except: j=r.text
    return r.status_code, j

for name, attrs in attempts:
    code, j = post(attrs)
    cause = ""
    if isinstance(j, dict):
        cs = j.get("cause") or []
        cause = " | ".join(f"{c.get('code')}:{c.get('message','')[:60]} refs={c.get('references')}" for c in cs) if cs else json.dumps(j)[:160]
    print(f"[{name:20}] http={code}  {cause}")
    if code < 300:
        print("  SUCCESS body:", json.dumps(j, ensure_ascii=False)[:400])
        break
print("DONE")

import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}

PICS = [
    "897724-MLM112154514469_052026",  # principal fondo blanco
    "840560-MLM112155272235_052026",  # espiritu
    "751916-MLM111152110628_052026",  # ofrenda
    "606658-MLM112155475559_052026",  # ritual
]
NOTES = ["Madera ámbar","Almizcle blanco","Azafrán Mexicano","Azúcar Cristalizada",
         "Caramelo Tostado","Cedro Blanco De Atlas","Flor De Nopal","Jazmín sambac",
         "Maderas Secas","Resina De Copal"]

# duración aproximada: buscar valor válido (EDP = larga)
dur_val = None
try:
    ts = requests.get(f"{API}/domains/{DOM}/technical_specs", headers={"Authorization": f"Bearer {T}"}, timeout=30).json()
    found = []
    def walk(n):
        if isinstance(n, dict):
            if n.get("id") == "APPROXIMATE_DURATION":
                for v in (n.get("values") or []): found.append(v.get("name"))
            for v in n.values(): walk(v)
        elif isinstance(n, list):
            for v in n: walk(v)
    walk(ts)
    print("APPROXIMATE_DURATION values:", found)
    for cand in ("Más de 12 horas","Larga","8 a 12 horas","Más de 8 horas","Prolongada"):
        if cand in found: dur_val = cand; break
except Exception as e:
    print("dur lookup exc", e)

attrs = [
    {"id": "BRAND", "value_name": "The Alchemia Lab"},          # CORRECCIÓN
    {"id": "MPN", "values": [{"value_name": "TAL-FDN-100ML"}]},       # CORRECCIÓN
    {"id": "LINE", "value_name": "Mexico En La Piel"},
    {"id": "PERFUME_NAME", "value_name": "Flor De Nopal"},
    {"id": "VERSION", "value_name": "Original"},
    {"id": "GENDER", "value_name": "Sin género"},
    {"id": "PERFUME_TYPE", "value_name": "Eau de parfum"},
    {"id": "APPLICATION_FORMAT", "value_name": "Spray"},
    {"id": "IS_REFILLABLE", "value_name": "Sí"},
    {"id": "UNIT_VOLUME", "value_name": "100 mL"},
    {"id": "ORIGIN_COUNTRY", "value_name": "México"},
    {"id": "RELEASE_YEAR", "value_name": "2025"},
    {"id": "IS_CRUELTY_FREE", "value_name": "Sí"},
    {"id": "IS_VEGAN", "value_name": "No"},
    {"id": "IS_ALCOHOL_FREE", "value_name": "No"},
    {"id": "IS_SET", "value_name": "No"},
    {"id": "INCLUDES_CASE", "value_name": "Sí"},
    {"id": "OLFACTORY_FAMILIES", "values": [{"value_name": "Gourmand"}]},
    {"id": "OLFACTORY_NOTES", "values": [{"value_name": n} for n in NOTES]},
]
if dur_val:
    attrs.append({"id": "APPROXIMATE_DURATION", "value_name": dur_val})

body = {
    "domain_id": DOM,
    "catalog_product_id": CPID,
    "type": "edit",
    "attributes": attrs,
    "pictures": [{"id": p} for p in PICS],
}
print("\n=== POST /catalog_suggestions ===")
r = requests.post(f"{API}/catalog_suggestions", headers=HJ, json=body, timeout=40)
print("http=", r.status_code)
print(json.dumps(r.json(), ensure_ascii=False)[:1200] if r.headers.get("content-type","").startswith("application/json") else r.text[:1200])
print("DONE")

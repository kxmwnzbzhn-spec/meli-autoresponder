"""
PILOTO: crear catalog_suggestion Audífonos ASVA Buds 2 (MLM-HEADPHONES).
Token ASVA via Worker. Descarga portada de Drive -> sube a MELI -> POST /catalog_suggestions.
Formato atributos: {"id":ATTR,"values":[{"name":"Valor"}]}  (NO value_name).
"""
import os, json, requests

EP = "https://meli-webhook.elite-market-1779161651.workers.dev/token"
API = "https://api.mercadolibre.com"
AT = requests.get(f"{EP}/ASVA", headers={"Authorization": f"Bearer {os.environ['TOKEN_SHARED']}"}, timeout=30).json()["access_token"]
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}

me = requests.get(f"{API}/users/me", headers=H, timeout=15).json()
print("ASVA uid:", me.get("id"), me.get("nickname"))

DRIVE_PHOTO_IDS = ["1jEhTKCXJFRcNjo40BnHtEIz-0yA98k2C"]  # portada fondo blanco pública

TITLE = ("Audífonos Inalámbricos ASVA Electronics Buds 2 Bluetooth TWS In-ear Blancos "
         "con Estuche de Carga, Micrófono Integrado, Control Táctil y Manos Libres")

ATTRIBUTES = [
    {"id": "BRAND", "values": [{"name": "ASVA Electronics"}]},
    {"id": "MODEL", "values": [{"name": "Buds 2"}]},
    {"id": "COLOR", "values": [{"name": "Blanco"}]},
    {"id": "HEADPHONE_FORMAT", "values": [{"name": "In-ear"}]},
    {"id": "IS_WIRELESS", "values": [{"name": "Sí"}]},
    {"id": "WITH_BLUETOOTH", "values": [{"name": "Sí"}]},
    {"id": "WITH_TWS_TECHNOLOGY", "values": [{"name": "Sí"}]},
    {"id": "WITH_MICROPHONE", "values": [{"name": "Sí"}]},
    {"id": "WITH_HANDS_FREE_MODE", "values": [{"name": "Sí"}]},
    {"id": "INCLUDES_CHARGING_CASE", "values": [{"name": "Sí"}]},
    {"id": "IS_MONAURAL", "values": [{"name": "No"}]},
    {"id": "IS_INFANT", "values": [{"name": "No"}]},
    {"id": "WITH_MP3_PLAYER", "values": [{"name": "No"}]},
    {"id": "WITH_FM_RADIO", "values": [{"name": "No"}]},
]

def dl(fid):
    r = requests.get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t", timeout=90)
    r.raise_for_status()
    return r.content

pics = []
for fid in DRIVE_PHOTO_IDS:
    img = dl(fid)
    rp = requests.post(f"{API}/pictures/items/upload", headers=H, files={"file": ("portada.png", img, "image/png")}, timeout=120)
    print("pic upload", rp.status_code, rp.text[:200])
    if rp.status_code in (200, 201):
        pics.append({"id": rp.json()["id"]})

body = {
    "site_id": "MLM",
    "domain_id": "MLM-HEADPHONES",
    "type": "EDIT",
    "title": TITLE,
    "attributes": ATTRIBUTES,
    "pictures": pics,
}
print("\n=== BODY ===")
print(json.dumps(body, ensure_ascii=False, indent=2)[:1800])

r = requests.post(f"{API}/catalog_suggestions", headers=HJ, json=body, timeout=40)
print("\n=== POST /catalog_suggestions ===")
print("http", r.status_code)
try:
    rb = r.json()
    print(json.dumps(rb, ensure_ascii=False, indent=2)[:2500])
    sid = rb.get("id") or rb.get("suggestion_id")
    if sid:
        print(f"\n>>> SUGGESTION_ID = {sid}")
        det = requests.get(f"{API}/catalog_suggestions/{sid}", headers=H, timeout=20)
        print("detail", det.status_code, det.text[:800])
except Exception as e:
    print("raw:", r.text[:1000])

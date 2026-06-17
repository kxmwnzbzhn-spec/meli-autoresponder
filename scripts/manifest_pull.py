"""Pulls pending shipments for multiple accounts and outputs a JSON manifest
with photo URLs per variation. Used by the public lookup web app.

Output: data/manifest.json
"""
import os, json, sys, requests, time
from datetime import datetime, timezone, timedelta
from collections import OrderedDict

APP_ID = os.environ.get("MELI_APP_ID","2008666770714005")

# === DEVOLUCIONES (anti-confusion) ===
SB_URL = os.environ.get("SUPABASE_URL","").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY","")
def load_devolucion_map():
    if not (SB_URL and SB_KEY): return {}
    try:
        r = requests.get(f"{SB_URL}/rest/v1/meli_devolucion_items",
            params={"select":"item_id,display_name,modelo"},
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}"}, timeout=10)
        if r.status_code == 200:
            return {row["item_id"]: row for row in r.json()}
    except Exception as e:
        print(f"[devolucion] load fail: {e}")
    return {}
DEV_MAP = load_devolucion_map()
print(f"[devolucion] {len(DEV_MAP)} item_ids marcados como devolución")
APP_SECRET = os.environ["MELI_APP_SECRET"]
TZ = timezone(timedelta(hours=-6))
NOW_ISO = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ALLOWED_SUBS = {"printed", "ready_to_print"}

ACCOUNTS = [
    {"name":"Claribel", "rt_env":"MELI_REFRESH_TOKEN_CLARIBEL"},
    {"name":"Asva",     "rt_env":"MELI_REFRESH_TOKEN_ASVA"},
    {"name":"Adrian",   "rt_env":"MELI_REFRESH_TOKEN_AH"},
    {"name":"Yiriam",   "rt_env":"MELI_REFRESH_TOKEN_YC_NEW"},
]

def tok(rt):
    r = requests.post("https://api.mercadolibre.com/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":rt}, timeout=15).json()
    return r.get("access_token")

ITEM_CACHE = {}
def get_item_full(item_id, H):
    if item_id in ITEM_CACHE: return ITEM_CACHE[item_id]
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=H, timeout=10)
        if r.status_code == 200:
            ITEM_CACHE[item_id] = r.json()
            return r.json()
    except: pass
    ITEM_CACHE[item_id] = {}
    return {}

def get_variation_photo(item_full, variation_id):
    """Try to find the specific variation's photo. Fallback to main item photo."""
    pics_index = {p.get("id"): p.get("secure_url") for p in item_full.get("pictures", []) if p.get("id")}
    if variation_id:
        for v in item_full.get("variations", []):
            if str(v.get("id")) == str(variation_id):
                for pid in v.get("picture_ids", []):
                    if pid in pics_index:
                        return pics_index[pid]
                # picture_ids reference IDs not in main pictures list — fetch separately
                if v.get("picture_ids"):
                    pid = v["picture_ids"][0]
                    try:
                        r = requests.get(f"https://api.mercadolibre.com/pictures/{pid}", timeout=5)
                        if r.status_code == 200:
                            return r.json().get("secure_url")
                    except: pass
    # fallback: thumbnail
    pics = item_full.get("pictures", [])
    if pics: return pics[0].get("secure_url")
    return item_full.get("thumbnail")

def get_color(item_obj, item_full):
    """1) variation_attributes from order item; 2) variation in full item; 3) None."""
    for a in (item_obj.get("variation_attributes") or []):
        if a.get("id") == "COLOR" or "color" in (a.get("name","") or "").lower():
            v = a.get("value_name", "").strip()
            if v: return v.title().replace("Color ","")
    vid = item_obj.get("variation_id")
    if vid:
        for v in item_full.get("variations", []):
            if str(v.get("id")) == str(vid):
                for a in v.get("attribute_combinations", []):
                    if a.get("id") == "COLOR":
                        val = a.get("value_name","").strip()
                        if val: return val.title().replace("Color ","")
    return None

def get_size(item_obj, item_full):
    """Devuelve la talla del producto. Similar a get_color pero busca SIZE.
       1) variation_attributes from order item; 2) variation in full item; 3) None."""
    for a in (item_obj.get("variation_attributes") or []):
        aid = a.get("id","")
        anm = (a.get("name","") or "").lower()
        if aid == "SIZE" or "talla" in anm or "size" in anm:
            v = a.get("value_name", "").strip()
            if v: return v
    vid = item_obj.get("variation_id")
    if vid:
        for v in item_full.get("variations", []):
            if str(v.get("id")) == str(vid):
                for a in v.get("attribute_combinations", []):
                    if a.get("id") == "SIZE":
                        val = a.get("value_name","").strip()
                        if val: return val
    return None


# === CÓDIGOS INTERNOS (mismo mapeo que labels_one.py) ===
MODEL_CODES = {
    "Charge6":"CH6","Charge5":"CH5","Charge4":"CH4","Go4":"GO4","Go3":"GO3","Go2":"GO2",
    "Clip5":"CL5","Clip4":"CL4","Clip3":"CL3","Flip7":"FL7","Flip6":"FL6","Flip5":"FL5",
    "Xtreme4":"XT4","Xtreme3":"XT3","Boombox3":"BB3","Boombox4":"BB4","Pulse5":"PL5",
    "SoundLink":"SLK","Soundlink":"SLK","SoundlinkHome":"SLH","SoundlinkMini":"SLM",
    "SoundlinkFlex":"SLF","SoundLinkHome":"SLH","SoundLinkMini":"SLM","SoundLinkFlex":"SLF",
    "XB100":"XB1","XB13":"X13","XB23":"X23","Grip":"GRP","Pulse4":"PL4",
}
COLOR_CODES = {
    "Negro":"NG","Negra":"NG","Black":"NG","Blanco":"BL","Blanca":"BL","White":"BL",
    "Rojo":"RJ","Roja":"RJ","Red":"RJ","Rosa":"RS","Pink":"RS","Morado":"MR",
    "Violeta":"MR","Purple":"MR","Azul":"AZ","Blue":"AZ","Azul Marino":"MAR",
    "Aqua":"AQ","Celeste":"CL","Verde":"VD","Green":"VD","Amarillo":"AMA",
    "Yellow":"AMA","Naranja":"NA","Orange":"NA","Gris":"GR","Gray":"GR","Grey":"GR",
    "Plata":"PT","Silver":"PT","Dorado":"DR","Gold":"DR","Camuflaje":"CMF","Camo":"CMF",
}
GENERIC_CODES = [
    ("alma de tenochtitlan","ALMA"),("flor de nopal","NOPAL"),("guerrero sol","GSOL"),
    ("xibalba","XIB"),("xochicopal","XOCH"),("tlaloc","TLA"),("dominio del fuego","DFG"),
    ("cenote azul","CEN"),("templo oscuro","TMP"),("corazon de copal","COP"),
    ("kukulcan","KUK"),("calvin klein","CK"),("le male","LMP"),("dashcam","DSC"),
    ("mandarin sky","MSKY"),
]
def to_code(model, color, size=None, title_full=""):
    import unicodedata
    def _na(s): return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")
    if title_full:
        tl = _na(title_full).lower()
        for kw, c_ in GENERIC_CODES:
            if kw in tl:
                base = c_
                return f"{base}-{size}" if size else base
    code_m = None
    if model:
        m = model.replace(" ", "")
        code_m = MODEL_CODES.get(m)
        if not code_m:
            for k, v in MODEL_CODES.items():
                if k.lower() == m.lower(): code_m = v; break
    if not code_m and model:
        cleaned = "".join(c for c in model if c.isalnum())
        code_m = cleaned[:3].upper() if cleaned else "???"
    if not code_m: code_m = "???"
    code_c = None
    if color:
        cn = _na(color).strip().title()
        code_c = COLOR_CODES.get(cn) or COLOR_CODES.get(color.strip().title())
        if not code_c:
            code_c = "".join(ch for ch in cn if ch.isalpha())[:2].upper() or "??"
    parts = [code_m]
    if code_c: parts.append(code_c)
    if size:   parts.append(str(size))
    return "-".join(parts)


def clean_title_short(title, color):
    """Shorten title for display: model name + color."""
    if not title: return color or "?"
    t = title.lower()
    model = None
    for m in ["go 4","go4","go 3","go3","go 2","go2","charge 6","charge6","charge 5","charge5",
             "clip 5","clip5","clip 4","clip4","flip 7","flip7","flip 6","flip6","flip 5","flip5",
             "xtreme 4","xtreme4","xtreme 3","xtreme3","boombox 3","boombox3","partybox",
             "xb100","xb13","xb23","srs-xb","soundlink","minilink","grip","pulse 5","pulse5"]:
        if m in t:
            model = m.replace(" ","").title()
            break
    if not model:
        words = title.replace("JBL","").replace("Sony","").replace("Bose","").strip().split()
        model = " ".join(words[:2])[:20]
    parts = [model]
    if color: parts.append(color)
    return " ".join(parts)

def collect_account(account):
    nm = account["name"]
    rt = os.environ.get(account["rt_env"], "")
    if not rt:
        print(f"  [{nm}] NO token in env", flush=True)
        return []
    at = tok(rt)
    if not at:
        print(f"  [{nm}] token refresh failed", flush=True)
        return []
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
    uid = me.get("id")
    if not uid:
        print(f"  [{nm}] /users/me failed", flush=True)
        return []
    nick = me.get("nickname","?")
    print(f"  [{nm}] uid={uid} nick={nick}", flush=True)
    # Pull orders to get ship_ids
    orders = []
    off = 0
    while True:
        r = requests.get("https://api.mercadolibre.com/orders/search",
            params={"seller":uid,"order.status":"paid","sort":"date_desc","limit":50,"offset":off},
            headers=H, timeout=15).json()
        orders.extend(r.get("results", []))
        off += 50
        if off >= r.get("paging", {}).get("total", 0) or off >= 500: break
    # Aggregate orders by shipping.id
    obs = {}
    for o in orders:
        sid = (o.get("shipping") or {}).get("id")
        if sid: obs.setdefault(sid, []).append(o)
    ships = []
    for sid, ord_list in obs.items():
        try:
            sh = requests.get(f"https://api.mercadolibre.com/shipments/{sid}", headers=H, timeout=10).json()
            st = sh.get("status"); sub = sh.get("substatus")
            if st != "ready_to_ship" or sub not in ALLOWED_SUBS: continue
            products = []; has_used = False
            for ord_o in ord_list:
                for it in ord_o.get("order_items", []):
                    io = it.get("item") or {}
                    iid = io.get("id")
                    if not iid: continue
                    full = get_item_full(iid, H)
                    color = get_color(io, full)
                    size  = get_size(io, full)
                    photo = get_variation_photo(full, io.get("variation_id"))
                    title_full = io.get("title") or full.get("title","")
                    name_short = clean_title_short(title_full, color)
                    cond = full.get("condition","new")
                    if cond == "used": has_used = True
                    # Detectar modelo simple del title para to_code
                    _tl = (title_full or "").lower()
                    _model = None
                    for _kw in ["charge6","charge5","charge4","go4","go3","go2","clip5","clip4","clip3","flip7","flip6","flip5","xtreme4","xtreme3","boombox3","boombox4","pulse5","soundlink","xb100","xb13","xb23","grip"]:
                        if _kw in _tl.replace(" ",""):
                            _model = _kw.capitalize().replace("Soundlink","Soundlink")
                            break
                    code = to_code(_model, color, size, title_full)
                    # Override si es devolución
                    is_devolucion = False
                    devolucion_name = None
                    if iid in DEV_MAP:
                        is_devolucion = True
                        devolucion_name = DEV_MAP[iid].get("display_name")
                    products.append({
                        "is_devolucion": is_devolucion,
                        "devolucion_name": devolucion_name,
                        "code": code,
                        "name_short": name_short,
                        "title_full": title_full,
                        "color": color,
                        "size": size,
                        "qty": it.get("quantity", 1),
                        "condition": cond,
                        "photo_url": photo,
                        "item_id": iid,
                        "variation_id": io.get("variation_id"),
                    })
            if not products: continue
            buyer = (ord_list[0].get("buyer") or {}).get("nickname", "?")
            sid_str = str(sid)
            ships.append({
                "sid": sid,
                "sid_str": sid_str,
                "sid_last4": sid_str[-4:],
                "sid_last6": sid_str[-6:],
                "account": nm,
                "buyer": buyer,
                "n_products": len(products),
                "has_used": has_used,
                "products": products,
            })
            time.sleep(0.03)
        except Exception as e:
            print(f"  [{nm}] err {sid}: {str(e)[:80]}", flush=True)
    print(f"  [{nm}] {len(ships)} shipments", flush=True)
    return ships

def main():
    all_ships = []
    counts = {}
    for a in ACCOUNTS:
        print(f"\n=== {a['name']} ===", flush=True)
        s = collect_account(a)
        all_ships.extend(s)
        counts[a["name"]] = len(s)
    manifest = {
        "generated_at": NOW_ISO,
        "counts_by_account": counts,
        "total": len(all_ships),
        "shipments": all_ships,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",",":"))
    print(f"\n✅ Manifest: {len(all_ships)} shipments · {os.path.getsize('data/manifest.json')} bytes")

if __name__ == "__main__":
    main()

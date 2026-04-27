"""
Responder Qs en items pausados: reactivar temporal → responder → re-pausar.
"""
import os, requests, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

# Skip Raymundo — items hardpaused intencionalmente
SKIP_ACCOUNTS = {"RAYMUNDO"}

GENERIC_ANSWER = "Buen dia, gracias por su pregunta. Le invito a revisar la descripcion completa de la publicacion donde estan todas las caracteristicas y especificaciones del producto. Si tiene alguna duda especifica con gusto le ayudamos. Saludos cordiales."

total_answered = 0
total_failed = 0

for label, env_var in ACCOUNTS:
    if label in SKIP_ACCOUNTS:
        print(f"\n=== {label}: SKIPPED (hard-paused) ===")
        continue
    
    RT = os.environ.get(env_var, "")
    if not RT:
        print(f"\n=== {label}: NO TOKEN ===")
        continue
    
    print(f"\n=== {label} ===")
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token",
            data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
            timeout=20).json()
        H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
        USER_ID = me["id"]
    except Exception as e:
        print(f"  auth err: {e}")
        continue
    
    # Get unanswered Qs
    qs = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("questions", [])
        if not b: break
        qs.extend(b)
        offset += 50
        if offset >= rr.get("total", 0): break
    
    print(f"  unanswered: {len(qs)}")
    
    items_to_reactivate = set()
    for q in qs:
        iid = q.get("item_id")
        if iid: items_to_reactivate.add(iid)
    
    # Verificar status de cada item
    item_status = {}
    for iid in items_to_reactivate:
        g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,status",headers=H,timeout=10).json()
        item_status[iid] = g.get("status")
    
    # Reactivar paused
    paused_temporal = []
    for iid, st in item_status.items():
        if st == "paused":
            rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"active"},timeout=15)
            if rp.status_code == 200:
                paused_temporal.append(iid)
                print(f"  ▶️  reactivado temporal {iid}")
            time.sleep(0.2)
    
    # Responder
    for q in qs:
        qid = q.get("id")
        text = q.get("text","")
        iid = q.get("item_id")
        rp = requests.post("https://api.mercadolibre.com/answers",
            headers=H, json={"question_id": qid, "text": GENERIC_ANSWER}, timeout=20)
        if rp.status_code in (200, 201):
            total_answered += 1
            print(f"  ✅ {qid} '{text[:40]}' [{iid}]")
        else:
            total_failed += 1
            print(f"  ❌ {qid} {rp.status_code}: {rp.text[:120]}")
        time.sleep(0.5)
    
    # Re-pausar los temporales
    for iid in paused_temporal:
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
        time.sleep(0.2)
    print(f"  ⏸️  re-pausados: {len(paused_temporal)}")

print(f"\n=== TOTAL: {total_answered} respondidas, {total_failed} fallidas ===")

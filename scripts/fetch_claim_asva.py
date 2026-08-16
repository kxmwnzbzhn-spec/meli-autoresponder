import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}
Hp={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CLAIM_ID = "5559906352"
MSG = "Buen dia, gracias por tu mensaje. Como tu mismo indicas el producto llego bien. La percepcion de duracion de una fragancia es totalmente subjetiva: depende de la agudeza olfativa, adaptacion al aroma, tipo de piel, quimica corporal, hidratacion y ambiente. No constituye defecto del producto. Reclamo infundado por criterio subjetivo. Gracias."
print(f"MSG len: {len(MSG)}")

# --- POST message ---
print(f"\n=== POST MESSAGE claim {CLAIM_ID} ===")
# Try main endpoint
r1 = requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
                   headers=Hp,
                   json={"receiver_role":"complainant","message":MSG},
                   timeout=25)
print(f"attempt 1 [/post-purchase/v1/claims/{CLAIM_ID}/messages]: {r1.status_code}")
print(f"  body: {r1.text[:600]}")

if r1.status_code >= 400:
    # Try alternate v1 with only message field
    r2 = requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
                       headers=Hp,
                       json={"message":MSG},
                       timeout=25)
    print(f"attempt 2 [message only]: {r2.status_code} body: {r2.text[:400]}")

    # Try multipart form
    if r2.status_code >= 400:
        m = requests.post(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages",
                          headers={"Authorization":f"Bearer {AT}"},
                          data={"message":MSG,"receiver_role":"complainant"},
                          timeout=25)
        print(f"attempt 3 [form-data]: {m.status_code} body: {m.text[:400]}")

    # Try newer messages endpoint
    if r2.status_code >= 400:
        r4 = requests.post(f"https://api.mercadolibre.com/messages/action-guide?tag=post_sale&role=respondent&claim_id={CLAIM_ID}",
                           headers=Hp,
                           json={"receiver_role":"complainant","message":MSG},
                           timeout=25)
        print(f"attempt 4 [messages/action-guide]: {r4.status_code} body: {r4.text[:400]}")

# --- Verify by re-fetching messages ---
print(f"\n=== VERIFY messages after post ===")
mv = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{CLAIM_ID}/messages", headers=H, timeout=15).json()
if isinstance(mv, list):
    print(f"total mensajes ahora: {len(mv)}")
    for m in mv[-3:]:
        print(f"  {m.get('date_created')} {m.get('sender_role')}->{m.get('receiver_role')}: '{m.get('message','')[:120]}'")
else:
    print(json.dumps(mv, indent=2)[:1000])

# --- SEARCH CK boxers claims con imitacion jul-ago ---
print(f"\n\n========== SEARCH CK BOXERS IMITATION CLAIMS ==========")
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
SELLER_ID = me.get("id")

# Get all claims (all statuses) date_created from 2026-07-01
all_claims = []
for status in ["opened","closed","waiting_for_documentation"]:
    for role in ["respondent","complainant"]:
        offset = 0
        while offset < 500:
            r = requests.get(
                f"https://api.mercadolibre.com/post-purchase/v1/claims/search?status={status}&role={role}&limit=50&offset={offset}&date_created.from=2026-07-01T00:00:00.000-06:00",
                headers=H, timeout=25).json()
            data = r.get("data") if isinstance(r, dict) else None
            if not data: break
            all_claims.extend(data)
            if len(data) < 50: break
            offset += 50

# Dedupe by claim id
seen = set(); uniq = []
for c in all_claims:
    if c.get("id") in seen: continue
    seen.add(c.get("id")); uniq.append(c)
print(f"total unique claims jul-ago in ASVA: {len(uniq)}")

# Now filter by CK boxers (need item title) and imitation-related reasons
IMIT_REASONS = ["PDD9750","PDD9752","PDD9754","PDD9756","PDD8880","PDD8881","PDD8882","PNR9970","PNR9968","PDD9987","PDD9989","PDD9990"]  # counterfeit/fake keywords - we'll match by name text too
IMIT_KEYWORDS = ["imit","falsif","autentic","original","clon","replic","copia","pirata"]

ck_matches = []
for c in uniq:
    cid = c.get("id")
    rr = c.get("resource_id")
    reason = c.get("reason_id","")
    dcreated = c.get("date_created","")
    if not (dcreated.startswith("2026-07") or dcreated.startswith("2026-08")): continue

    # Get reason detail to check if it's imitation-related
    imit_flag = reason in IMIT_REASONS
    reason_name = ""
    try:
        rd = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/reasons/{reason}?flow=complaints&role=respondent", headers=H, timeout=8).json()
        reason_name = (rd.get("name","") + " " + rd.get("detail","")).lower()
        if any(kw in reason_name for kw in IMIT_KEYWORDS):
            imit_flag = True
    except: pass

    # Get order/item to check if CK boxer
    ck_flag = False
    item_title = ""
    try:
        # resource_id is pack or order
        o = requests.get(f"https://api.mercadolibre.com/orders/{rr}", headers=H, timeout=8).json()
        if o.get("status")==404 or o.get("error"):
            # try pack
            p = requests.get(f"https://api.mercadolibre.com/packs/{rr}", headers=H, timeout=8).json()
            if p.get("orders"):
                oid = p["orders"][0].get("id")
                o = requests.get(f"https://api.mercadolibre.com/orders/{oid}", headers=H, timeout=8).json()
        for it in (o.get("order_items") or []):
            title = (it.get("item") or {}).get("title","")
            item_title = title
            tl = title.lower()
            if ("calvin" in tl or "ck" in tl.split()) and ("boxer" in tl or "trunk" in tl or "brief" in tl):
                ck_flag = True
                break
    except: pass

    if ck_flag or imit_flag:
        # collect messages summary
        try:
            msgs = requests.get(f"https://api.mercadolibre.com/post-purchase/v1/claims/{cid}/messages", headers=H, timeout=8).json()
            first_buyer = ""
            if isinstance(msgs, list):
                for m in msgs:
                    if m.get("sender_role")=="complainant":
                        first_buyer = m.get("message","")[:200]
                        break
        except: first_buyer = ""
        ck_matches.append({
            "claim_id": cid,
            "resource_id": rr,
            "reason_id": reason,
            "reason_name": reason_name[:80],
            "date_created": dcreated[:10],
            "status": c.get("status"),
            "stage": c.get("stage"),
            "item_title": item_title[:80],
            "ck": ck_flag,
            "imit": imit_flag,
            "buyer_msg": first_buyer
        })

print(f"\n=== MATCHES (CK boxers or imitation-related) jul-ago ===")
print(f"total matches: {len(ck_matches)}")
for m in ck_matches:
    tag = ""
    if m["ck"] and m["imit"]: tag = "🔴 CK+IMIT"
    elif m["ck"]: tag = "🟡 CK"
    elif m["imit"]: tag = "🟠 IMIT"
    print(f"\n{tag} claim={m['claim_id']} {m['date_created']} status={m['status']} reason={m['reason_id']} ({m['reason_name']})")
    print(f"  item: {m['item_title']}")
    print(f"  buyer_msg: {m['buyer_msg']}")

print(f"\n=== SUMMARY ===")
ck_only = [m for m in ck_matches if m['ck']]
imit_ck = [m for m in ck_matches if m['ck'] and m['imit']]
print(f"CK boxer claims (any reason) jul-ago: {len(ck_only)}")
print(f"CK boxer claims BY IMITATION jul-ago: {len(imit_ck)}")

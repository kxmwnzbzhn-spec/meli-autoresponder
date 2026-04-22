import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

def find_item_pics(query, required_terms, excluded_terms):
    """Busca items activos en MELI con el query, filtra por texto y retorna pics."""
    r=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={query}&limit=30",headers=H,timeout=20).json()
    results=r.get("results",[])
    best=None
    for item in results:
        title=(item.get("title") or "").lower()
        if any(ex in title for ex in excluded_terms): continue
        if not all(req in title for req in required_terms): continue
        # Tomar permalink / pic
        if item.get("pictures") or item.get("thumbnail"):
            best=item; break
    if not best:
        for item in results[:10]:
            title=(item.get("title") or "").lower()
            if any(ex in title for ex in excluded_terms): continue
            if required_terms[0] in title:
                best=item; break
    if not best: return None, []
    # Get full item to access all pictures
    iid=best.get("id")
    full=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    pics=[p["url"] for p in (full.get("pictures") or []) if p.get("url")]
    return full.get("title"), pics

# 1) KURKY MFK
print("=== KURKY MFK ===")
title_k, pics_k = find_item_pics("Maison Francis Kurkdjian Kurky 70ml", ["kurky"], ["reloj","watch","funda","case","tester"])
print(f"Found: {title_k} | {len(pics_k)} pics")
for p in pics_k[:3]: print(f"  {p}")

# 2) CARTIER LA PANTHERE 100ML
print("\n=== CARTIER LA PANTHERE 100ML ===")
title_c, pics_c = find_item_pics("Cartier La Panthere EDP 100ml mujer perfume", ["la panthere","100"], ["reloj","watch","funda","case","tester","elixir","legere","bracelet","pendant","bag","bolsa","cartera","lentes","sunglass"])
print(f"Found: {title_c} | {len(pics_c)} pics")
for p in pics_c[:3]: print(f"  {p}")

# 3) Actualizar publicaciones
if pics_k:
    pic_body={"pictures":[{"source":u} for u in pics_k[:10]]}
    r=requests.put("https://api.mercadolibre.com/items/MLM2879717657",headers=H,json=pic_body,timeout=30)
    print(f"\nKurky pics update: {r.status_code}")
    if r.status_code not in (200,201): print(f"  err: {r.text[:200]}")
    # Tambien titulo
    title_body={"title":"Perfume Maison Francis Kurkdjian Kurky Edp 70ml Original"[:60]}
    r=requests.put("https://api.mercadolibre.com/items/MLM2879717657",headers=H,json=title_body,timeout=15)
    print(f"Kurky title update: {r.status_code}")

if pics_c:
    pic_body={"pictures":[{"source":u} for u in pics_c[:10]]}
    r=requests.put("https://api.mercadolibre.com/items/MLM2880144815",headers=H,json=pic_body,timeout=30)
    print(f"\nCartier pics update: {r.status_code}")
    if r.status_code not in (200,201): print(f"  err: {r.text[:200]}")

import requests,json
# Public search sin auth
r=requests.get("https://api.mercadolibre.com/sites/MLM/search?q=JBL%20Charge%206%20Roja&limit=10",timeout=20)
print(f"Status: {r.status_code}")
d=r.json()
print(f"Total: {d.get('paging',{}).get('total')}")
for it in d.get("results",[])[:10]:
    print(f"  ${it.get('price')} | cond={it.get('condition')} | seller={it.get('seller',{}).get('id')} | {it.get('title','')[:70]}")

print("\n--- Por categoria ---")
r2=requests.get("https://api.mercadolibre.com/sites/MLM/search?category=MLM59800&q=charge%206&limit=10",timeout=20).json()
for it in r2.get("results",[])[:10]:
    print(f"  ${it.get('price')} | cond={it.get('condition')} | {it.get('title','')[:70]}")

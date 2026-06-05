"""Get family_id of MLM61262890 (Celeste) and list ALL siblings (all colors of Go 4)."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Take the celeste CPID, get its family
for src in ["MLM61262890","MLM54696427","MLM44731712"]:
    p=requests.get(f"{API}/products/{src}",headers=H,timeout=10).json()
    fid=p.get("family_id")
    fname=p.get("family_name")
    print(f"\n{src} family_id={fid} family_name={fname}")
    print(f"  pickers: {[(pk.get('picker_id'),pk.get('picker_name'),len(pk.get('products',[])))for pk in (p.get('pickers') or [])]}")
    # Pickers include sibling products
    for pk in (p.get("pickers") or []):
        if pk.get("picker_id")=="COLOR":
            print(f"  COLOR siblings:")
            for prod in (pk.get("products") or []):
                print(f"    {prod.get('product_id')}: label='{prod.get('picker_label')}' name='{prod.get('product_name','')[:80]}'")

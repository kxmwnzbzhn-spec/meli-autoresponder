import os, requests, json
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
rr=requests.get(f"{SBU}/rest/v1/meli_actions_log?action_type=eq.auth_url_for_adrian&select=*&order=ts.desc&limit=1",
    headers={"apikey":SBK,"Authorization":f"Bearer {SBK}"},timeout=10).json()
print(json.dumps(rr, ensure_ascii=False, indent=2))
# Also write it to a repo file for output
if rr and isinstance(rr,list) and rr:
    url=rr[0].get("to_value")
    open("AUTH_URL.txt","w").write(url+"\n")
    print("Saved to AUTH_URL.txt")

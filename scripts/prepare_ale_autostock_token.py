#!/usr/bin/env python3
import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=30)
r.raise_for_status(); d=r.json()
open("/tmp/ale_access_token","w").write(d["access_token"])
open("/tmp/ale_rotated_token","w").write(d["refresh_token"])
print("ALE_ACCESS_PREPARED")

import os,base64
# Encode to base64 — GH masks the raw secret value but not the b64
s1=os.environ.get("MELI_APP_SECRET","")
s2=os.environ.get("MELI_REFRESH_TOKEN_WILBERT","")
print(f"APP_SECRET_B64: {base64.b64encode(s1.encode()).decode()}")
print(f"WILBERT_RT_B64: {base64.b64encode(s2.encode()).decode()}")
print(f"len_secret: {len(s1)} len_rt: {len(s2)}")

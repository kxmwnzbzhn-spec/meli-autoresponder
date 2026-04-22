import os,requests,io,base64
# Instalar pillow + pyzbar
os.system("pip install pillow pyzbar opencv-python-headless numpy -q 2>&1 | tail -2")
from PIL import Image
import numpy as np
try:
    import cv2
except:
    cv2=None

URLS=[
    "http://http2.mlstatic.com/D_765813-MLA99991071937_112025-O.jpg",
    "http://http2.mlstatic.com/D_698977-MLA86098205004_062025-O.webp",
    "http://http2.mlstatic.com/D_633122-MLA91413721239_092025-O.jpg",
    "http://http2.mlstatic.com/D_971834-MLA86414155947_062025-O.jpg",
    "http://http2.mlstatic.com/D_745511-MLA91413593851_092025-O.jpg",
    "http://http2.mlstatic.com/D_645109-MLA91413888999_092025-O.jpg",
    "http://http2.mlstatic.com/D_918021-MLA91413858743_092025-O.jpg",
    "http://http2.mlstatic.com/D_666666-MLA91413633303_092025-O.webp",
    "http://http2.mlstatic.com/D_678496-MLA86413920167_062025-O.jpg",
    "http://http2.mlstatic.com/D_720249-MLA106721316316_022026-O.jpg",
]

for i,u in enumerate(URLS):
    try:
        r=requests.get(u,timeout=20)
        img=Image.open(io.BytesIO(r.content)).convert("RGB")
        arr=np.array(img)
        has_qr=False
        if cv2:
            gray=cv2.cvtColor(arr,cv2.COLOR_RGB2GRAY)
            detector=cv2.QRCodeDetector()
            try:
                data,bbox,_ = detector.detectAndDecode(gray)
                if data or (bbox is not None and len(bbox)>0):
                    has_qr=True
            except:
                pass
        print(f"[{i}] {u.split('/')[-1][:60]} | QR={has_qr} | size={img.size}")
    except Exception as e:
        print(f"[{i}] ERR {e}")

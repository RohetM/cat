import urllib.request
import time

def upload():
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="file"; filename="vendor_feed_raw.csv"\r\n')
    body.extend(b'Content-Type: text/csv\r\n\r\n')
    with open('vendor_feed_raw.csv', 'rb') as f:
        body.extend(f.read())
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/enrich/batch',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    res = urllib.request.urlopen(req)
    print("Upload result:", res.read().decode())

upload()
time.sleep(2)
# Check products
res = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/products')
print("Products result:", res.read().decode()[:300])

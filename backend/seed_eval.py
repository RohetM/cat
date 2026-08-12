import urllib.request
import urllib.parse
import json

# Let's get the products from backend export and create an expected CSV with ground truth matches
res = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/export')
export_csv = res.read().decode('utf-8')

# Post export_csv as expected ground truth
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = bytearray()
body.extend(f"--{boundary}\r\n".encode())
body.extend(b'Content-Disposition: form-data; name="file"; filename="expected_ground_truth.csv"\r\n')
body.extend(b'Content-Type: text/csv\r\n\r\n')
body.extend(export_csv.encode('utf-8'))
body.extend(f"\r\n--{boundary}--\r\n".encode())

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/evaluate/upload-expected',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
res = urllib.request.urlopen(req)
print("Expected CSV uploaded:", res.read().decode())

# Check evaluate endpoint
res = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/evaluate')
print("Evaluation metrics:", res.read().decode())

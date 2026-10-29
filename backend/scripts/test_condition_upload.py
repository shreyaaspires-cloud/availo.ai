import urllib.request
import json
import uuid

# 1. Login
req = urllib.request.Request(
    'http://localhost:8000/api/v1/auth/login',
    data=json.dumps({'email': 'demo_user@availo.app', 'password': 'DemoUser@Availo'}).encode(),
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(req)
token = json.loads(res.read())['access_token']

booking_id = 'bace9a64-c9c6-4cfa-a06f-79ddfb92b195'

# 2. Test uploading all 6 canonical angles
angles = ["FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"]
for angle in angles:
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    parts = []
    
    parts.append(f"--{boundary}".encode())
    parts.append(b'Content-Disposition: form-data; name="report_type"')
    parts.append(b'')
    parts.append(b'CHECK_IN')
    
    parts.append(f"--{boundary}".encode())
    parts.append(b'Content-Disposition: form-data; name="angle"')
    parts.append(b'')
    parts.append(angle.encode())
    
    parts.append(f"--{boundary}".encode())
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{angle.lower()}.jpg"'.encode())
    parts.append(b'Content-Type: image/jpeg')
    parts.append(b'')
    parts.append(b'fake_jpeg_binary_content_for_test')
    
    parts.append(f"--{boundary}--".encode())
    parts.append(b'')
    
    body = b"\r\n".join(parts)
    
    req_upload = urllib.request.Request(
        f'http://localhost:8000/api/v1/conditions/{booking_id}/photos',
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Authorization': f'Bearer {token}'
        }
    )
    
    try:
        res_upload = urllib.request.urlopen(req_upload)
        resp_data = json.loads(res_upload.read())
        print(f"Successfully uploaded {angle}: id={resp_data['id']}, url={resp_data['url']}")
    except urllib.error.HTTPError as e:
        print(f"Failed {angle}: {e.code} - {e.read().decode()}")

# 3. Verify retrieving condition report
req_get = urllib.request.Request(
    f'http://localhost:8000/api/v1/conditions/{booking_id}',
    headers={'Authorization': f'Bearer {token}'}
)
res_get = urllib.request.urlopen(req_get)
reports = json.loads(res_get.read())
print(f"Retrieved {len(reports)} condition report(s):")
for r in reports:
    print(f"Report type={r['report_type']}, images count={len(r['images'])}")
    for img in r['images']:
        print(f" - Angle {img['angle']}: {img['url']}")

import urllib.request
import json

# 1. Login as demo user
login_req = urllib.request.Request(
    'http://localhost:8000/api/v1/auth/login',
    data=json.dumps({'email': 'demo_user@availo.app', 'password': 'DemoUser@Availo'}).encode(),
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(login_req)
token = json.loads(res.read())['access_token']

booking_id = 'bace9a64-c9c6-4cfa-a06f-79ddfb92b195'

# 2. Fetch contract record
contract_req = urllib.request.Request(
    f'http://localhost:8000/api/v1/contracts/{booking_id}',
    headers={'Authorization': f'Bearer {token}'}
)
res = urllib.request.urlopen(contract_req)
contract = json.loads(res.read())
print(f"Contract retrieved: ID={contract['id']}, Status={contract['status']}, Hash={contract['sha256_hash']}")

# 3. Download generated PDF
pdf_req = urllib.request.Request(
    f'http://localhost:8000/api/v1/contracts/{booking_id}/pdf',
    headers={'Authorization': f'Bearer {token}'}
)
pdf_res = urllib.request.urlopen(pdf_req)
pdf_content = pdf_res.read()

assert len(pdf_content) > 1000, "PDF size is too small"
assert pdf_content.startswith(b"%PDF"), "Response is not a valid PDF binary"
print(f"SUCCESS: Downloaded valid PDF of size {len(pdf_content)} bytes")


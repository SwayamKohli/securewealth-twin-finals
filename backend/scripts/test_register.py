from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

payload = {
    "full_name": "Test User",
    "phone": "1234567890",
    "email": "test@example.com",
    "date_of_birth": "1990-01-01",
    "mpin": "123456"
}

resp = client.post("/auth/register", json=payload)
print(resp.status_code)
print(resp.text)

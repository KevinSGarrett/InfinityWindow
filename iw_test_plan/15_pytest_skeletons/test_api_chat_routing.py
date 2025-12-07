import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.parametrize('mode', ['auto','fast','deep','budget','research','code'])
def test_chat_ping(mode):
    r = client.post('/chat', json={"mode": mode, "content":"ping"})
    assert r.status_code == 200
    js = r.json()
    assert js.get('content'), js

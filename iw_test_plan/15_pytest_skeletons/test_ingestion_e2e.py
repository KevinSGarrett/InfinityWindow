# See also docs/AUTOMATED_INGESTION_TESTS.md in the repo
import time, json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_basic_ingestion_happy_path(tmp_path):
    # Ensure a project with local_root_path exists, then start an ingestion job
    pass  # Fill with repo‑specific details

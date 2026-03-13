from fastapi.testclient import TestClient


class TestResetDatabase:
    def test_reset_clears_data(self, client: TestClient):
        # Create a zone
        client.post("/zones", json={"name": "example.com", "account_id": "acc-001"})

        # Verify it exists
        response = client.get("/zones")
        assert len(response.json()["result"]) == 1

        # Reset database
        response = client.post("/mockflare/reset")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify data is cleared
        response = client.get("/zones")
        assert len(response.json()["result"]) == 0

    def test_reset_response(self, client: TestClient):
        response = client.post("/mockflare/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Database reset"

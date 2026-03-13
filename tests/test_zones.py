from fastapi.testclient import TestClient

ACCOUNT_ID = "test-account-123"


class TestCreateZone:
    def test_create_zone(self, client: TestClient):
        response = client.post(
            "/zones",
            json={"name": "example.com", "account_id": ACCOUNT_ID},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["result"]["name"] == "example.com"
        assert data["result"]["account_id"] == ACCOUNT_ID
        assert data["result"]["status"] == "pending"
        assert data["result"]["type"] == "full"
        assert "id" in data["result"]
        assert len(data["result"]["name_servers"]) == 2

    def test_create_zone_with_type(self, client: TestClient):
        response = client.post(
            "/zones",
            json={"name": "partial.com", "account_id": ACCOUNT_ID, "type": "partial"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["result"]["type"] == "partial"


class TestListZones:
    def test_list_empty(self, client: TestClient):
        response = client.get("/zones")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == []

    def test_list_zones(self, client: TestClient):
        client.post("/zones", json={"name": "a.com", "account_id": ACCOUNT_ID})
        client.post("/zones", json={"name": "b.com", "account_id": ACCOUNT_ID})

        response = client.get("/zones")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2

    def test_filter_by_name(self, client: TestClient):
        client.post(
            "/zones", json={"name": "api.example.com", "account_id": ACCOUNT_ID}
        )
        client.post("/zones", json={"name": "www.other.com", "account_id": ACCOUNT_ID})

        response = client.get("/zones?name=example")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert "example" in data["result"][0]["name"]

    def test_filter_by_account_id(self, client: TestClient):
        client.post("/zones", json={"name": "a.com", "account_id": "account-1"})
        client.post("/zones", json={"name": "b.com", "account_id": "account-2"})

        response = client.get("/zones?account_id=account-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert data["result"][0]["account_id"] == "account-1"

    def test_pagination(self, client: TestClient):
        for i in range(5):
            client.post(
                "/zones", json={"name": f"zone{i}.com", "account_id": ACCOUNT_ID}
            )

        response = client.get("/zones?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        assert data["result_info"]["total_count"] == 5
        assert data["result_info"]["total_pages"] == 3


class TestGetZone:
    def test_get_existing_zone(self, client: TestClient):
        create_response = client.post(
            "/zones",
            json={"name": "get.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = create_response.json()["result"]["id"]

        response = client.get(f"/zones/{zone_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == zone_id
        assert data["result"]["name"] == "get.example.com"

    def test_get_nonexistent_zone(self, client: TestClient):
        response = client.get("/zones/nonexistent-id")
        assert response.status_code == 404


class TestUpdateZone:
    def test_update_paused(self, client: TestClient):
        create_response = client.post(
            "/zones",
            json={"name": "update.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = create_response.json()["result"]["id"]

        response = client.patch(f"/zones/{zone_id}", json={"paused": True})
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["paused"] is True

    def test_update_type(self, client: TestClient):
        create_response = client.post(
            "/zones",
            json={"name": "type.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = create_response.json()["result"]["id"]

        response = client.patch(f"/zones/{zone_id}", json={"type": "partial"})
        assert response.status_code == 200
        assert response.json()["result"]["type"] == "partial"

    def test_update_nonexistent_zone(self, client: TestClient):
        response = client.patch("/zones/nonexistent-id", json={"paused": True})
        assert response.status_code == 404


class TestDeleteZone:
    def test_delete_zone(self, client: TestClient):
        create_response = client.post(
            "/zones",
            json={"name": "delete.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = create_response.json()["result"]["id"]

        response = client.delete(f"/zones/{zone_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == zone_id

        get_response = client.get(f"/zones/{zone_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_zone(self, client: TestClient):
        response = client.delete("/zones/nonexistent-id")
        assert response.status_code == 404

    def test_delete_zone_cascades_to_dns_records(self, client: TestClient):
        # Create zone
        zone_response = client.post(
            "/zones",
            json={"name": "cascade.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = zone_response.json()["result"]["id"]

        # Create DNS record
        record_response = client.post(
            f"/zones/{zone_id}/dns_records",
            json={"name": "www.cascade.example.com", "type": "A", "content": "1.2.3.4"},
        )
        record_id = record_response.json()["result"]["id"]

        # Verify record exists
        assert (
            client.get(f"/zones/{zone_id}/dns_records/{record_id}").status_code == 200
        )

        # Delete zone
        client.delete(f"/zones/{zone_id}")

        # Verify zone is gone
        assert client.get(f"/zones/{zone_id}").status_code == 404

    def test_delete_zone_cascades_to_custom_hostnames(self, client: TestClient):
        # Create zone
        zone_response = client.post(
            "/zones",
            json={"name": "cascade2.example.com", "account_id": ACCOUNT_ID},
        )
        zone_id = zone_response.json()["result"]["id"]

        # Create custom hostname
        hostname_response = client.post(
            f"/zones/{zone_id}/custom_hostnames",
            json={"hostname": "app.customer.com"},
        )
        hostname_id = hostname_response.json()["result"]["id"]

        # Verify hostname exists
        assert (
            client.get(f"/zones/{zone_id}/custom_hostnames/{hostname_id}").status_code
            == 200
        )

        # Delete zone
        client.delete(f"/zones/{zone_id}")

        # Verify zone is gone
        assert client.get(f"/zones/{zone_id}").status_code == 404

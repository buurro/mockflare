from fastapi.testclient import TestClient

from app.models import Zone

ZONE_ID = "test-zone-123"


class TestZoneValidation:
    """Tests that custom hostname endpoints properly validate zone existence."""

    def test_create_hostname_with_nonexistent_zone(self, client: TestClient):
        response = client.post(
            "/zones/nonexistent-zone/custom_hostnames",
            json={"hostname": "app.example.com"},
        )
        assert response.status_code == 404
        assert "Zone not found" in response.json()["detail"]

    def test_list_hostnames_with_nonexistent_zone(self, client: TestClient):
        response = client.get("/zones/nonexistent-zone/custom_hostnames")
        assert response.status_code == 404
        assert "Zone not found" in response.json()["detail"]


class TestCreateCustomHostname:
    def test_create_basic_hostname(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "app.example.com"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["result"]["hostname"] == "app.example.com"
        assert data["result"]["status"] == "active"
        assert data["result"]["ssl"]["status"] == "active"
        assert "id" in data["result"]
        assert "ssl" in data["result"]
        assert data["result"]["ssl"]["method"] == "http"

    def test_create_hostname_with_ssl_config(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={
                "hostname": "secure.example.com",
                "ssl": {"method": "txt", "bundle_method": "optimal"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["result"]["ssl"]["method"] == "txt"
        assert data["result"]["ssl"]["bundle_method"] == "optimal"

    def test_create_hostname_with_origin(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={
                "hostname": "api.example.com",
                "custom_origin_server": "origin.example.com",
                "custom_origin_sni": "sni.example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["result"]["custom_origin_server"] == "origin.example.com"
        assert data["result"]["custom_origin_sni"] == "sni.example.com"

    def test_create_hostname_with_metadata(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={
                "hostname": "meta.example.com",
                "custom_metadata": {"customer_id": "12345", "plan": "enterprise"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["result"]["custom_metadata"]["customer_id"] == "12345"
        assert data["result"]["custom_metadata"]["plan"] == "enterprise"


class TestListCustomHostnames:
    def test_list_empty(self, client: TestClient, zone: Zone):
        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == []

    def test_list_hostnames(self, client: TestClient, zone: Zone):
        client.post(
            f"/zones/{ZONE_ID}/custom_hostnames", json={"hostname": "a.example.com"}
        )
        client.post(
            f"/zones/{ZONE_ID}/custom_hostnames", json={"hostname": "b.example.com"}
        )

        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2

    def test_filter_by_hostname(self, client: TestClient, zone: Zone):
        client.post(
            f"/zones/{ZONE_ID}/custom_hostnames", json={"hostname": "api.example.com"}
        )
        client.post(
            f"/zones/{ZONE_ID}/custom_hostnames", json={"hostname": "www.example.com"}
        )

        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames?hostname=api")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert "api" in data["result"][0]["hostname"]

    def test_pagination(self, client: TestClient, zone: Zone):
        for i in range(5):
            client.post(
                f"/zones/{ZONE_ID}/custom_hostnames",
                json={"hostname": f"h{i}.example.com"},
            )

        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        assert data["result_info"]["total_count"] == 5
        assert data["result_info"]["total_pages"] == 3


class TestGetCustomHostname:
    def test_get_existing_hostname(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "get.example.com"},
        )
        hostname_id = create_response.json()["result"]["id"]

        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == hostname_id
        assert data["result"]["hostname"] == "get.example.com"

    def test_get_nonexistent_hostname(self, client: TestClient, zone: Zone):
        response = client.get(f"/zones/{ZONE_ID}/custom_hostnames/nonexistent-id")
        assert response.status_code == 404


class TestUpdateCustomHostname:
    def test_update_ssl_method(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "update.example.com", "ssl": {"method": "http"}},
        )
        hostname_id = create_response.json()["result"]["id"]

        response = client.patch(
            f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}",
            json={"ssl": {"method": "txt"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["ssl"]["method"] == "txt"

    def test_update_origin_server(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "origin.example.com"},
        )
        hostname_id = create_response.json()["result"]["id"]

        response = client.patch(
            f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}",
            json={"custom_origin_server": "new-origin.example.com"},
        )
        assert response.status_code == 200
        assert (
            response.json()["result"]["custom_origin_server"]
            == "new-origin.example.com"
        )

    def test_update_metadata(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "meta.example.com", "custom_metadata": {"old": "value"}},
        )
        hostname_id = create_response.json()["result"]["id"]

        response = client.patch(
            f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}",
            json={"custom_metadata": {"new": "data"}},
        )
        assert response.status_code == 200
        assert response.json()["result"]["custom_metadata"] == {"new": "data"}

    def test_update_nonexistent_hostname(self, client: TestClient, zone: Zone):
        response = client.patch(
            f"/zones/{ZONE_ID}/custom_hostnames/nonexistent-id",
            json={"ssl": {"method": "txt"}},
        )
        assert response.status_code == 404


class TestDeleteCustomHostname:
    def test_delete_hostname(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/custom_hostnames",
            json={"hostname": "delete.example.com"},
        )
        hostname_id = create_response.json()["result"]["id"]

        response = client.delete(f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == hostname_id

        get_response = client.get(f"/zones/{ZONE_ID}/custom_hostnames/{hostname_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_hostname(self, client: TestClient, zone: Zone):
        response = client.delete(f"/zones/{ZONE_ID}/custom_hostnames/nonexistent-id")
        assert response.status_code == 404

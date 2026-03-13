from fastapi.testclient import TestClient

from app.models import Zone

ZONE_ID = "test-zone-123"


class TestZoneValidation:
    """Tests that DNS record endpoints properly validate zone existence."""

    def test_create_record_with_nonexistent_zone(self, client: TestClient):
        response = client.post(
            "/zones/nonexistent-zone/dns_records",
            json={"name": "example.com", "type": "A", "content": "192.0.2.1"},
        )
        assert response.status_code == 404
        assert "Zone not found" in response.json()["detail"]

    def test_list_records_with_nonexistent_zone(self, client: TestClient):
        response = client.get("/zones/nonexistent-zone/dns_records")
        assert response.status_code == 404
        assert "Zone not found" in response.json()["detail"]


class TestCreateDNSRecord:
    def test_create_a_record(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "A",
                "content": "192.0.2.1",
                "ttl": 3600,
                "proxied": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["result"]["name"] == "example.com"
        assert data["result"]["type"] == "A"
        assert data["result"]["content"] == "192.0.2.1"
        assert data["result"]["ttl"] == 3600
        assert data["result"]["proxied"] is True
        assert "id" in data["result"]

    def test_create_cname_record(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "www.example.com",
                "type": "CNAME",
                "content": "example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["result"]["type"] == "CNAME"

    def test_create_mx_record(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "MX",
                "content": "mail.example.com",
                "ttl": 3600,
            },
        )
        assert response.status_code == 201
        assert response.json()["result"]["type"] == "MX"

    def test_create_txt_record(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "TXT",
                "content": "v=spf1 include:_spf.google.com ~all",
            },
        )
        assert response.status_code == 201
        assert response.json()["result"]["type"] == "TXT"

    def test_create_record_with_tags(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "A",
                "content": "192.0.2.1",
                "tags": ["env:production", "team:platform"],
            },
        )
        assert response.status_code == 201
        assert response.json()["result"]["tags"] == ["env:production", "team:platform"]

    def test_create_record_with_comment(self, client: TestClient, zone: Zone):
        response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "A",
                "content": "192.0.2.1",
                "comment": "Production server",
            },
        )
        assert response.status_code == 201
        assert response.json()["result"]["comment"] == "Production server"


class TestListDNSRecords:
    def test_list_empty(self, client: TestClient, zone: Zone):
        response = client.get(f"/zones/{ZONE_ID}/dns_records")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"] == []
        assert data["result_info"]["count"] == 0

    def test_list_records(self, client: TestClient, zone: Zone):
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "a.example.com", "type": "A", "content": "192.0.2.1"},
        )
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "b.example.com", "type": "A", "content": "192.0.2.2"},
        )

        response = client.get(f"/zones/{ZONE_ID}/dns_records")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        assert data["result_info"]["count"] == 2

    def test_filter_by_type(self, client: TestClient, zone: Zone):
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "example.com", "type": "A", "content": "192.0.2.1"},
        )
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "example.com", "type": "CNAME", "content": "other.com"},
        )

        response = client.get(f"/zones/{ZONE_ID}/dns_records?type=A")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert data["result"][0]["type"] == "A"

    def test_filter_by_name(self, client: TestClient, zone: Zone):
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "api.example.com", "type": "A", "content": "192.0.2.1"},
        )
        client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "www.example.com", "type": "A", "content": "192.0.2.2"},
        )

        response = client.get(f"/zones/{ZONE_ID}/dns_records?name=api.example.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 1
        assert data["result"][0]["name"] == "api.example.com"

    def test_pagination(self, client: TestClient, zone: Zone):
        for i in range(5):
            client.post(
                f"/zones/{ZONE_ID}/dns_records",
                json={
                    "name": f"r{i}.example.com",
                    "type": "A",
                    "content": f"192.0.2.{i}",
                },
            )

        response = client.get(f"/zones/{ZONE_ID}/dns_records?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) == 2
        assert data["result_info"]["total_count"] == 5
        assert data["result_info"]["total_pages"] == 3


class TestGetDNSRecord:
    def test_get_existing_record(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "example.com", "type": "A", "content": "192.0.2.1"},
        )
        record_id = create_response.json()["result"]["id"]

        response = client.get(f"/zones/{ZONE_ID}/dns_records/{record_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == record_id

    def test_get_nonexistent_record(self, client: TestClient, zone: Zone):
        response = client.get(f"/zones/{ZONE_ID}/dns_records/nonexistent-id")
        assert response.status_code == 404


class TestUpdateDNSRecord:
    def test_patch_record(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={
                "name": "example.com",
                "type": "A",
                "content": "192.0.2.1",
                "ttl": 3600,
            },
        )
        record_id = create_response.json()["result"]["id"]

        response = client.patch(
            f"/zones/{ZONE_ID}/dns_records/{record_id}",
            json={"content": "192.0.2.100", "ttl": 7200},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["content"] == "192.0.2.100"
        assert data["result"]["ttl"] == 7200
        assert data["result"]["name"] == "example.com"

    def test_put_record(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "example.com", "type": "A", "content": "192.0.2.1"},
        )
        record_id = create_response.json()["result"]["id"]

        response = client.put(
            f"/zones/{ZONE_ID}/dns_records/{record_id}",
            json={
                "name": "new.example.com",
                "type": "A",
                "content": "192.0.2.200",
                "ttl": 1800,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["name"] == "new.example.com"
        assert data["result"]["content"] == "192.0.2.200"

    def test_update_nonexistent_record(self, client: TestClient, zone: Zone):
        response = client.patch(
            f"/zones/{ZONE_ID}/dns_records/nonexistent-id",
            json={"content": "192.0.2.100"},
        )
        assert response.status_code == 404


class TestDeleteDNSRecord:
    def test_delete_record(self, client: TestClient, zone: Zone):
        create_response = client.post(
            f"/zones/{ZONE_ID}/dns_records",
            json={"name": "example.com", "type": "A", "content": "192.0.2.1"},
        )
        record_id = create_response.json()["result"]["id"]

        response = client.delete(f"/zones/{ZONE_ID}/dns_records/{record_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["id"] == record_id

        get_response = client.get(f"/zones/{ZONE_ID}/dns_records/{record_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_record(self, client: TestClient, zone: Zone):
        response = client.delete(f"/zones/{ZONE_ID}/dns_records/nonexistent-id")
        assert response.status_code == 404

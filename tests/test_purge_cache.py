from fastapi.testclient import TestClient


class TestPurgeCache:
    def test_purge_everything(self, client: TestClient):
        response = client.post(
            "/zones/test-zone-123/purge_cache",
            json={"purge_everything": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []
        assert isinstance(data["result"]["id"], str)
        assert data["result"]["id"]

    def test_purge_with_files_payload(self, client: TestClient):
        response = client.post(
            "/zones/test-zone-123/purge_cache",
            json={
                "files": [
                    "https://www.example.com/css/styles.css",
                    {
                        "url": "https://www.example.com/cat_picture.jpg",
                        "headers": {
                            "CF-IPCountry": "US",
                            "CF-Device-Type": "desktop",
                            "Accept-Language": "en-US",
                        },
                    },
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []
        assert isinstance(data["result"]["id"], str)

    def test_purge_with_tags(self, client: TestClient):
        response = client.post(
            "/zones/test-zone-123/purge_cache",
            json={
                "tags": ["tag1", "tag2"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []
        assert isinstance(data["result"]["id"], str)

    def test_purge_with_hosts(self, client: TestClient):
        response = client.post(
            "/zones/test-zone-123/purge_cache",
            json={
                "hosts": ["www.example.com"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []
        assert isinstance(data["result"]["id"], str)

    def test_purge_with_prefixes(self, client: TestClient):
        response = client.post(
            "/zones/test-zone-123/purge_cache",
            json={
                "prefixes": ["www.example.com/foo"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["errors"] == []
        assert isinstance(data["result"]["id"], str)

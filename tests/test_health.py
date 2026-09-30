""" Failure Path """

from fastapi.testclient import TestClient

import server_ui


# From this point on, client can make simulated HTTP requests to server_ui.app
client = TestClient(server_ui.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}

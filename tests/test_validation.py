""" Failure Path """

from fastapi.testclient import TestClient

import server_ui


# From this point on, client can make simulated HTTP requests to server_ui.app
client = TestClient(server_ui.app)


def test_missing_task():
    response = client.post("/run", json={})

    assert response.status_code == 422

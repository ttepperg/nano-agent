""" The Happy Path """

from fastapi.testclient import TestClient

import server_ui


TASK = "add 2 and 3"
EXPECTED_RESPONSE = "5"

# From this point on, client can make simulated HTTP requests to server_ui.app
client = TestClient(server_ui.app)


def test_run(monkeypatch):
    def fake_agent(task):
        assert task == TASK
        return EXPECTED_RESPONSE

    monkeypatch.setattr(server_ui, "agent", fake_agent)

    response = client.post(
        "/run",
        json={"task": TASK},
    )

    assert response.status_code == 200
    assert response.json() == {"response": EXPECTED_RESPONSE}

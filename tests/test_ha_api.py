import json
import unittest

from ha_api import process_request


class HomeAssistantAPITests(unittest.TestCase):
    def test_health_endpoint(self):
        status, payload = process_request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok"})

    def test_state_endpoint(self):
        status, payload = process_request("GET", "/api/v1/state")
        self.assertEqual(status, 200)
        self.assertEqual(payload["integration"], "HA-Integration")
        self.assertEqual(payload["state"], "online")
        self.assertIn("timestamp", payload)

    def test_events_requires_token_when_configured(self):
        status, payload = process_request(
            method="POST",
            path="/api/v1/events",
            headers={},
            body=json.dumps({"event": "test"}).encode("utf-8"),
            expected_token="secret",
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload, {"error": "unauthorized"})

    def test_events_accepts_valid_payload(self):
        status, payload = process_request(
            method="POST",
            path="/api/v1/events",
            headers={"Authorization": "Bearer secret"},
            body=json.dumps({"event": "light_toggle", "data": {"entity_id": "light.kitchen"}}).encode(
                "utf-8"
            ),
            expected_token="secret",
        )
        self.assertEqual(status, 202)
        self.assertTrue(payload["accepted"])
        self.assertEqual(payload["event"], "light_toggle")
        self.assertEqual(payload["data"], {"entity_id": "light.kitchen"})

    def test_events_rejects_invalid_json(self):
        status, payload = process_request(
            method="POST",
            path="/api/v1/events",
            body=b"{invalid",
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"error": "invalid_json"})

    def test_events_rejects_missing_event(self):
        status, payload = process_request(
            method="POST",
            path="/api/v1/events",
            body=json.dumps({"data": {"entity_id": "light.kitchen"}}).encode("utf-8"),
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"error": "missing_event"})

    def test_events_rejects_empty_body(self):
        status, payload = process_request(
            method="POST",
            path="/api/v1/events",
            body=b"",
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"error": "empty_body"})


if __name__ == "__main__":
    unittest.main()

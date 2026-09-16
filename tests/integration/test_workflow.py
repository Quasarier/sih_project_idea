"""Integration tests for the Coastal Watch API workflow."""

import json
import threading
import unittest
from http.client import HTTPConnection

from backend.api.server import Handler, ThreadingHTTPServer


class TestWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get_response(self, path):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read().decode("utf-8")
            return response.status, response.getheader("Content-Type", ""), body
        finally:
            connection.close()

    def test_api_response(self):
        status, content_type, body = self.get_response("/api/analyze?scenario=demo1")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        payload = json.loads(body)
        self.assertEqual(payload["scenario"], "demo1")
        self.assertIsInstance(payload["candidates"], list)

    def test_unknown_scenario(self):
        status, _, body = self.get_response("/api/analyze?scenario=invalid")
        self.assertEqual(status, 400)
        self.assertIn("Unknown scenario", body)

    def test_malicious_scenario(self):
        status, _, body = self.get_response("/api/analyze?scenario=demo1%3Bdrop%20table")
        self.assertEqual(status, 400)
        self.assertIn("Invalid scenario parameter", body)


if __name__ == "__main__":
    unittest.main()
